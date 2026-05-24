# Phase 4: 全量端到端验证与数据质量攻坚

## 背景

Phase 0-3 已完成架构重构与 64 家机构的 parser 注册。但当前系统存在以下关键缺口：

- **URL 发现仅验证 23/33 家 Phase 3 机构**，剩余大量 parser 尚未验证
- **LLM 解析零验证**：除早期 12 家机构外，新增 50+ 家机构未经过实际的 HTML → LLM → 结构化数据流程验证
- **已知技术障碍未解决**：10+ 个 parser 受 Cloudflare 403、SPA 渲染、SSL 证书错误限制
- **数据质量黑盒**：数据库中 ~8,000 条记录存在字段缺失、日期格式不一致、重复展览等问题

## 目标

在 Phase 4 结束时，系统应达到：
1. **90%+ 机构** 可通过 `run_collector.py --site <key> --limit 3 --dry-run` 成功完成端到端解析
2. **数据质量基线** 建立：关键字段（title, start_date, city, url）缺失率 < 5%
3. **问题机构分级清单**：明确区分 "可修复" / "需 Playwright" / "需替代数据源" / "暂时搁置"
4. **运营监控基础**：health check 脚本可用，scraper 运行日志可追踪

---

## 任务分解

### 任务 1：全量 Smoke Test 与 URL 发现修复

**目标**：验证全部 64 个 parser 的 `get_exhibition_urls()` 至少能返回 >0 个 URL。

**执行方式**：
```bash
python run_collector.py --list-sites | awk '{print $2}' | xargs -I{} sh -c 'echo "=== {} ==="; python run_collector.py --site {} --limit 1 --dry-run 2>&1 | tail -5'
```

**分级标准**：
| 状态 | URL 数量 | 处理策略 |
|:--|:--|:--|
| 绿色 | >= 5 | 正常进入 LLM 验证 |
| 黄色 | 1-4 | 检查 pattern 是否过严，尝试放宽 |
| 红色 | 0 | 诊断：curl 测试 → 检查 403/404/SSL/SPA → 分级处理 |

**产出**：`docs/plans/smoke-test-report-YYYY-MM-DD.md`

---

### 任务 2：有限深度 LLM 解析验证

**目标**：对任务 1 中绿色/黄色状态的 parser，每家取 3 个 URL 执行真实 LLM 解析（dry-run 或不 dry-run），验证输出质量。

**关注点**：
- `title` 是否被正确提取（非 "Homepage" / "Menu" 等噪音）
- `start_date` / `end_date` 格式是否为 `YYYY-MM-DD`
- `curators` 是否被正确识别为列表（非字符串）
- `concept` 是否有实质内容（非空或仅复制标题）
- 作品列表 `artworks` 是否被正确提取

**问题记录模板**：
```markdown
### <parser_key>
- URL: <url>
- 问题: <描述>
- 根因推测: <HTML 结构 / LLM prompt / 字段映射>
- 修复方案: <具体改动>
```

---

### 任务 3：技术障碍 Parser 分级处理

对任务 1 中红色状态的 parser，按以下路径处理：

#### 路径 A：Cloudflare 403（lacma, dia, whitechapel, hayward, mass_moca 等）
- **尝试 1**：强化 HEADERS（已做，效果有限）
- **尝试 2**：引入 `curl_cffi` 或 `httpx` + `browserforge` 进行 TLS/JA3 指纹模拟
- **判定**：若尝试 2 失败，标记为 `BLOCKED_CLOUDFLARE`，寻找替代数据源（Wikidata / Google Arts / 官方 API）

#### 路径 B：SPA / React 渲染（psa, new_museum, momat, leeum, mca_australia, flv, pinakothek）
- **PSA 已有 Playwright 实现**，提取为通用 Playwright mixin
- **评估每家**：是否值得引入 Playwright（启动成本 ~2-3s/页）
- **判定**：高价值机构（PSA, MOMAT）用 Playwright；低价值机构标记为 `BLOCKED_SPA`

#### 路径 C：SSL 证书错误（hamburger_bahnhof）
- 尝试 `verify=False` + 检查证书链
- 判定：若无法修复，标记为 `BLOCKED_SSL`

**产出**：在 `CLAUDE.md` 的机构表中更新每家机构的 `status` 字段（如 `ok`, `blocked_cloudflare`, `blocked_spa`, `needs_playwright`）。

