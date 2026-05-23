# 系统架构

## 总览

Auto Curation 是一个模块化的当代艺术展览数据采集与结构化存储系统。系统将来自全球顶级艺术机构的展览信息，通过三种采集策略转化为结构化数据，存入 SQLite 数据库。

```
┌─────────────────────────────────────────────────────────┐
│                    run_collector.py                      │
│                  CLI 命令行入口                           │
│   --site / --all / --since YEAR / --limit / --dry-run   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   src/scraper.py                         │
│              ExhibitionScraper 编排器                     │
│   路由到三种策略：HTML爬取 / CSV解析 / REST API          │
└──────┬───────────────────┬──────────────────┬───────────┘
       │                   │                  │
       ▼                   ▼                  ▼
┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
│  HTML 爬取   │   │  CSV 本地解析 │   │   REST API 拉取   │
│             │   │              │   │                  │
│ Tate        │   │ MoMA (exh.)  │   │ AIC (芝加哥艺术)  │
│ M+          │   │ MoMA (coll.) │   │（6,253个展览）    │
│ Serpentine  │   │ The Met      │   │                  │
│ Mori        │   │ NGA          │   │                  │
│ Pompidou    │   │ Tate (hist.) │   │                  │
│ Palais Tokyo│   │              │   │                  │
│ Biennale    │   │              │   │                  │
│ Guggenheim  │   │              │   │                  │
└──────┬──────┘   └──────┬───────┘   └────────┬─────────┘
       │                 │                    │
       ▼                 │                    │
┌─────────────┐          │                    │
│src/llm_     │          │                    │
│parser.py    │          │                    │
│Gemini 2.5   │          │                    │
│Flash 结构化  │          │                    │
│提取          │          │                    │
└──────┬──────┘          │                    │
       │                 │                    │
       └────────────┬────┘────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  src/database.py                         │
│              ExhibitionDatabase (SQLite)                 │
│                                                          │
│  exhibitions 表          artworks 表                      │
│  ─────────────           ──────────────                  │
│  id                      id                              │
│  source                  exhibition_id (FK)              │
│  title                   artist_name                     │
│  preface                 work_title                      │
│  concept                 work_year                       │
│  curators (JSON)         medium                          │
│  start_date              dimensions                      │
│  end_date                caption                         │
│  location                created_at                      │
│  city                                                    │
│  url (UNIQUE)                                            │
│  created_at                                              │
└─────────────────────────────────────────────────────────┘
```

---

## 模块说明

### `run_collector.py` — CLI 入口

命令行主程序，解析参数并调用 `ExhibitionScraper`。

**关键参数：**
- `--site <key>` / `--all`：指定采集目标
- `--since YEAR`：时间范围过滤（1900–今）
- `--limit N`：每站最多处理 N 条
- `--force`：跳过去重，强制重新抓取
- `--dry-run`：模拟运行，不写入数据库

---

### `src/scraper.py` — 编排器

`ExhibitionScraper` 根据 parser 类型自动路由到对应策略：

| 策略 | 触发条件 | 适用机构 |
|:--|:--|:--|
| **HTML 爬取 + LLM** | `BaseSiteParser` 子类 | Tate, M+, Serpentine, Mori 等 |
| **CSV 本地解析** | `MoMAParser` / `NGAParser` | MoMA, NGA, The Met |
| **REST API** | `AICParser` | Art Institute of Chicago |

---

### `src/sites/` — 站点解析器

每个机构一个文件，继承自 `BaseSiteParser`（HTML爬取）或独立实现（CSV/API）。

| 文件 | 机构 | 策略 | 历史数据支持 |
|:--|:--|:--|:--|
| `base.py` | — | 基类 | 多 URL + since_year |
| `moma.py` | MoMA | 本地 CSV | ✅ 1929–1989 全量 |
| `tate.py` | Tate Modern | HTML + 年份 URL | ✅ 按年生成 URL |
| `mplus.py` | M+ Museum | HTML | ✅ status=past |
| `serpentine.py` | Serpentine | HTML + 分页 archive | ✅ 最多 142 页 |
| `mori.py` | Mori Art Museum | HTML + past 分页 | ✅ 5 页历史 |
| `aic.py` | Art Institute of Chicago | REST API | ✅ 6,253 个展览 |
| `nga.py` | National Gallery of Art | 本地 CSV (多表 join) | ✅ 145,655 件 |
| `met.py` | The Met | HTML（403 封锁）| ⚠️ 用 CSV 替代 |
| `pompidou.py` | Centre Pompidou | HTML | ❌ JS 渲染限制 |
| `palais_tokyo.py` | Palais de Tokyo | HTML | ❌ 仅当前 |
| `biennale.py` | Venice Biennale | HTML | ❌ 仅当前 |
| `guggenheim.py` | Guggenheim | HTML（403 封锁）| ❌ 暂无 |

---

### `src/llm_parser.py` — LLM 结构化解析

调用 `gemini-2.5-flash` 将展览页面的自然语言文本转化为结构化 JSON。

**输入：** 清洗后的 HTML 文本（去除 nav/footer/script）  
**输出：** 符合 Pydantic 模型的展览结构体，含：
- 展览标题、前言、策展理念
- 策展人列表
- 开闭幕日期、地点、城市
- 作品列表（艺术家、作品名、媒介、尺寸、caption）

**成本控制：** CSV/API 模式下不调用 LLM，仅 HTML 爬取时调用。

---

### `src/database.py` — 数据持久化

SQLite 数据库，两张核心表：

```sql
-- 展览主表
CREATE TABLE exhibitions (
    id          INTEGER PRIMARY KEY,
    source      TEXT,           -- 机构名称
    title       TEXT,           -- 展览标题
    preface     TEXT,           -- 展览前言/简介
    concept     TEXT,           -- 策展理念
    curators    TEXT,           -- 策展人（JSON 数组）
    start_date  TEXT,           -- 开幕日期
    end_date    TEXT,           -- 闭幕日期
    location    TEXT,           -- 具体场馆
    city        TEXT,           -- 城市
    url         TEXT UNIQUE,    -- 展览页 URL（去重键）
    created_at  TIMESTAMP
);

-- 作品/艺术家表
CREATE TABLE artworks (
    id            INTEGER PRIMARY KEY,
    exhibition_id INTEGER REFERENCES exhibitions(id),
    artist_name   TEXT,         -- 艺术家姓名
    work_title    TEXT,         -- 作品名称
    work_year     TEXT,         -- 创作年份
    medium        TEXT,         -- 媒介材质
    dimensions    TEXT,         -- 尺寸
    caption       TEXT,         -- 完整 caption（含国籍、生卒年）
    created_at    TIMESTAMP
);
```

---

## 数据流示意

```
网络/本地文件
     │
     ▼
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
              [去重检查 url UNIQUE]
                        │
                        ▼
                [exhibitions.db]
```
