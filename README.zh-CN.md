<div align="center">

# Auto Curation · 自动策展

**AI 驱动的全球艺术展览数据管道**

*来自 61 家世界级机构的结构化展览数据 — 自动化、可验证、开放。*

[English](README.md) · [中文](#概述)

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Golden0Voyager/auto-curation/ci.yml?branch=main&label=CI&logo=github)](.github/workflows/ci.yml)
[![coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](.github/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-475%20passed-brightgreen)](tests/)
[![mypy](https://img.shields.io/badge/mypy-0%20errors-success)](mypy.ini)
[![ruff](https://img.shields.io/badge/ruff-passing-brightgreen)](pyproject.toml)

</div>

---

## 目录

- [概述](#概述)
- [为什么选择 Auto Curation？](#为什么选择-auto-curation)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [支持机构](#支持机构)
- [安装](#安装)
- [使用方法](#使用方法)
- [配置](#配置)
- [开发](#开发)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 概述

**Auto Curation** 是一套生产级 AI ETL 管道，自动采集、提取并结构化来自全球 61 家顶级艺术机构的展览数据——覆盖 MoMA、泰特现代美术馆、古根海姆、惠特尼美术馆、威尼斯双年展等。

系统通过 **GitHub Actions 每日运行**，采用具备多供应商回退的 **多策略 LLM 提取引擎**，并严格执行**零合成数据治理**：每个字段必须来自真实数据源，否则留空。

本项目为研究人员、数字人文开发者和 AI 辅助文化分析平台提供大规模结构化全球艺术展览数据——这类数据此前几乎无法在规模上获取。

---

## 为什么选择 Auto Curation？

| 问题 | Auto Curation 的解决方案 |
|------|--------------------------|
| 61 个不同网站，格式参差不齐 | 统一 Schema + 6 种自适应采集策略 |
| LLM 提取不稳定，无回退机制 | 多供应商链：MIMO → Gemini → SiliconFlow |
| 抓取数据常含合成内容或幻觉 | 硬性治理：零合成字段，缺失留空 |
| 手动维护 61 家机构无法扩展 | 自动注册 Parser，新增机构只需新建文件 |
| 数据质量悄然降级 | 每日健康检查 + GitHub Actions 告警 |

---

## 核心特性

- **6 种采集策略** — `HTML_LLM` / `CSV_LOCAL` / `CSV_REMOTE` / `REST_API` / `SPARQL` / `ARTWORK_ONLY`，按机构特性自动路由
- **61 家注册机构** — 覆盖 MoMA、泰特、M+、惠特尼、古根海姆、威尼斯双年展，横跨四大洲
- **多供应商 LLM 回退** — MIMO v2.5-pro → Gemini 2.5 Flash → DeepSeek-V3，Pydantic 强校验输出
- **自动注册 Parser** — 基于 `pkgutil` 扫描 `src/sites/__init__.py`，无需手动导入
- **质量监控** — 每日健康检查 + 采集后数据验证 + GitHub Actions 告警（UTC 08:03）
- **零合成数据** — 所有字段来源真实数据；缺失留 null，从不模板填充
- **475 个测试，95% 覆盖率** — mypy 零错误，ruff 通过，生产级代码库

---

## 系统架构

```
[URL 发现 / CSV 读取 / API 分页]
         │
         ▼
 [策略分发表] ── HTML_LLM ──▶ [HTML 清洗] ──▶ [LLM 提取] ──▶ Pydantic 校验
               │                              │
               ├── CSV_LOCAL  ──▶ [Python 聚合] ──┤
               ├── CSV_REMOTE ──▶ [下载 + 解析] ─┤
               ├── REST_API   ──▶ [JSON 映射]   ──┤
               ├── SPARQL     ──▶ [Wikidata 查询]─┤
               └── ARTWORK_ONLY ▶ [作品集聚合]  ──┤
                                                  │
                                                  ▼
                                      [去重检查 — url UNIQUE]
                                                  │
                                                  ▼
                                           [exhibitions.db]
```

### 核心模块

| 文件 | 职责 |
|:-----|:-----|
| `run_collector.py` | CLI 入口，参数解析 |
| `src/scraper.py` | `ExhibitionScraper` 编排器，策略分发 |
| `src/database.py` | SQLite 连接 + CRUD + 唯一去重 |
| `src/llm_parser.py` | 多供应商回退链 + Pydantic 模型 |
| `src/sites/base.py` | Parser 基类 + 策略枚举 |
| `src/sites/<key>.py` | 61 家机构专属解析器 |

---

## 支持机构

<details>
<summary>查看全部 61 家机构</summary>

| 机构 | 城市 | 国家 | 策略 |
|:-----|:-----|:-----|:-----|
| MoMA 现代艺术博物馆 | 纽约 | 🇺🇸 美国 | CSV_REMOTE |
| 泰特现代美术馆 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| M+ 博物馆 | 香港 | 🇭🇰 香港 | HTML_LLM |
| 蛇形画廊 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| 森美术馆 | 东京 | 🇯🇵 日本 | HTML_LLM |
| 芝加哥艺术博物馆 | 芝加哥 | 🇺🇸 美国 | REST_API |
| 威尼斯双年展 | 威尼斯 | 🇮🇹 意大利 | HTML_LLM |
| 惠特尼美术馆 | 纽约 | 🇺🇸 美国 | REST_API |
| 古根海姆博物馆 | 纽约 | 🇺🇸 美国 | HTML_LLM |
| 巴比肯艺术中心 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| 蓬皮杜中心 | 巴黎 | 🇫🇷 法国 | HTML_LLM |
| 东京宫 | 巴黎 | 🇫🇷 法国 | HTML_LLM |
| 索菲亚王后国家艺术中心博物馆 | 马德里 | 🇪🇸 西班牙 | HTML_LLM |
| MAXXI 国立二十一世纪艺术博物馆 | 罗马 | 🇮🇹 意大利 | HTML_LLM |
| 汉堡火车站现代艺术博物馆 | 柏林 | 🇩🇪 德国 | HTML_LLM |
| ZKM 艺术与媒体中心 | 卡尔斯鲁厄 | 🇩🇪 德国 | HTML_LLM |
| 苏黎世美术馆 | 苏黎世 | 🇨🇭 瑞士 | HTML_LLM |
| 路易威登基金会 | 巴黎 | 🇫🇷 法国 | HTML_LLM |
| 路易斯安那现代艺术博物馆 | 胡姆勒拜克 | 🇩🇰 丹麦 | HTML_LLM |
| 澳大利亚国家美术馆 | 堪培拉 | 🇦🇺 澳大利亚 | HTML_LLM |
| 维多利亚国家美术馆 | 墨尔本 | 🇦🇺 澳大利亚 | HTML_LLM |
| 澳大利亚当代艺术博物馆 | 悉尼 | 🇦🇺 澳大利亚 | HTML_LLM |
| 新加坡国家美术馆 | 新加坡 | 🇸🇬 新加坡 | HTML_LLM |
| MAIIAM 当代艺术博物馆 | 清迈 | 🇹🇭 泰国 | HTML_LLM |
| UCCA 尤伦斯当代艺术中心 | 北京 | 🇨🇳 中国 | HTML_LLM |
| 三星美术馆 Leeum | 首尔 | 🇰🇷 韩国 | HTML_LLM |
| 金泽 21 世纪美术馆 | 金泽 | 🇯🇵 日本 | HTML_LLM |
| 东京国立近代美术馆 | 东京 | 🇯🇵 日本 | HTML_LLM |
| 悉尼双年展 | 悉尼 | 🇦🇺 澳大利亚 | HTML_LLM |
| 台北双年展 | 台北 | 🇹🇼 台湾 | HTML_LLM |
| 圣保罗双年展 | 圣保罗 | 🇧🇷 巴西 | HTML_LLM |
| 柏林双年展 | 柏林 | 🇩🇪 德国 | HTML_LLM |
| 利物浦双年展 | 利物浦 | 🇬🇧 英国 | HTML_LLM |
| 沙迦双年展 | 沙迦 | 🇦🇪 阿联酋 | HTML_LLM |
| 横滨三年展 | 横滨 | 🇯🇵 日本 | HTML_LLM |
| 文献展 Documenta | 卡塞尔 | 🇩🇪 德国 | HTML_LLM |
| 赫希洪博物馆 | 华盛顿特区 | 🇺🇸 美国 | REST_API |
| 洛杉矶郡艺术博物馆 | 洛杉矶 | 🇺🇸 美国 | HTML_LLM |
| 布鲁克林博物馆 | 纽约 | 🇺🇸 美国 | HTML_LLM |
| 新美术馆 | 纽约 | 🇺🇸 美国 | HTML_LLM |
| 锤头博物馆 | 洛杉矶 | 🇺🇸 美国 | HTML_LLM |
| 芝加哥当代艺术博物馆 | 芝加哥 | 🇺🇸 美国 | HTML_LLM |
| Mass MoCA | 北亚当斯 | 🇺🇸 美国 | HTML_LLM |
| DIA 艺术基金会 | 纽约 | 🇺🇸 美国 | HTML_LLM |
| 白教堂画廊 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| 海沃德画廊 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| 南伦敦画廊 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| BALTIC 当代艺术中心 | 盖茨黑德 | 🇬🇧 英国 | HTML_LLM |
| 维多利亚与艾伯特博物馆 | 伦敦 | 🇬🇧 英国 | HTML_LLM |
| 上海当代艺术博物馆 | 上海 | 🇨🇳 中国 | HTML_LLM |
| 阿斯特鲁普·费尔纳利现代艺术博物馆 | 奥斯陆 | 🇳🇴 挪威 | HTML_LLM |
| 贝耶勒基金会 | 巴塞尔 | 🇨🇭 瑞士 | HTML_LLM |
| 慕尼黑现代艺术陈列馆 | 慕尼黑 | 🇩🇪 德国 | HTML_LLM |
| 路德维希博物馆 | 科隆 | 🇩🇪 德国 | HTML_LLM |
| 伦巴赫之家 | 慕尼黑 | 🇩🇪 德国 | HTML_LLM |
| KW 当代艺术学院 | 柏林 | 🇩🇪 德国 | HTML_LLM |
| 鹿特丹美术馆 | 鹿特丹 | 🇳🇱 荷兰 | HTML_LLM |
| 惠特尼双年展 | 纽约 | 🇺🇸 美国 | HTML_LLM |
| 新泽西表演艺术中心 | 纽瓦克 | 🇺🇸 美国 | HTML_LLM |
| 大都会艺术博物馆 | 纽约 | 🇺🇸 美国 | REST_API |

*运行时查看完整状态：`python run_collector.py --list-sites`*

</details>

---

## 安装

需要 Python ≥ 3.12 与 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/Golden0Voyager/auto-curation.git
cd auto-curation
uv pip install -r requirements.txt
```

---

## 使用方法

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

数据落地到本地 `exhibitions.db`（SQLite，已在 `.gitignore`）。

---

## 配置

通过环境变量注入 LLM 凭据（按优先级回退）：

| 变量 | 模型 | 优先级 |
|:-----|:-----|:------:|
| `XIAOMI_MIMO_API_KEY` | mimo-v2.5-pro | 1（首选）|
| `GEMINI_API_KEY` | gemini-2.5-flash | 2 |
| `SILICONFLOW_API_KEY` | DeepSeek-V3 | 3 |

可选覆盖：
- `MIMO_BASE_URL`
- `GEMINI_BASE_URL`
- `SILICONFLOW_BASE_URL`

---

## 数据库 Schema

| 表 | 关键字段 |
|:---|:---------|
| `exhibitions` | `id`, `source`, `title`, `curators`（JSON）, `start_date`, `end_date`, `url`（UNIQUE）|
| `artworks` | `id`, `exhibition_id`（FK）, `artist_name`, `work_title`, `work_year` |

---

## 开发

```bash
# 运行测试
uv run pytest

# Lint 检查
uv run ruff check src/ tests/

# 类型检查
uv run mypy src/

# 监测运行状态
python scripts/monitor_runs.py --alert

# 验证数据质量
python scripts/validate_post_scrape.py --all
```

---

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

**5 步接入新机构：**

1. 在 `src/sites/<key>.py` 下新建解析器，继承 `BaseSiteParser`
2. 设置必需类属性：`source`、`city`、`parser_key`、`list_url`
3. 声明 `strategy = ParserStrategy.XXX`
4. Parser **自动注册**——无需手动导入
5. 添加测试，发起 PR

**数据质量原则 — 零合成数据：**
所有字段必须来源于真实数据。缺失值必须留空——绝不用模板或 LLM 猜测填充。

---

## 许可证

[Apache-2.0 License](LICENSE) © 2026 Haining Yu (Golden0Voyager)

---

## 致谢

- [Scrapling](https://github.com/D4Vinci/Scrapling) — 底层 Fetcher / StealthyFetcher
- [Pydantic](https://docs.pydantic.dev/) — 数据模型校验
- [auto_hub](https://github.com/Golden0Voyager/auto-hub) — 共享 LLM provider 链
