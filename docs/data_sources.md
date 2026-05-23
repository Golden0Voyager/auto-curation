# 数据来源完整说明

本文档描述 auto_curation 项目中所有已接入和规划中的数据来源，包括接入方式、数据字段、本地状态和使用策略。

---

## 一、已接入数据来源

### 1.1 本地 GitHub 数据集（CSV，零 LLM 消耗）

#### MoMA 展览历史（1929–1989）

| 属性 | 值 |
|:--|:--|
| **本地路径** | `data/moma_github/MoMAExhibitions1929to1989.csv` |
| **规模** | 1,727 个展览 / 34,558 行（每行=一位参展者） |
| **许可证** | CC0 |
| **来源** | [github.com/MuseumofModernArt/exhibitions](https://github.com/MuseumofModernArt/exhibitions) |
| **Parser** | `src/sites/moma.py` → `MoMAParser` |

**关键字段：**

| CSV 字段 | 映射到 | 说明 |
|:--|:--|:--|
| `ExhibitionTitle` | `exhibitions.title` | 展览名称 |
| `ExhibitionBeginDate` | `exhibitions.start_date` | 开幕日期（MM/DD/YYYY） |
| `ExhibitionEndDate` | `exhibitions.end_date` | 闭幕日期 |
| `ExhibitionURL` | `exhibitions.url` | 去重键 |
| `DisplayName` | `artworks.artist_name` | 参展者姓名 |
| `ExhibitionRole` | — | Artist / Curator / Director |
| `Nationality` | `artworks.caption` | 国籍（拼入 caption） |
| `ConstituentBeginDate` | `artworks.caption` | 出生年 |
| `VIAFID` / `WikidataID` | — | 外部权威控制 ID |

**采集命令：**
```bash
python run_collector.py --site moma --since 1960
```

---

#### MoMA 馆藏作品

| 属性 | 值 |
|:--|:--|
| **本地路径** | `data/moma_collection/Artworks.csv` |
| **规模** | 160,435 件作品 |
| **许可证** | CC0 |
| **来源** | [github.com/MuseumofModernArt/collection](https://github.com/MuseumofModernArt/collection) |

> 与展览数据集通过 `ConstituentID` 关联，可查询特定艺术家的全部馆藏作品。

---

#### The Met 大都会博物馆（唯一可用来源）

| 属性 | 值 |
|:--|:--|
| **本地路径** | `data/met_collection/MetObjects.csv` |
| **规模** | 470,000+ 件（当代艺术部门约 4,000 件） |
| **许可证** | CC0 |
| **来源** | [github.com/metmuseum/openaccess](https://github.com/metmuseum/openaccess) |

> ⚠️ The Met 网站对爬虫返回 403，此 CSV 是唯一数据来源。

**当代艺术过滤：**
```python
# Department 字段过滤
df[df['Department'] == 'Modern and Contemporary Art']
```

---

#### NGA 美国国家美术馆

| 属性 | 值 |
|:--|:--|
| **本地路径** | `data/nga_collection/` |
| **规模** | 145,655 件（含绘画、雕塑、摄影、版画） |
| **许可证** | CC0 |
| **来源** | [github.com/NationalGalleryOfArt/opendata](https://github.com/NationalGalleryOfArt/opendata) |
| **Parser** | `src/sites/nga.py` → `NGAParser` |

**本地文件结构：**

| 文件 | 内容 |
|:--|:--|
| `objects.csv` | 作品主表（含 medium、dimensions） |
| `constituents.csv` | 艺术家信息 |
| `objects_constituents.csv` | 作品↔艺术家关联表 |
| `objects_dimensions.csv` | 尺寸详表 |

---

#### Tate 泰特美术馆（历史存档）

| 属性 | 值 |
|:--|:--|
| **本地路径** | `data/tate_collection/` |
| **规模** | 69,201 件（⚠️ 截至 2014 年，已停更） |
| **许可证** | CC0 |
| **用途** | 历史研究、WikidataID 对齐 |

---

### 1.2 REST API（实时调用，无需密钥）

#### Art Institute of Chicago (AIC)

| 属性 | 值 |
|:--|:--|
| **API 根路径** | `https://api.artic.edu/api/v1` |
| **密钥要求** | ❌ 无需 |
| **Parser** | `src/sites/aic.py` → `AICParser` |

**可用端点：**

| 端点 | 数据量 | 说明 |
|:--|:--|:--|
| `/exhibitions` | **6,253 个展览** | 含日期、描述、艺术家列表 |
| `/artworks` | 131,945 件 | 含 medium、dimensions、图片 ID |
| `/artworks/search` | — | ElasticSearch 全文搜索 |

**重要字段（exhibitions）：**

| API 字段 | 映射到 | 说明 |
|:--|:--|:--|
| `title` | `exhibitions.title` | 展览标题 |
| `description` | `exhibitions.preface` | 展览描述（HTML） |
| `aic_start_at` | `exhibitions.start_date` | ISO 8601 格式 |
| `aic_end_at` | `exhibitions.end_date` | ISO 8601 格式 |
| `artist_titles` | `artworks.artist_name` | 参展艺术家列表 |
| `artwork_titles` | `artworks.work_title` | 参展作品列表 |
| `web_url` | `exhibitions.url` | 去重键 |

---

### 1.3 网页爬取（HTML → Gemini LLM 结构化）

以下机构无开放数据集，通过爬取官网 + LLM 提取信息：

| 机构 | Key | 历史深度 | 限制 |
|:--|:--|:--|:--|
| Tate Modern | `tate` | 年份分页（--since） | JS 渲染，部分内容不完整 |
| M+ Museum | `mplus` | `?status=past`（38个） | 无 |
| Serpentine | `serpentine` | archive 分页（默认15页） | archive 共 142 页 |
| Mori Art Museum | `mori` | past 5 页 | 无 |
| Centre Pompidou | `pompidou` | 仅当前 | JS 渲染严重 |
| Palais de Tokyo | `palais_tokyo` | 仅当前 | 无 |
| Venice Biennale | `biennale` | 仅当前 | 双年展特殊结构 |
| Guggenheim | `guggenheim` | 仅当前 | 403 封锁，成功率低 |

---

## 二、规划中数据来源

详见 [europe_integration.md](./europe_integration.md)

| 机构 | 类型 | 优先级 | 预期数据量 |
|:--|:--|:--|:--|
| Rijksmuseum | REST API（需申请 Key） | 🔴 高 | 800,000+ 件 |
| Harvard Art Museums | REST API（需申请 Key） | 🔴 高 | 220,000+ 件 + **展览记录** |
| V&A Museum | REST API（无需密钥） | 🟡 中 | 800,000+ 件 |
| Europeana | SPARQL + 批量下载 | 🟡 中 | 5,000 万+ 件（跨欧洲） |
| Smithsonian | AWS S3 数据转储 | 🟢 低 | 1,100 万+ 件 |
| Cooper Hewitt | GitHub JSON | 🟢 低 | 200,000+ 件 |
| Cleveland Museum | GitHub CSV + API | 🟢 低 | 64,000+ 件 |

---

## 三、数据字段对照表

各来源字段到数据库表字段的统一映射：

| 数据来源 | 艺术家字段 | 作品标题 | 媒介 | 尺寸 | 日期 |
|:--|:--|:--|:--|:--|:--|
| MoMA exhibitions CSV | `DisplayName` | `ExhibitionTitle` | — | — | `ExhibitionBeginDate` |
| MoMA collection CSV | `Artist` | `Title` | `Medium` | `Dimensions` | `Date` |
| Met CSV | `Artist Display Name` | `Title` | `Medium` | `Dimensions` | `Object Date` |
| NGA objects.csv | constituents join | `title` | `medium` | `dimensions` | `displaydate` |
| Tate CSV | `artistname` | `title` | `medium` | `dimensions` | `year` |
| AIC API | `artist_titles[]` | `artwork_titles[]` | — | — | `aic_start_at` |
| HTML + LLM | 动态提取 | 动态提取 | 动态提取 | 动态提取 | 动态提取 |
