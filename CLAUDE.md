# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Auto Curation 已从最初的策展概念文档演化为一个**模块化当代艺术展览数据采集与结构化存储系统**。它从全球 10 家顶级艺术机构抓取展览数据，通过三种策略转化为结构化数据，存入 SQLite 数据库。

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

### 三种采集策略

`ExhibitionScraper`（`src/scraper.py`）根据 parser 类型自动路由到对应策略：

| 策略 | 触发条件 | 适用机构 | 说明 |
|:--|:--|:--|:--|
| **HTML 爬取 + LLM** | `BaseSiteParser` 子类 | Tate, M+, Serpentine, Mori 等 | 爬取官网，HTML 清洗后送 Gemini 结构化提取 |
| **CSV 本地解析** | `MoMAParser` / `NGAParser` | MoMA, NGA, The Met | 读取本地 GitHub 开放数据集，零 LLM 消耗 |
| **REST API** | `AICParser` | Art Institute of Chicago | 直接拉取 JSON，无需密钥 |

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
| `src/scraper.py` | `ExhibitionScraper` 编排器，路由三种策略，管理 httpx 客户端 |
| `src/database.py` | `ExhibitionDatabase`，SQLite 连接与 CRUD，`url` 字段为唯一去重键 |
| `src/llm_parser.py` | `LLMExhibitionParser`，调用 Gemini/SiliconFlow API，Pydantic 模型校验输出 |
| `src/sites/base.py` | `BaseSiteParser` 基类，封装列表页抓取、URL 发现、HTML 清洗 |
| `src/sites/__init__.py` | `SITES` 字典，注册全部 10 个机构的 parser 实例 |
| `src/sites/<key>.py` | 各机构专属解析器（见下表） |

### 机构与策略对照

| Key | 机构 | 策略 | 历史数据支持 |
|:--|:--|:--|:--|
| `moma` | MoMA | 本地 CSV | 1929–1989 全量（GitHub 开放数据集） |
| `tate` | Tate Modern | HTML + 年份 URL | 按年生成列表页 URL，`--since` 生效 |
| `mplus` | M+ Museum | HTML | `?status=past` 历史档案 |
| `serpentine` | Serpentine Galleries | HTML + 分页 archive | 默认 15 页历史，最多 142 页 |
| `mori` | Mori Art Museum | HTML + past 分页 | 5 页历史 |
| `aic` | Art Institute of Chicago | REST API | 6,253 个展览 |
| `nga` | National Gallery of Art | 本地 CSV (多表 join) | 145,655 件 |
| `met` | The Met | HTML（403 封锁）| 用本地 CSV 替代 |
| `pompidou` | Centre Pompidou | HTML | 仅当前，JS 渲染限制 |
| `palais_tokyo` | Palais de Tokyo | HTML | 仅当前 |
| `biennale` | Venice Biennale | HTML | 仅当前 |
| `guggenheim` | Guggenheim | HTML（403 封锁）| 暂无 |

---

## 数据库 Schema

SQLite，两张核心表：

- **`exhibitions`**：`id`, `source`, `title`, `preface`, `concept`, `curators` (JSON), `start_date`, `end_date`, `location`, `city`, `url` (UNIQUE), `scraped_at`
- **`artworks`**：`id`, `exhibition_id` (FK), `artist_name`, `work_title`, `work_year`, `medium`, `dimensions`, `caption`

---

## 环境变量

| 变量 | 说明 |
|:--|:--|
| `GEMINI_API_KEY` | 首选 LLM API 密钥（HTML 爬取模式必需） |
| `GEMINI_BASE_URL` | 可选，默认 `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `SILICONFLOW_API_KEY` | 备用密钥（Gemini 不可用时回退） |
| `SILICONFLOW_BASE_URL` | 可选，默认 `https://api.siliconflow.cn/v1` |

---

## 新增机构接入

1. 在 `src/sites/` 下新建解析器文件（继承 `BaseSiteParser` 或独立实现 CSV/API 逻辑）
2. 在 `src/sites/__init__.py` 中导入并注册到 `SITES` 字典
3. 在 `run_collector.py` 的 `list_registered_sites()` 中更新历史支持状态提示（如有必要）

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
- 依赖：`httpx`, `beautifulsoup4`, `pydantic`
- 包管理器：`uv`
