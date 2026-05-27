# Auto Curation 安全审计报告

**审计日期**: 2026-05-27
**审计范围**: `src/scraper.py`, `src/llm_parser.py`, `src/cache.py`, `src/database.py`, `src/web/app.py`, `src/sites/base.py`, `run_collector.py`, 及全部 parser 模块
**审计方法**: 静态代码分析 + 依赖清单审查 + 攻击面建模

---

## 1. 注入漏洞 (Injection Vulnerabilities)

### 1.1 SQL 注入

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/web/app.py:285`, `src/web/app.py:290` |
| **描述** | `/api/exhibitions` 查询接口使用字符串拼接构建 `WHERE` 子句 (`where_str`)，但所有动态参数均通过 SQLite 参数化占位符 `?` 传入。`where_str` 本身由代码内部硬编码的条件片段拼接而成，**不直接暴露用户输入**。然而，`query` 参数被用于 `LIKE ?` 子查询中，属于安全的参数化查询。 |
| **攻击场景** | 当前实现下，攻击者无法通过 `source`/`query`/`start_year`/`end_year` 参数注入恶意 SQL，因为所有用户输入均绑定为参数。风险点在于未来维护者可能在 `where_clauses` 中误将用户输入直接拼接进字符串。 |
| **修复建议** | 保持当前参数化查询模式；禁止在 `where_clauses` 中直接拼接任何用户输入。建议对 `query` 参数增加长度限制（如 <= 100 字符）以防止 ReDoS 和滥用。 |

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/web/app.py:190-204` (`/api/network`) |
| **描述** | `placeholders` 通过 `",".join(["?"] * len(artists_names))` 构建，随后拼接进 SQL 字符串。虽然 `artists_names` 来自数据库聚合查询（非直接用户输入），且占位符为硬编码 `?`，但**该模式属于动态 SQL 拼接**。 |
| **攻击场景** | 若未来代码变更使 `artists_names` 来源不可信，或 `limit_artists` 参数被恶意放大导致查询膨胀，可能引发性能问题。当前无直接注入风险。 |
| **修复建议** | 在 `limit_artists` 上增加上限校验（如 <= 500）；确保 `artists_names` 永远只来自可信的数据库聚合结果。 |

### 1.2 命令注入

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/sites/mca_australia.py:63` |
| **描述** | `page.evaluate()` 执行硬编码的 JavaScript 字符串 `() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)`。该字符串为常量，不含用户输入。 |
| **攻击场景** | 当前无风险。若未来将用户可控的 URL 或选择器传入 `evaluate()`，则会产生远程代码执行（RCE）风险。 |
| **修复建议** | 保持 `evaluate()` 仅执行硬编码脚本；如需动态参数，使用 Playwright 的 `page.evaluate(fn, arg)` 将参数作为结构化数据传递，而非字符串拼接。 |

### 1.3 代码注入 / 反序列化

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `src/llm_parser.py:152-169` (`_parse_response`) |
| **描述** | LLM 返回的 JSON 字符串通过 `json.loads(content)` 直接解析，随后用 `ExhibitionModel(**parsed_json)` 进行 Pydantic 校验。虽然 Pydantic 提供了类型校验，但 `json.loads` 本身不限制对象类型。若 LLM 被提示词注入（prompt injection）诱导返回非预期结构，可能导致应用层逻辑异常。 |
| **攻击场景** | 攻击者若控制某个展览页面的内容（如提交恶意展览描述到被爬取的机构网站），可能通过提示词注入让 LLM 返回畸形 JSON，触发解析异常或逻辑绕过。 |
| **修复建议** | 1. 在 `json.loads` 后增加对象类型断言（`isinstance(parsed_json, dict)`）。2. 对 `content` 增加最大长度限制（如 <= 100KB），防止内存膨胀。3. 考虑使用 `orjson` 替代 `json` 以获得更严格的解析性能。 |

---

## 2. 敏感数据暴露 (Sensitive Data Exposure)

### 2.1 API 密钥管理

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `src/llm_parser.py:51-78` |
| **描述** | LLM API 密钥（`SENSENOVA_API_KEY`, `GEMINI_API_KEY`, `SILICONFLOW_API_KEY`）均通过 `os.getenv()` 从环境变量读取，**无硬编码密钥**。符合安全最佳实践。 |
| **攻击场景** | 但 `llm_parser.py` 在初始化时将密钥明文存储在 `self.providers` 列表中。若应用发生内存转储（core dump）或被调试器 attach，密钥可能泄露。此外，日志中未过滤密钥，但当前代码未直接记录 `self.providers`。 |
| **修复建议** | 1. 考虑使用 `pydantic.SecretStr` 包装 API 密钥，避免在内存中长时间以明文 `str` 存在。2. 确保日志配置中禁止打印 `self.providers` 或任何请求头。3. 在 `_call_provider` 中构造 `headers` 时，避免将完整 `provider` dict 传入日志。 |

### 2.2 日志中的敏感信息

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/llm_parser.py:206`, `src/llm_parser.py:260` |
| **描述** | 日志记录 `Sending LLM parsing request ({model_name})...`，未记录 API 密钥或请求体内容。`src/scraper.py` 中的日志记录 URL 和 HTML 长度，亦不包含凭证。 |
| **攻击场景** | 若日志级别设为 `DEBUG` 且 httpx 的底层日志开启，可能记录完整的 HTTP 请求头（含 `Authorization: Bearer <key>`）。 |
| **修复建议** | 在 `setup_logging` 或 uvicorn 启动配置中，为 `httpx` 和 `httpcore` logger 设置级别为 `WARNING`，防止底层库泄露请求头。 |

