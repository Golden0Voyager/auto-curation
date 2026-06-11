# Auto Curation · 自动策展与艺术展览数据平台

> 模块化全球当代艺术展览数据采集系统，覆盖 61 家顶级艺术机构，支持多策略（HTML/CSV/API/SPARQL）自动结构化采集，LLM 智能提取并落地 SQLite。

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Golden0Voyager/auto_curation/ci.yml?branch=main&label=CI&logo=github)](.github/workflows/ci.yml)
[![coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](.github/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-475%20passed-brightgreen)](tests/)
[![mypy](https://img.shields.io/badge/mypy-0%20errors-success)](mypy.ini)
[![ruff](https://img.shields.io/badge/ruff-passing-brightgreen)](pyproject.toml)

---

## ✨ 核心特性

- **6 种采集策略**：HTML+LLM / 本地 CSV / 远程 CSV / REST API / SPARQL / 作品集模式，按机构特性自动路由
- **61 家注册机构**：覆盖 MoMA / Tate / M+ / Whitney / Guggenheim / 双年展体系 等
- **LLM 智能提取**：多供应商回退链（XIAOMI MIMO → Gemini → SiliconFlow），Pydantic 强校验
- **自动注册 parser**：基于 `pkgutil` 扫描，新机构仅需新增文件无需手动注册
- **质量监测**：日常健康检查 + 数据验证 + 异常告警（GitHub Actions 每日 UTC 08:03）
- **零合成数据**：所有字段必须来源于真实数据，缺失留空而非模板填充

## 📦 安装

需要 Python ≥ 3.12 与 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/Golden0Voyager/auto_curation.git
cd auto_curation
uv pip install -r requirements.txt
```

## 🚀 快速开始

```bash
# 列出所有支持的机构
python run_collector.py --list-sites

# 采集单个机构
python run_collector.py --site mplus

# 全量采集
python run_collector.py --all

# 模拟运行（不写数据库）
python run_collector.py --site mori --dry-run --limit 2

# 按年份过滤
python run_collector.py --site moma --since 1970
```

数据落地到本地 `exhibitions.db`（SQLite，已在 .gitignore）。

## 🏗️ 架构

```
[URL 发现 / CSV 读取 / API 分页]
         │
         ▼
[策略分发表] ── HTML_LLM ──▶ [HTML 清洗] ──▶ [LLM 提取] ──▶ Pydantic 校验
                │                              │
                ├── CSV_LOCAL  ──▶ [Python 聚合] ──┤
                ├── CSV_REMOTE ──▶ [下载 + 解析] ─┤
                ├── REST_API   ──▶ [JSON 映射]  ──┤
                ├── SPARQL     ──▶ [Wikidata Q]  ─┤
                └── ARTWORK_ONLY ▶ [作品集聚合] ──┤
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
| `run_collector.py` | CLI 入口，参数解析 |
| `src/scraper.py` | `ExhibitionScraper` 编排器，策略分发表 |
| `src/database.py` | SQLite 连接 + CRUD + 唯一去重 |
| `src/llm_parser.py` | 多供应商回退链 + Pydantic 模型 |
| `src/sites/base.py` | parser 基类 + 策略枚举 |
| `src/sites/<key>.py` | 61 家机构专属解析器 |

## 🌍 支持机构（精选）

| 机构 | 城市 | 策略 | 状态 |
|:--|:--|:--|:--|
| MoMA | New York | CSV_REMOTE | ✅ |
| Tate Modern | London | HTML_LLM | ✅ |
| M+ Museum | Hong Kong | HTML_LLM | ✅ |
| Serpentine Galleries | London | HTML_LLM | ✅ |
| Mori Art Museum | Tokyo | HTML_LLM | ✅ |
| Art Institute of Chicago | Chicago | REST_API | ✅ |
| Venice Biennale | Venice | HTML_LLM | ✅ |
| Whitney Museum | New York | REST_API | ✅ |

完整 61 家列表 + 状态见 [docs/SITES.md](docs/SITES.md)（运行 `python run_collector.py --list-sites`）。

## 🔧 配置

通过环境变量注入 LLM 凭据（按优先级回退）：

| 变量 | 模型 | 优先级 |
|:--|:--|:--:|
| `XIAOMI_MIMO_API_KEY` | mimo-v2.5-pro | 1（首选） |
| `GEMINI_API_KEY` | gemini-2.5-flash | 2 |
| `SILICONFLOW_API_KEY` | DeepSeek-V3 | 3 |

可选：
- `MIMO_BASE_URL`（默认 Xiaomi Token Plan 端点）
- `GEMINI_BASE_URL`
- `SILICONFLOW_BASE_URL`

## 🧪 开发

```bash
# 运行测试
uv run pytest

# Lint
uv run ruff check src/ tests/

# 监测运行状态
python scripts/monitor_runs.py --alert

# 验证数据质量
python scripts/validate_post_scrape.py --all
```

## 📊 数据库 Schema (v2)

| 表 | 关键字段 |
|:--|:--|
| `exhibitions` | `id`, `source`, `title`, `curators` (JSON), `start_date`, `end_date`, `url` (UNIQUE) |
| `artworks` | `id`, `exhibition_id` (FK), `artist_name`, `work_title`, `work_year` |

## 📜 许可

[MIT License](LICENSE) © 2026 Auto Curation Contributors

## 🙏 致谢

- [Scrapling](https://github.com/D4Vinci/Scrapling) — 底层 Fetcher / StealthyFetcher
- [Pydantic](https://docs.pydantic.dev/) — 数据模型校验
- [auto_hub](../auto_hub) — LLM provider chain 统一封装
