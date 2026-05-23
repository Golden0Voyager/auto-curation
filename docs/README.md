# Auto Curation — 文档索引

> 本目录为 auto_curation 项目的技术文档，面向开发者和数据研究者。

## 📄 文档列表

| 文件 | 内容 |
|:--|:--|
| [architecture.md](./architecture.md) | 系统架构、模块说明、数据流 |
| [data_sources.md](./data_sources.md) | 所有数据来源的接入方式、状态、字段说明 |
| [cli_reference.md](./cli_reference.md) | 命令行工具完整使用手册 |
| [europe_integration.md](./europe_integration.md) | 欧洲博物馆数据集成路线图 |

## 🚀 快速开始

```bash
# 安装依赖
uv sync

# 查看所有已注册机构
python run_collector.py --list-sites

# 采集 MoMA 1970 年以来的展览（来自本地 GitHub 数据集，无 LLM 消耗）
python run_collector.py --site moma --since 1970

# 采集 M+ 博物馆所有历史展览（含 Gemini LLM 解析）
python run_collector.py --site mplus

# 全量采集所有机构（当前展览）
python run_collector.py --all --limit 5
```