### 2.3 硬编码密钥 / URL

| 项目 | 详情 |
|------|------|
| **严重程度** | INFO |
| **位置** | 全局配置 |
| **描述** | 代码中未发现硬编码的 API 密钥、密码或私有 Token。所有外部服务端点（Wikidata SPARQL、AIC API、Whitney API、MoMA GitHub CSV）均为公开资源。 |
| **修复建议** | 保持现状。对任何未来新增的付费/私有 API，继续通过环境变量注入。 |

---

## 3. SSRF (服务器端请求伪造)

### 3.1 用户可控 URL 传入爬虫

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `run_collector.py:131-135`, `src/scraper.py:46-74` |
| **描述** | CLI 参数 `--site` 用于从 `SITES` 注册表中获取对应的 `parser`，随后调用 `parser.get_exhibition_urls()`。`site_key` 经过 `lower().strip()` 处理，但**未验证是否为允许的键**。虽然 `SITES` 字典起到了白名单作用，但 `since_year` 和 `limit` 等参数被直接传入 parser。 |
| **攻击场景** | 攻击者无法直接通过 `--site` 注入任意 URL，因为 `SITES` 是硬编码注册表。但若某个 parser 的实现存在漏洞（如动态构造 URL 时未校验），可能产生 SSRF。例如 `src/sites/tate.py:30-38` 的 `get_list_urls` 根据 `since_year` 构造查询参数，若 `since_year` 被异常放大，仅导致生成大量 URL，无 SSRF 风险。 |
| **修复建议** | 1. 确保所有 parser 中的 `list_url` / `extra_list_urls` 为硬编码字符串，不依赖外部输入。2. 对 `since_year` 增加范围校验（当前 `run_collector.py:84-88` 已校验 1900-current_year，符合要求）。3. 禁止 parser 接受任意 URL 参数。 |

