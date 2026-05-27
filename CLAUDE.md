# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Auto Curation 是一个**模块化全球当代艺术展览数据采集与结构化存储系统**。它从全球 65 家顶级艺术机构（美术馆、双年展、三年展）抓取展览数据，通过六种策略转化为结构化数据，存入 SQLite 数据库。

---

## 常用命令

### 依赖管理

```bash
uv pip install -r requirements.txt
```

### 运行采集器

```bash
# 列出所有支持的机构及其历史数据支持情况
python run_collector.py --list-sites

# 采集单个机构（示例：M+ Museum）
python run_collector.py --site mplus

# 全量采集所有机构
python run_collector.py --all

# 限制每站处理数量（测试用）
python run_collector.py --site serpentine --limit 3

# 按年份过滤（支持 moma / tate / mori / mplus / serpentine）
python run_collector.py --site moma --since 1970

# 模拟运行，不写入数据库
python run_collector.py --site mori --dry-run --limit 2

# 强制重新抓取（跳过去重检查）
python run_collector.py --site tate --force

# 详细 DEBUG 日志
python run_collector.py --site mplus --verbose
```

### 数据库查询

```bash
# 快速统计
python -c "import sqlite3; conn=sqlite3.connect('exhibitions.db'); print('展览:', conn.execute('SELECT count(*) FROM exhibitions').fetchone()[0]); print('作品:', conn.execute('SELECT count(*) FROM artworks').fetchone()[0]); [print(f'  {r[0]}: {r[1]}') for r in conn.execute('SELECT source, count(*) FROM exhibitions GROUP BY source ORDER BY 2 DESC')]"
```

---

## 高层架构

### 六种采集策略

`ExhibitionScraper`（`src/scraper.py`）根据 parser 声明的 `strategy` 属性自动路由到对应策略：

| 策略 | 触发条件 | 适用机构 | 说明 |
|:--|:--|:--|:--|
| **HTML_LLM** | `BaseSiteParser` 子类（默认） | Tate, M+, Serpentine, Mori, PSA, UCCA 等 | 爬取官网，HTML 清洗后送 LLM 结构化提取 |
| **CSV_LOCAL** | `strategy = CSV_LOCAL` | NGA, The Met | 读取本地 GitHub 开放数据集 |
| **CSV_REMOTE** | `strategy = CSV_REMOTE` | MoMA | 下载远程 CSV 并解析 |
| **REST_API** | `strategy = REST_API` | AIC, Whitney | 直接拉取 JSON API |
| **SPARQL** | `strategy = SPARQL` | Wikidata (SFMOMA, Stedelijk, Van Gogh) | Wikidata SPARQL 查询 |
| **ARTWORK_ONLY** | `strategy = ARTWORK_ONLY` | NGA | 无展览数据，仅作品，创建虚拟 "Permanent Collection" 记录 |

**Native Extraction 回退**：若 parser 实现了 `parse_exhibition_page(client, url)` 并返回 dict，则跳过 LLM 调用（如 PSA、Kunsthaus）。

### 数据流

```
[URL 发现 / CSV 读取 / API 分页]
         │
         ▼
[HTML 清洗 / CSV 聚合 / JSON 解析]
         │
         ├──(HTML)──▶ [Gemini LLM 结构化] ──▶ Pydantic 模型
         │
         ├──(CSV)───▶ [Python 聚合逻辑]  ──▶ Dict
         │
         └──(API)───▶ [JSON 直接映射]    ──▶ Dict
                            │
                            ▼
                  [去重检查 — url UNIQUE]
                            │
                            ▼
                    [exhibitions.db]
```

### 核心模块

| 文件 | 职责 |
|:--|:--|
| `run_collector.py` | CLI 入口，解析参数并调用 `ExhibitionScraper` |
| `src/scraper.py` | `ExhibitionScraper` 编排器，策略分发表路由，管理 httpx 客户端 |
| `src/database.py` | `ExhibitionDatabase`，SQLite 连接与 CRUD，`url` 字段为唯一去重键 |
| `src/llm_parser.py` | `LLMExhibitionParser`，多供应商回退链（SenseNova → Gemini → SiliconFlow），Pydantic 模型校验 |
| `src/sites/base.py` | `BaseSiteParser` 基类，`ParserStrategy` enum，封装列表页抓取、URL 发现、HTML 清洗 |
| `src/sites/__init__.py` | `pkgutil` + `inspect` 自动扫描注册全部 parser，无需手动导入 |
| `src/sites/<key>.py` | 各机构专属解析器（见下表） |

### 机构与策略对照（精选）

原有 12 家 + Phase 1-3 新增 53 家，总计 65 家注册机构。

