# 全球美术馆数字化资源清单

> 本清单记录全球各大艺术机构的开放数据资源，涵盖 GitHub 数据集、REST API、数据转储等形式。
> 用于 auto_curation 项目的数据采集与扩展参考。
>
> **最后更新**: 2026-05-23  
> **维护方式**: 发现新资源时在对应分类下添加记录，并更新 `本地状态` 列。

---

## 📦 已下载到本地的数据集

| 机构 | 本地路径 | 文件 | 规模 | 许可证 | 说明 |
|:--|:--|:--|:--|:--|:--|
| **MoMA** | `data/moma_github/` | `MoMAExhibitions1929to1989.csv` | 10MB / 1,727 个展览 / 34,558 行 | CC0 | **展览历史**，每行=一位参展者，含 WikidataID |
| **MoMA** | `data/moma_github/` | `MoMADirectorsDepartmentHeads.csv` | 12KB | CC0 | 历任馆长名录 |
| **MoMA** | `data/moma_collection/` | `Artworks.csv` | 70MB / 160,435 件 | CC0 | **馆藏作品**，含 medium / dimensions / ThumbnailURL |
| **MoMA** | `data/moma_collection/` | `Artists.csv` | 1MB / ~15,000 人 | CC0 | 艺术家信息，含 WikidataID / ULANID |
| **The Met** | `data/met_collection/` | `MetObjects.csv` | **303MB** / 470,000+ 件 | CC0 | 大都会全馆藏，**唯一可用来源**（网站 403 封锁） ✅ 下载完成 |
| **Tate** | `data/tate_collection/` | `artwork_data.csv` | 23MB / 69,201 件 | CC0 | ⚠️ 数据截至 2014 年，已停止维护 |
| **Tate** | `data/tate_collection/` | `artist_data.csv` | 471KB / ~3,500 人 | CC0 | ⚠️ 数据截至 2014 年 |

---

## 🌐 有 GitHub 仓库的机构（可下载 CSV/JSON）