### 3.2 爬虫请求重定向

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/scraper.py:39-42`, `src/scraper.py:330-333` |
| **描述** | `httpx.Client` 和 `AsyncClient` 均设置了 `follow_redirects=True`。在 HTML_LLM 策略中，请求的 URL 来自 parser 的白名单发现逻辑，但重定向目标不受控制。 |
| **攻击场景** | 若被爬取的机构域名被劫持，或展览页面包含恶意重定向（如 `meta refresh` 或 302 到内网地址），爬虫可能访问内部网络资源。 |
| **修复建议** | 1. 为 `httpx.Client` 增加 `max_redirects` 限制（如 <= 5）。2. 考虑在请求后检查最终响应 URL 的域名是否仍在预期的机构域名列表中。3. 对 `curl_cffi` 和 `scrapling` 的 fallback 调用同样增加重定向限制。 |

---

## 4. XSS 与输出消毒 (XSS & Output Sanitization)

### 4.1 Web API 返回未经消毒的数据

| 项目 | 详情 |
|------|------|
| **严重程度** | HIGH |
| **位置** | `src/web/app.py:104`, `src/web/app.py:150`, `src/web/app.py:230`, `src/web/app.py:317`, `src/web/app.py:359` |
| **描述** | FastAPI 接口返回的 JSON 数据中包含直接从数据库读取的展览标题、前言、策展人、艺术家姓名等字段。FastAPI 默认返回 `application/json`，**JSON 响应本身不受反射型 XSS 影响**。但前端 `index.html` / `app.js` 将这些数据直接插入 DOM。 |
| **攻击场景** | 若数据库中某条展览记录的 `title`、`preface`、`concept`、`artist_name` 等字段包含 `<script>alert(1)</script>` 或事件处理器（如 `onclick=...`），前端 `app.js` 使用 `innerHTML` 和 `textContent` 混合插入，部分字段可能被执行。具体风险点：<br>1. `app.js:741` `ex.title` 直接插入 `innerHTML`（通过模板字符串）。<br>2. `app.js:789-792` `modal-title`, `modal-source` 使用 `textContent`，安全。<br>3. `app.js:977-982` `renderBilingualTexts` 使用 `textContent`，安全。<br>4. `app.js:888-894`  artworks 表格使用 `innerHTML` 插入 `art.artist_name`, `art.work_title`, `art.medium` 等，**存在存储型 XSS 风险**。 |
| **修复建议** | **紧急修复**：在 `app.js` 中所有使用 `innerHTML` 插入用户/数据库可控数据的位置，改用 `textContent` 或先进行 HTML 实体编码。例如：<br>```js
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
```<br>然后对 `ex.title`, `art.artist_name`, `art.work_title`, `art.medium`, `art.dimensions` 等字段调用 `escapeHtml()` 后再插入。 |

### 4.2 CORS 配置过于宽松

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `src/web/app.py:19-25` |
| **描述** | CORS 中间件配置为 `allow_origins=["*"]`，允许任何来源访问 API。在本地开发场景下常见，但若部署到公网，会导致敏感数据被第三方网站通过 AJAX 读取。 |
| **攻击场景** | 攻击者搭建恶意网站，诱导已登录（或处于内网）的用户访问，从而通过浏览器窃取展览数据或执行未授权查询。 |
| **修复建议** | 1. 生产环境将 `allow_origins` 限制为实际的前端域名。2. 通过环境变量 `CORS_ORIGINS` 动态配置，默认仅允许 `localhost`。3. 若必须开放，至少关闭 `allow_credentials=True`（当前开启，与 `*` 组合是危险配置）。 |

---

## 5. 路径遍历 (Path Traversal)

### 5.1 数据库路径可控

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `run_collector.py:74`, `run_collector.py:92`, `src/scraper.py:36`, `src/database.py:11`, `src/cache.py:22` |
| **描述** | CLI 参数 `--db` 允许用户指定任意 SQLite 数据库路径，默认值为 `exhibitions.db`。该路径被直接传入 `sqlite3.connect()` 和 `open()`。 |
| **攻击场景** | 攻击者可通过 `--db ../../../etc/passwd` 尝试读取系统文件（虽然 SQLite 会尝试创建/打开数据库文件，而非直接泄露内容）。更严重的场景是：**若目录可写**，攻击者可以覆盖任意 `.db` 文件，或向已知路径写入数据库以配合后续攻击。此外，`src/web/app.py:27` 的 `DB_PATH = "exhibitions.db"` 为硬编码，与 CLI 参数不一致，可能导致数据隔离失效。 |
| **修复建议** | 1. 对 `--db` 参数进行路径规范化：`os.path.abspath` + 禁止路径包含 `..`。2. 限制 `--db` 只能指向项目工作目录或其子目录。3. 统一 `run_collector.py` 和 `src/web/app.py` 的数据库路径配置，建议通过环境变量 `DB_PATH` 统一管理。 |

### 5.2 CSV 本地文件读取

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/sites/moma.py:24`, `src/sites/nga.py:20-24` |
| **描述** | MoMA 和 NGA parser 使用硬编码的相对路径读取本地 CSV 文件（如 `data/moma_github/...`, `data/nga_collection/...`）。路径不可由用户控制。 |
| **攻击场景** | 无直接路径遍历风险，因为路径为常量。但若工作目录被篡改，可能读取到非预期的同路径文件。 |
| **修复建议** | 使用 `os.path.join(os.path.dirname(__file__), "../../data/...")` 将相对路径锚定到项目根目录，避免依赖运行时 CWD。 |

---

## 6. 依赖漏洞 (Dependency Vulnerabilities)