| Key | 机构 | 城市 | 策略 | 状态 |
|:--|:--|:--|:--|:--|
| `moma` | MoMA | New York | CSV_REMOTE | ok |
| `tate` | Tate Modern | London | HTML_LLM | ok |
| `mplus` | M+ Museum | Hong Kong | HTML_LLM | ok |
| `serpentine` | Serpentine Galleries | London | HTML_LLM | ok |
| `mori` | Mori Art Museum | Tokyo | HTML_LLM | ok |
| `aic` | Art Institute of Chicago | Chicago | REST_API | ok |
| `nga` | National Gallery of Art | Washington D.C. | ARTWORK_ONLY | ok |
| `met` | The Met | New York | CSV_LOCAL | ok |
| `pompidou` | Centre Pompidou | Paris | HTML_LLM | ok |
| `guggenheim` | Guggenheim | New York | HTML_LLM | blocked_cloudflare |
| `biennale` | Venice Biennale | Venice | HTML_LLM | ok |
| `whitney` | Whitney Museum | New York | REST_API | ok |
| `kunsthaus` | Kunsthaus Zürich | Zürich | HTML_LLM | ok |
| `psa` | Power Station of Art | Shanghai | HTML_LLM | ok |
| `ucca` | UCCA | Beijing | HTML_LLM | ok |
| `documenta` | Documenta | Kassel | HTML_LLM | ok |
| `berlin_biennale` | Berlin Biennale | Berlin | HTML_LLM | ok |
| `gwangju_biennale` | Gwangju Biennale | Gwangju | HTML_LLM | ok |
| `istanbul_biennale` | Istanbul Biennial | Istanbul | HTML_LLM | ok |
| `lyon_biennale` | Lyon Biennale | Lyon | HTML_LLM | ok |
| `liverpool_biennale` | Liverpool Biennial | Liverpool | HTML_LLM | ok |
| `taipei_biennale` | Taipei Biennial | Taipei | HTML_LLM | ok |
| `yokohama_triennale` | Yokohama Triennale | Yokohama | HTML_LLM | ok |
| `sydney_biennale` | Sydney Biennale | Sydney | HTML_LLM | ok |
| `sharjah_biennale` | Sharjah Biennial | Sharjah | HTML_LLM | ok |
| `saopaulo_biennial` | São Paulo Biennial | São Paulo | HTML_LLM | ok |
| `maxxi` | MAXXI | Rome | HTML_LLM | ok |
| `kw_institute` | KW Institute | Berlin | HTML_LLM | ok |
| `lenbachhaus` | Lenbachhaus | Munich | HTML_LLM | ok |
| `baltic` | BALTIC | Gateshead | HTML_LLM | ok |
| `brooklyn_museum` | Brooklyn Museum | New York | HTML_LLM | ok |
| `mca_chicago` | MCA Chicago | Chicago | HTML_LLM | ok |
| `barbican` | Barbican Centre | London | HTML_LLM | ok |
| `national_gallery_sg` | National Gallery Singapore | Singapore | HTML_LLM | ok |
| `maiiam` | MAIIAM | Chiang Mai | HTML_LLM | ok |
| `njpac` | Nam June Paik Art Center | Yongin | HTML_LLM | ok |
| `reina_sofia` | Museo Reina Sofía | Madrid | HTML_LLM | ok |
| `kanazawa21` | 21st Century Museum | Kanazawa | HTML_LLM | ok |
| `new_museum` | New Museum | New York | HTML_LLM | ok |
| `lacma` | LACMA | Los Angeles | HTML_LLM | blocked_cloudflare |
| `dia` | Dia Art Foundation | New York | HTML_LLM | blocked_cloudflare |
| `whitechapel` | Whitechapel Gallery | London | HTML_LLM | blocked_cloudflare |
| `hayward` | Hayward Gallery | London | HTML_LLM | blocked_cloudflare |
| `mass_moca` | MASS MoCA | North Adams | HTML_LLM | blocked_cloudflare |
| `flv` | Fondation Louis Vuitton | Paris | HTML_LLM | blocked_spa |
| `momat` | MOMAT | Tokyo | HTML_LLM | ok |
| `leeum` | Leeum Samsung Museum | Seoul | HTML_LLM | warn |
| `mca_australia` | MCA Australia | Sydney | HTML_LLM | ok |
| `pinakothek` | Pinakothek der Moderne | Munich | HTML_LLM | warn |
| `hamburger_bahnhof` | Hamburger Bahnhof | Berlin | HTML_LLM | ok |
| `astrup_fearnley` | Astrup Fearnley | Oslo | HTML_LLM | ok |
| `beyeler` | Fondation Beyeler | Basel | HTML_LLM | ok |
| `hammer_museum` | Hammer Museum | Los Angeles | HTML_LLM | ok |
| `hirshhorn` | Hirshhorn Museum | Washington D.C. | HTML_LLM | blocked_api_key |
| `kunsthal` | Kunsthal Rotterdam | Rotterdam | HTML_LLM | ok |
| `louisiana` | Louisiana Museum | Humlebæk | HTML_LLM | ok |
| `museum_ludwig` | Museum Ludwig | Cologne | HTML_LLM | ok |
| `ngv` | National Gallery of Victoria | Melbourne | HTML_LLM | ok |
| `palaistokyo` | Palais de Tokyo | Paris | HTML_LLM | ok |
| `south_london_gallery` | South London Gallery | London | HTML_LLM | warn |
| `whitney_biennial` | Whitney Biennial | New York | HTML_LLM | ok |
| `wikidata` | Wikidata | Various | SPARQL | ok |
| `zkm` | ZKM | Karlsruhe | HTML_LLM | ok |