| 机构 | 城市 | GitHub 仓库 | 数据规模 | 许可证 | 格式 | 本地状态 |
|:--|:--|:--|:--|:--|:--|:--|
| **MoMA** | New York | [MuseumofModernArt/exhibitions](https://github.com/MuseumofModernArt/exhibitions) | 1,727 展览 | CC0 | CSV | ✅ 已下载 |
| **MoMA** | New York | [MuseumofModernArt/collection](https://github.com/MuseumofModernArt/collection) | 160,435 件 | CC0 | CSV | ✅ 已下载 |
| **The Met** | New York | [metmuseum/openaccess](https://github.com/metmuseum/openaccess) | 470,000+ 件 | CC0 | CSV | ✅ 已下载 |
| **Tate** | London | [tategallery/collection](https://github.com/tategallery/collection) | 69,201 件 | CC0 | CSV / JSON | ✅ 已下载（⚠️ 2014 停更）|
| **National Gallery of Art** | Washington D.C. | [NationalGalleryOfArt/opendata](https://github.com/NationalGalleryOfArt/opendata) | 130,000+ 件 | CC0 | CSV | ⬜ 待下载 |
| **Cooper Hewitt** | New York | [cooperhewitt/collection](https://github.com/cooperhewitt/collection) | ~200,000 件 | CC0 | JSON | ⬜ 待下载 |
| **Cleveland Museum of Art** | Cleveland | [ClevelandMuseumArt/openaccess](https://github.com/ClevelandMuseumArt/openaccess) | 64,000+ 件 | CC0 | CSV / JSON | ⬜ 待下载 |
| **Whitney Museum** | New York | [whitneymuseum/collection](https://github.com/whitneymuseum/collection) | — | CC0 | CSV | ⬜ 待下载 |
| **Carnegie Museum of Art** | Pittsburgh | [cmoa/collection](https://github.com/cmoa/collection) | — | CC0 | CSV / JSON | ⬜ 待下载 |
| **Williams College Museum** | Williamstown | [WilliamsCollegeMuseumofArt/collection](https://github.com/WilliamsCollegeMuseumofArt/collection) | — | CC0 | CSV | ⬜ 待下载 |

---

## 🔌 有 REST API 的机构（无 GitHub 直接下载，需调用）

| 机构 | 城市 | API 文档 | 数据规模 | 密钥要求 | 许可证 | 备注 |
|:--|:--|:--|:--|:--|:--|:--|
| **Rijksmuseum** | Amsterdam | [data.rijksmuseum.nl](https://data.rijksmuseum.nl/) | 800,000+ 件 | ✅ 需申请 API Key | CC0 | 提供图片高清下载；荷兰黄金时代强项 |
| **Harvard Art Museums** | Cambridge | [api.harvardartmuseums.org](https://api.harvardartmuseums.org) | 220,000+ 件 + 展览记录 | ✅ 需申请 API Key | 非商业 | 有展览(exhibitions)端点，是稀缺资源 |
| **Art Institute of Chicago** | Chicago | [api.artic.edu](https://api.artic.edu/docs/) | 120,000+ 件 | ❌ 无需密钥 | CC0 | 无需注册，可直接调用，文档完善 |
| **Victoria & Albert Museum** | London | [api.vam.ac.uk](https://api.vam.ac.uk/) | 800,000+ 件 | ❌ 无需密钥 | CC0 | 支持 CSV 导出，有 Jupyter 示例 |
| **Smithsonian Institution** | Washington D.C. | [api.si.edu](https://api.si.edu/) | 1,100 万+ 件 | ✅ 需申请 API Key | CC0 | 覆盖 19 个博物馆，规模最大 |
| **The Met** | New York | [metmuseum.github.io/openaccess/api](https://metmuseum.github.io/openaccess/api) | 470,000+ 件 | ❌ 无需密钥 | CC0 | 与 CSV 数据集同源，可实时查询图片 |

---

## 📡 有数据转储但需特殊处理的机构

| 机构 | 城市 | 获取方式 | 说明 |
|:--|:--|:--|:--|
| **Rijksmuseum** | Amsterdam | [OAI-PMH + 数据下载](https://data.rijksmuseum.nl/object-metadata/download/) | 提供完整 XML 转储，需解析 |
| **Smithsonian** | Washington D.C. | [AWS S3 Open Data](https://registry.opendata.aws/smithsonian-open-access/) | 11M 条记录，Line-delimited JSON 格式，分机构压缩包下载 |
| **Europeana** | 欧洲联合 | [data.europeana.eu](https://data.europeana.eu/) | 聚合欧洲各大博物馆，SPARQL 端点 + 数据转储 |
| **Wikidata** | 全球联合 | [query.wikidata.org](https://query.wikidata.org/) (SPARQL) | 聚合全球艺术家/作品实体，可与本地数据库对齐 |

---

## 🚫 暂无开放数据的机构

| 机构 | 城市 | 原因 | 当前采集方式 |
|:--|:--|:--|:--|
| **Centre Pompidou** | Paris | 无公开数据集，网站 JS 渲染 | 爬虫（有限） |
| **Palais de Tokyo** | Paris | 无公开数据 | 爬虫 |
| **Venice Biennale** | Venice | 无公开数据集 | 爬虫 |
| **Guggenheim** | New York | 网站 403 封锁爬虫 | ❌ 暂无可用方式 |
| **Mori Art Museum** | Tokyo | 无公开数据集 | 爬虫（含历史分页） |
| **Serpentine Galleries** | London | 无公开数据集 | 爬虫（含 archive 142 页） |
| **M+ Museum** | Hong Kong | 无公开数据集 | 爬虫（含 status=past 历史） |

---

## 🗺️ 数据覆盖图谱

```
当代艺术重点覆盖:
  MoMA       ████████████ 160K件藏品 + 1727展览历史（1929-1989）
  The Met    ████████████████████ 470K件（当代艺术部门约4K件）
  Tate       ████ 69K件（2014停更）
  Cleveland  ███ 64K件（待引入）
  Harvard    ███ 220K件（含展览API，待引入）

可爬取的展览历史:
  Serpentine ████████████ archive 142页（~1000+个展览）
  M+         ████ 38个历史展览
  Mori       ████ past 多页
  Tate       ████ 按年份过滤（JS渲染，有限）
```

---

## 📋 待办事项

- [ ] 下载 National Gallery of Art CSV（130K件，CC0）
- [ ] 接入 Art Institute of Chicago API（无需密钥，直接可用）
- [ ] 申请 Harvard Art Museums API Key（有展览记录，罕见）
- [ ] 申请 Rijksmuseum API Key（800K件 + 图片）
- [ ] 探索 Cooper Hewitt JSON 格式导入
- [ ] 为 Met 馆藏建立本地解析器（利用 `data/met_collection/MetObjects.csv`）
- [ ] 为 MoMA collection 建立 exhibition↔artwork 关联查询