---

### 任务 4：数据质量清洗与 Schema 加固

**目标**：基于已有 ~8,000 条记录，建立数据质量基线。

#### 4.1 缺失字段分析
```sql
SELECT source,
       count(*) as total,
       sum(case when title is null or title = '' then 1 else 0 end) as missing_title,
       sum(case when start_date is null then 1 else 0 end) as missing_start,
       sum(case when concept is null or concept = '' then 1 else 0 end) as missing_concept
FROM exhibitions
GROUP BY source;
```

#### 4.2 日期格式标准化
- 现有日期格式混杂：`YYYY-MM-DD`, `YYYY-MM`, `YYYY`
- 方案：LLM prompt 中强制要求 `YYYY-MM-DD` 格式；对已有数据用 Python 正则规范化

#### 4.3 重复展览检测
- 同一机构、同一 title、相近 start_date 的重复记录
- 方案：添加 `scripts/dedup_exhibitions.py`，基于 `(source, title, start_date)` fuzzy match

#### 4.4 策展人字段回填
- 现有记录的 `curators` 均为 `'[]'`（schema v2 新增字段）
- 方案：对高价值机构（MoMA, Tate, Whitney）手动检查原始数据，验证 LLM 是否能提取策展人信息

---

### 任务 5：Health Check 脚本与运行日志

#### 5.1 Health Check 脚本 (`scripts/health_check.py`)
```bash
python scripts/health_check.py
# 输出：
# PASS  moma        34 URLs  1.2s
# PASS  tate        120 URLs 2.1s
# WARN  maxxi       2 URLs   1.5s   (only 2 URLs found)
# FAIL  lacma       0 URLs   0.8s   HTTP 403
```

功能：
- 遍历所有 SITES，执行 `--limit 1 --dry-run`
- 记录 HTTP 状态码、URL 数量、耗时
- 生成 Markdown 报告

#### 5.2 Scraper Runs 日志表
```sql
CREATE TABLE scraper_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parser_key TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    urls_discovered INTEGER DEFAULT 0,
    urls_parsed INTEGER DEFAULT 0,
    exhibitions_saved INTEGER DEFAULT 0,
    exhibitions_failed INTEGER DEFAULT 0,
    error_message TEXT,
    run_type TEXT DEFAULT 'full'  -- 'full', 'limit', 'dry_run'
);
```

在 `ExhibitionScraper.scrape_site()` 开始和结束时插入记录。

---

## 验证标准

| 指标 | 目标值 | 验证方式 |
|:--|:--|:--|
| Smoke Test 通过率 | >= 90% (58/64) | `scripts/health_check.py` |
| LLM 解析成功率 | >= 85% 的 URL 返回有效 ExhibitionModel | 抽样 3 URL/parser |
| 关键字段缺失率 | < 5% | SQL 查询 |
| Health Check 执行时间 | < 5 分钟全量 | `time python scripts/health_check.py` |

---

## 时间估算

| 任务 | 工作量 | 预估时间 |
|:--|:--|:--|
| 任务 1：Smoke Test + URL 修复 | 高（64 家逐一验证）| 2-3 小时 |
| 任务 2：LLM 解析验证 | 高（每家 3 URL × LLM 调用）| 3-4 小时 |
| 任务 3：技术障碍分级 | 中（评估 + 少量代码改动）| 1-2 小时 |
| 任务 4：数据质量清洗 | 中（SQL + Python 脚本）| 2-3 小时 |
| 任务 5：Health Check + 日志表 | 低（独立脚本，不影响核心）| 1-2 小时 |
| **总计** | | **9-14 小时** |

---

## 可选扩展（Phase 5 候选）

若 Phase 4 提前完成或用户有额外需求，以下任务可纳入：

1. **Async 并发爬取**：`httpx.AsyncClient` + `asyncio.Semaphore(10)`，将全量采集从小时级降至分钟级
2. **LLM 响应缓存**：按 URL hash 缓存结构化结果，避免重复调用（节省 30-50% LLM 成本）
3. **Biennial Series 关联表**：将 "Documenta 1-15"、"Venice Biennale 1895-2024" 等按系列聚合
4. **Web Dashboard 增强**：搜索、过滤、按城市/时间线可视化展览分布
5. **自动化 CI Health Check**：GitHub Actions 每日运行 `scripts/health_check.py`，检测网站结构变更
