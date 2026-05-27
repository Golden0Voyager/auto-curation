# Phase 5: 数据扩展与系统优化

## 背景

Phase 4 已完成端到端验证与稳定性加固：
- 65 家机构全部注册，49 家绿色（≥5 URLs），3 家黄色，8 家红色（确认不可修复）
- 关键字段缺失率 < 5%（title 0%, start_date 0.3%, city 0%, concept 2.2%）
- 稳定性审计 8 项全部修复（LLM 防御、异步锁、重试、WAL、去重等）
- LLM 缓存、async 并发、前端 i18n 均已实现

Phase 5 聚焦两个方向：**数据扩展**（新增机构）和**系统优化**（运行效率、可维护性）。

---

## 任务分解

### 任务 1：欧洲博物馆 API 解析器（数据扩展）

**目标**：新增 3-5 家欧洲机构的 REST API 解析器，扩大数据覆盖范围。

**候选机构**（基于 `docs/europe_integration.md` 路线图）：

| 机构 | API | 密钥 | 预估数据量 |
|:--|:--|:--|:--|
| V&A Museum | `api.vam.ac.uk/v2/` | 不需要 | 800,000+ 藏品 |
| Rijksmuseum | `data.rijksmuseum.nl` | 不需要 | 500,000+ 藏品 |
| Europeana | `api.europeana.eu` | 需注册（免费） | 聚合多家欧洲馆 |

**执行方式**：
1. 为每家机构新建 `src/sites/<key>.py`，声明 `strategy = ParserStrategy.REST_API`
2. 实现 `get_api_exhibitions()` 方法
3. 运行 `python run_collector.py --site <key> --dry-run --limit 5` 验证
4. 端到端测试：确认 title, start_date, city 字段完整

**产出**：每家机构一个 parser 文件 + 测试验证

---

### 任务 2：双年展系列聚合表（数据增强）

**目标**：创建 `biennial_series` 关联表，将同一双年展的不同届次聚合。

**设计方案**：
```sql
CREATE TABLE biennial_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name TEXT NOT NULL,      -- e.g. "Venice Biennale"
    series_key TEXT UNIQUE NOT NULL, -- e.g. "venice_biennale"
    city TEXT,
    country TEXT,
    founded_year INTEGER,
    description TEXT
);

-- exhibitions 表新增 series_id 外键
ALTER TABLE exhibitions ADD COLUMN series_id INTEGER REFERENCES biennial_series(id);
```

**数据迁移**：
- 识别所有 parser_key 包含 "biennale" / "biennial" / "triennale" 的展览
- 按 source 分组创建系列记录
- 回填 exhibitions.series_id

---

### 任务 3：Health Check CI 自动化（运维）

**目标**：创建 GitHub Actions workflow，每日自动运行 health check。

**设计方案**：
```yaml
# .github/workflows/health-check.yml
name: Daily Health Check
on:
  schedule:
    - cron: '0 8 * * *'  # 每天 UTC 8:00
  workflow_dispatch:      # 手动触发

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install uv && uv pip install -r requirements.txt
      - run: python scripts/health_check.py --timeout 120
      - uses: actions/upload-artifact@v4
        with:
          name: health-check-report
          path: docs/plans/health-check-report-*.md
```

**产出**：`.github/workflows/health-check.yml`

---

### 任务 4：Scraper 运行日志查询工具（可维护性）

**目标**：创建 `scripts/scraper_history.py`，查询 scraper_runs 表历史记录。

**功能**：
```bash
python scripts/scraper_history.py                # 最近 20 次运行
python scripts/scraper_history.py --site moma     # 按机构过滤
python scripts/scraper_history.py --failed        # 只看失败的运行
python scripts/scraper_history.py --since 7d      # 最近 7 天
```

**产出**：`scripts/scraper_history.py`

---

## 验证标准

| 指标 | 目标值 | 验证方式 |
|:--|:--|:--|
| 新增机构数 | ≥ 3 家 | `run_collector.py --list-sites` |
| 新机构端到端通过 | 100% | `--dry-run --limit 3` |
| 双年展系列覆盖 | 全部 biennale/biennial parser | SQL 查询 |
| CI workflow 可运行 | 手动触发成功 | GitHub Actions |

---

## 时间估算

| 任务 | 工作量 | 预估时间 |
|:--|:--|:--|
| 任务 1：欧洲 API 解析器 | 高（每家 1-2h） | 3-6 小时 |
| 任务 2：双年展系列表 | 中 | 1-2 小时 |
| 任务 3：CI 自动化 | 低 | 0.5-1 小时 |
| 任务 4：运行日志工具 | 低 | 0.5-1 小时 |
| **总计** | | **5-10 小时** |

---

## 执行顺序

1. **任务 1**（欧洲 API 解析器）— 数据扩展优先
2. **任务 2**（双年展系列表）— 数据增强
3. **任务 4**（运行日志工具）— 运维工具
4. **任务 3**（CI 自动化）— 最后配置，依赖前序任务完成