### 6.1 依赖清单审查

| 包名 | 声明版本 | 风险说明 |
|------|----------|----------|
| `httpx` | `>=0.27.0` | 2024 年 6 月后的版本修复了若干 HTTP/2 拒绝服务漏洞。建议升级到 `>=0.28.0`。 |
| `beautifulsoup4` | `>=4.12.0` | 该版本系列无已知高危 CVE，但需注意 `lxml` 解析器（若使用）的底层漏洞。当前代码使用默认的 `html.parser`，安全。 |
| `pydantic` | `>=2.7.0` | Pydantic v2 系列总体安全。建议保持最新 patch 版本。 |
| `playwright` | `>=1.40.0` | Playwright 定期发布 Chromium/Firefox/WebKit 安全更新。建议跟踪最新版本。 |
| `fastapi` | `>=0.110.0` | 该版本系列无已知严重漏洞，但需关注 Starlette 底层依赖。 |
| `uvicorn` | `>=0.28.0` | 标准 ASGI 服务器，保持更新即可。 |

### 6.2 缺失的依赖锁定

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `requirements.txt`, `pyproject.toml` |
| **描述** | `requirements.txt` 使用 `>=` 下限约束，无上限锁定。`pyproject.toml` 同样未指定精确版本。这可能导致 CI/生产环境拉取到包含新漏洞或破坏性变更的最新版本。 |
| **修复建议** | 1. 使用 `uv pip compile` 生成 `requirements.lock` 或 `uv.lock`（项目根目录已存在 `uv.lock`，应确保其被版本控制并用于生产部署）。2. 定期运行 `uv pip audit` 或 `pip-audit` 扫描已知 CVE。 |

---

## 7. 拒绝服务 (Denial of Service)

### 7.1 无界 HTML 处理

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `src/scraper.py:204`, `src/scraper.py:338` |
| **描述** | `parser.clean_html(page_html)` 对完整的 HTML 页面进行 BeautifulSoup 解析和文本提取。若目标页面返回超大 HTML（如数百 MB 的日志文件或恶意生成的垃圾页面），会导致内存暴涨。 |
| **攻击场景** | 攻击者若控制某个被爬取的展览页面（如在机构网站的评论/UGC 区域注入恶意内容，或机构本身被入侵），可返回超大响应，导致爬虫进程 OOM。 |
| **修复建议** | 1. 在 `self.client.get()` 前增加 `max_content_length` 限制（httpx 可通过自定义 transport 实现，或在响应后检查 `len(response.content)`）。2. 若页面大小超过阈值（如 5MB），跳过处理并记录警告。3. 对 `clean_html` 的输入增加截断逻辑。 |

### 7.2 图片 URL 提取无界

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/scraper.py:220-237` |
| **描述** | 图片提取逻辑遍历页面所有 `<img>` 标签，最多保留 8 张（`[:8]`），但遍历前未限制 soup 中 img 标签的数量。若页面包含数万张图片标签，遍历和 `urljoin` 会消耗 CPU。 |
| **攻击场景** | 恶意页面包含大量 `<img src="...">` 标签，导致 CPU 短暂飙升。 |
| **修复建议** | 在 `soup.find_all("img", src=True)` 后增加 `[:50]` 截断，或改用 `soup.find_all("img", src=True, limit=50)`。 |

### 7.3 无限循环风险

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/sites/aic.py:77`, `src/sites/whitney.py:44` |
| **描述** | AIC 和 Whitney parser 使用 `while True` 进行 API 分页，依赖 `total_pages` 或空 `items` 列表退出循环。当前实现有明确的终止条件（`page >= total_pages` 或 `not items`），且每次循环有 `time.sleep()` 限速。 |
| **攻击场景** | 若 API 返回畸形响应（如 `total_pages` 永远大于 `page`，或 `items` 永远非空），会导致无限循环。 |
| **修复建议** | 增加绝对上限保护，如 `if page > 1000: break`，防止极端情况下的无限循环。 |

### 7.4 LLM max_tokens 限制

| 项目 | 详情 |
|------|------|
| **严重程度** | INFO |
| **位置** | `src/llm_parser.py:198`, `src/llm_parser.py:252` |
| **描述** | LLM 请求已设置 `max_tokens: 8192`，有效防止了模型返回超大响应导致的内存问题。 |
| **修复建议** | 保持当前限制。可考虑根据输入文本长度动态调整 `max_tokens`（如输入越短，输出上限越低），进一步节省成本。 |

