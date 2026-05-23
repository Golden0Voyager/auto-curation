# Tate Collection — 数据来源说明

**原始仓库**: https://github.com/tategallery/collection  
**许可证**: CC0 (Public Domain)  
**下载时间**: 2026-05-23

> ⚠️ **注意**：该数据集自 **2014 年起停止更新**，Tate 官方已确认不再维护此 GitHub 仓库。
> 适合用于历史研究，不建议作为当前展览信息的数据来源。
> 当前展览数据请通过 `run_collector.py --site tate` 实时爬取。

## 📁 文件说明

| 文件 | 内容 | 规模 |
|:--|:--|:--|
| `artwork_data.csv` | Tate 馆藏作品元数据（截至 2014 年） | ~70,000 件 |
| `artist_data.csv` | 关联艺术家信息（含 WikidataID） | ~3,500 人 |

## 📊 数据字段（artwork_data.csv 核心字段）

| 字段 | 说明 |
|:--|:--|
| id | Tate 内部作品 ID |
| title | 作品名称 |
| artistname | 艺术家姓名 |
| medium | 媒介材质 |
| dimensions | 尺寸描述（文本格式） |
| year | 创作年份 |
| acquisitionYear | 入藏年份 |
| url | Tate 网站详情页 URL |

## 💡 适用场景

- 查询 Tate 2014 年前的馆藏作品历史记录
- 通过 WikidataID 与其他数据集进行艺术家实体对齐
- 作为 LLM 训练/分析的历史馆藏基础语料
