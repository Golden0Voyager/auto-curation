# MoMA Collection — 馆藏作品数据集

**原始仓库**: https://github.com/MuseumofModernArt/collection  
**许可证**: CC0 (Public Domain)  
**下载时间**: 2026-05-23  
**数据规模**: 130,000+ 件馆藏作品

> 📌 **与 MoMA Exhibitions 数据集的区别**
> - `data/moma_github/`（exhibitions）：记录**展览历史**（哪位艺术家参加了哪个展览）
> - `data/moma_collection/`（本目录）：记录**馆藏作品**（具体作品的媒介、尺寸、图片链接等）
> - 两者可通过 `ConstituentID` ↔ `Artist ID` 字段关联

## 📁 文件说明

| 文件 | 大小 | 内容 |
|:--|:--|:--|
| `Artworks.csv` | ~69MB | 130,000+ 件馆藏作品元数据（含媒介、尺寸、图片 URL） |
| `Artists.csv` | ~5MB | 关联艺术家信息（含 WikidataID、ULANID） |

## 📊 核心字段（Artworks.csv）

| 字段 | 说明 |
|:--|:--|
| Title | 作品名称 |
| Artist | 艺术家姓名（可多人，逗号分隔） |
| ConstituentID | 艺术家 ID（可关联 Artists.csv 和 exhibitions 数据集） |
| Date | 创作年份（文本） |
| Medium | **媒介材质**（如 "Oil on canvas"） |
| Dimensions | **尺寸描述**（如 "33.5 x 24.9 cm"） |
| Department | 所属部门 |
| URL | MoMA 官网详情页 URL |
| ThumbnailURL | 缩略图 URL（部分有效） |
| Nationality | 艺术家国籍 |
| BeginDate / EndDate | 艺术家生卒年 |
| WikidataID / ULANID | 权威控制 ID |

## 关联 exhibitions 数据集

两个数据集通过 ConstituentID 可以关联，例如查询 Mark Rothko 的所有馆藏作品：

```python
import pandas as pd
exhibitions = pd.read_csv("data/moma_github/MoMAExhibitions1929to1989.csv", encoding="latin-1")
artworks = pd.read_csv("data/moma_collection/Artworks.csv", encoding="utf-8", low_memory=False)

artist_ids = exhibitions[exhibitions["DisplayName"] == "Mark Rothko"]["ConstituentID"].unique()
rothko_works = artworks[artworks["ConstituentID"].astype(str).isin(artist_ids.astype(str))]
```