完整列表运行 `python run_collector.py --list-sites` 查看。

**状态图例**：
- `ok` — URL 发现正常（≥5 个或策略预期数量）
- `warn` — URL 发现偏少（1–4 个），pattern 可能过严
- `blocked_cloudflare` — Cloudflare 403 封锁，需替代数据源
- `blocked_spa` — SPA 渲染失败，Playwright 无法解决
- `blocked_api_key` — 需要 API Key 才能访问
- `needs_playwright` — 需要 Playwright 渲染（已配置但可能不稳定）

**Red 站点修复评估（2026-05-27）**：
以下 8 家 red parser 已穷尽现有绕过方案，明确记录为不可修复，后续无需再尝试：
- `dia` — Playwright 超时，curl_cffi 未安装但普通请求已 403
- `guggenheim` — Scrapling StealthyFetcher 已失败
- `hayward` — curl_cffi 已失败
- `lacma` — curl_cffi 已失败
- `mass_moca` — curl_cffi 已失败
- `whitechapel` — curl_cffi 已失败
- `flv` — Scrapling StealthyFetcher 已失败（Akamai CDN）
- `hirshhorn` — 需要 Smithsonian API Key

**Yellow→Green 修复（2026-05-27）**：
- `louisiana` — 修正 list_url 为 `/exhibitions/current/`，添加 past/upcoming extra_list_urls：1→131 URLs
- `beyeler` — 启用 Playwright，添加 past-exhibitions 页面，修正 link_patterns：3→20 URLs

---

## 数据库 Schema (v2)

SQLite，两张核心表：

- **`exhibitions`**：`id`, `source`, `title`, `preface`, `concept`, `curators` (JSON), `start_date`, `end_date`, `location`, `city`, `url` (UNIQUE), `scraped_at`, `institution_type`, `parser_key`
- **`artworks`**：`id`, `exhibition_id` (FK), `artist_name`, `work_title`, `work_year`, `medium`, `dimensions`, `caption`

索引：`idx_exhibitions_source`, `idx_exhibitions_city`, `idx_exhibitions_start_date`, `idx_exhibitions_parser_key`

---

## 环境变量

| 变量 | 说明 |
|:--|:--|
| `SENSENOVA_API_KEY` | 首选 LLM 密钥（DeepSeek-V3-1） |
| `SENSENOVA_BASE_URL` | 可选，默认 `https://api.sensenova.cn/compatible-mode/v1` |
| `GEMINI_API_KEY` | 次选 LLM 密钥（gemini-2.5-flash） |
| `GEMINI_BASE_URL` | 可选，默认 `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `SILICONFLOW_API_KEY` | 第三备选密钥（DeepSeek-V3） |
| `SILICONFLOW_BASE_URL` | 可选，默认 `https://api.siliconflow.cn/v1` |

---

## 新增机构接入

1. 在 `src/sites/` 下新建解析器文件（继承 `BaseSiteParser` 或独立实现 CSV/API 逻辑）
2. 设置必需的类属性：`source`, `city`, `parser_key`, `list_url`, `link_patterns`
3. 声明 `strategy = ParserStrategy.XXX`（默认 HTML_LLM 可省略）
4. **自动注册**：`src/sites/__init__.py` 通过 `pkgutil.iter_modules()` 自动扫描，无需手动导入
5. 如需 Playwright（React SPA），参考 `src/sites/psa.py` 实现 `get_exhibition_urls()`

---

## 本地数据集

部分机构依赖预下载的 CSV 数据集（存放于 `data/`）：

- `data/moma_github/MoMAExhibitions1929to1989.csv` — MoMA 展览历史
- `data/nga_collection/` — NGA 多表（`objects.csv`, `constituents.csv`, `objects_constituents.csv`）
- `data/met_collection/MetObjects.csv` — The Met 开放数据
- `data/tate_collection/` — Tate 馆藏（已停更，截至 2014）
- `data/moma_collection/Artworks.csv` — MoMA 馆藏

---

## 技术栈

- Python 3.12+
- 依赖：`httpx`, `beautifulsoup4`, `pydantic`, `playwright`
- 包管理器：`uv`