### 7.5 并发控制

| 项目 | 详情 |
|------|------|
| **严重程度** | INFO |
| **位置** | `src/scraper.py:305` |
| **描述** | 异步模式使用 `asyncio.Semaphore(self.max_concurrency)`，默认并发数为 10，有效防止了对单一目标站点的连接洪泛。 |
| **修复建议** | 保持当前设计。可考虑为不同站点设置不同的并发上限（如某些站点要求更低的 QPS）。 |

---

## 8. 其他发现

### 8.1 SSL 证书验证被禁用

| 项目 | 详情 |
|------|------|
| **严重程度** | MEDIUM |
| **位置** | `src/sites/base.py:114` |
| **描述** | 对于 `verify_ssl=False` 的 parser，使用 `httpx.Client(verify=False)` 发起请求。这会禁用 SSL 证书验证，使连接容易受到中间人攻击（MITM）。 |
| **攻击场景** | 在不可信网络环境下，攻击者可伪造目标机构网站证书，拦截或篡改爬虫请求/响应，进而注入恶意 HTML 或窃取数据。 |
| **修复建议** | 1. 尽可能修复目标站点的证书问题（如更新根证书、使用正确的 hostname）。2. 若必须禁用验证，应在日志中输出强烈警告，并限制仅对特定已知有证书问题的域名生效。3. 考虑使用 `curl_cffi` 的 `verify=False` 作为替代，而非全局禁用。 |

### 8.2 前端图片 URL 直接渲染

| 项目 | 详情 |
|------|------|
| **严重程度** | LOW |
| **位置** | `src/web/static/app.js:846-855` |
| **描述** | 展览详情弹窗中的图片通过 `<img src="${imgUrl}">` 直接渲染，且 `imgUrl` 来自数据库中的 `images` JSON 字段。这些 URL 由爬虫从机构官网提取，理论上可信。 |
| **攻击场景** | 若机构网站被入侵，图片 URL 可能被替换为指向攻击者服务器的追踪像素或恶意内容。此外，直接加载第三方图片会泄露用户 IP 和 Referer。 |
| **修复建议** | 1. 增加图片域名白名单校验，仅允许来自已知机构 CDN 域名的图片。2. 对图片 URL 进行签名或代理，避免前端直接请求第三方服务器。3. 增加 `referrerpolicy="no-referrer"` 和 `crossorigin="anonymous"` 属性。 |

---

## 总结与优先级修复清单

| 优先级 | 严重程度 | 问题 | 负责文件 | 修复动作 |
|--------|----------|------|----------|----------|
| P0 | HIGH | 前端存储型 XSS | `src/web/static/app.js` | 将所有 `innerHTML` 插入数据库字段的位置改为 `textContent` 或 `escapeHtml()` |
| P1 | MEDIUM | CORS 过于宽松 | `src/web/app.py:19-25` | 生产环境限制 `allow_origins`，关闭 `allow_credentials` 或绑定具体域名 |
| P1 | MEDIUM | 数据库路径遍历 | `run_collector.py`, `src/web/app.py` | 对 `--db` 参数做路径规范化并限制在项目目录内；统一 Web 与 CLI 的数据库路径 |
| P1 | MEDIUM | SSL 验证禁用 | `src/sites/base.py:114` | 减少 `verify=False` 的使用范围，增加警告日志 |
| P2 | MEDIUM | API 密钥内存明文 | `src/llm_parser.py` | 使用 `SecretStr` 包装密钥，避免明文常驻内存 |
| P2 | MEDIUM | 无界 HTML 处理 | `src/scraper.py` | 增加响应大小上限检查（如 5MB） |
| P2 | LOW | 前端图片直接加载 | `src/web/static/app.js` | 增加域名白名单或图片代理 |
| P2 | LOW | 依赖版本未锁定 | `pyproject.toml` | 确保 `uv.lock` 用于生产，定期运行 `pip-audit` |
| P3 | LOW | 无限循环保护 | `src/sites/aic.py`, `src/sites/whitney.py` | 增加分页绝对上限（如 1000 页） |
| P3 | LOW | 日志可能泄露凭证 | `logging` 配置 | 将 `httpx`/`httpcore` logger 级别设为 `WARNING` |

---

*报告结束*
