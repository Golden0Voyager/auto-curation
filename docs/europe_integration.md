# 欧洲博物馆数据集成路线图

## 背景

当前 auto_curation 的数据来源以**北美机构**为主（MoMA、The Met、NGA、AIC），这与全球当代艺术生态的实际格局不匹配——欧洲拥有威尼斯双年展、卡塞尔文献展、蓬皮杜、泰特、里约热内卢等极具话语权的机构和展览体系。

本路线图规划欧洲及全球其他地区数据的分阶段集成方案。

---

## 为什么欧洲开放数据较少？

详见对话记录，核心原因：

1. **资金结构**：欧洲博物馆多为国家文化机构，有稳定政府拨款，开放数据动力弱
2. **版权体系**：EU 版权法中的「道德权（Moral Rights）」和「数据库权」阻碍 CC0 授权
3. **路径差异**：欧洲机构偏向建自己的门户（卢浮宫、普拉多），而非推送到 GitHub
4. **语言壁垒**：机构内部系统和文档多为各国语言，国际化接口开发滞后

---

## 分阶段集成计划

### 阶段一：无需密钥，立即可用 🟢

#### V&A Museum（维多利亚与阿尔伯特博物馆，伦敦）

- **数据量**：800,000+ 件藏品
- **API**：`https://api.vam.ac.uk/v2/`
- **密钥**：❌ 无需
- **许可证**：CC0
- **特色**：设计、时尚、装饰艺术强项；支持 CSV 导出

**核心端点：**
```
GET https://api.vam.ac.uk/v2/objects/search?q=contemporary&cluster_role=production
GET https://api.vam.ac.uk/v2/exhibitions
```

**集成方案：**
```python
# src/sites/vam.py — VAMParser
class VAMParser:
    source = "Victoria and Albert Museum"
    city = "London"
    api_base = "https://api.vam.ac.uk/v2"

    def get_api_exhibitions(self, since_year=None, limit=None):
        # 分页拉取展览，字段映射到 exhibitions 表
        ...
```

**预计工期：** 1 天

---

#### Europeana（欧洲数字图书馆聚合平台）

- **数据量**：50,000,000+ 件（覆盖欧洲 3,000+ 机构）
- **API**：`https://api.europeana.eu/`
- **密钥**：❌ SPARQL 端点无需；REST API 需免费注册
- **SPARQL 端点**：`https://sparql.europeana.eu/`

**价值**：一次查询可覆盖卢浮宫、普拉多、Stedelijk、柏林国家博物馆等难以直接爬取的机构数据。

**SPARQL 示例查询：**
```sparql
PREFIX edm: <http://www.europeana.eu/schemas/edm/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?title ?creator ?date ?medium WHERE {
  ?object dc:title ?title ;
          dc:creator ?creator ;
          dc:date ?date .
  OPTIONAL { ?object dc:format ?medium }
  FILTER(CONTAINS(STR(?creator), "contemporary"))
}
LIMIT 100
```

**集成方案：**
```python
# src/sites/europeana.py — EuropeanaParser
# 通过 SPARQL 查询特定机构 + 时间范围的展览/作品
# 支持按 dataProvider（机构）过滤：
# ?provider = "Louvre" / "Stedelijk Museum" / "Tate" 等
```

**预计工期：** 2 天

---

### 阶段二：需申请 API Key 🔴（高优先级）

#### Rijksmuseum（荷兰国家博物馆，阿姆斯特丹）

- **数据量**：800,000+ 件，含高清图片
- **API 文档**：[data.rijksmuseum.nl](https://data.rijksmuseum.nl/)
- **申请地址**：[rijksmuseum.nl/en/research/conduct-research/data/api-key](https://www.rijksmuseum.nl/en/research/conduct-research/data/api-key)
- **许可证**：CC0（公有领域作品）+ CC BY-SA（部分近现代）

**核心端点：**
```
GET https://www.rijksmuseum.nl/api/en/collection?key={KEY}&q=rembrandt&ps=100
```

**关键字段：**

| API 字段 | 映射 |
|:--|:--|
| `title` | `work_title` |
| `principalMakers[].name` | `artist_name` |
| `principalMakers[].nationality` | caption |
| `subTitle` | `medium` + `dimensions` |
| `dating.presentingDate` | `work_year` |
| `webImage.url` | 图片链接 |

**申请步骤：**
1. 访问上方链接，填写机构/研究目的表单
2. 等待邮件确认（通常 1-3 个工作日）
3. 将 Key 存入 `.env` 文件：`RIJKSMUSEUM_API_KEY=xxx`

**集成方案：**
```python
# src/sites/rijksmuseum.py
class RijksmuseumParser:
    source = "Rijksmuseum"
    city = "Amsterdam"
    api_base = "https://www.rijksmuseum.nl/api/en"
```

**预计工期：** 1 天（获得 Key 后）

---

#### Harvard Art Museums（哈佛艺术博物馆）

- **数据量**：220,000+ 件 + **展览记录**（稀缺！）
- **API 文档**：[github.com/harvardartmuseums/api-docs](https://github.com/harvardartmuseums/api-docs)
- **申请地址**：[api.harvardartmuseums.org](https://api.harvardartmuseums.org/)
- **许可证**：非商业使用

> ⭐ **特别价值**：哈佛 API 有 `/exhibitions` 端点，包含历史展览记录（参展艺术家、出版物、时间），在欧美学术机构中极为罕见。

**展览端点：**
```
GET https://api.harvardartmuseums.org/exhibition?apikey={KEY}&size=100
GET https://api.harvardartmuseums.org/exhibition/{id}?apikey={KEY}
```

**展览字段预览：**
```json
{
  "title": "Mark Rothko",
  "begindate": "1999-09-16",
  "enddate": "2000-01-16",
  "venues": [{"name": "Fogg Art Museum"}],
  "objects": [{"id": 123, "title": "No. 61 (Rust and Blue)"}]
}
```

**申请步骤：**
1. 访问 API 文档页面注册账号
2. 填写研究目的（注明 auto_curation 学术研究项目）
3. Key 通常即时生效
4. 存入 `.env`：`HARVARD_API_KEY=xxx`

**预计工期：** 1 天（获得 Key 后）

---

### 阶段三：大型数据转储（按需引入）🟡

#### Smithsonian Institution（史密森学会）

- **数据量**：11,000,000+ 件（19 个博物馆）
- **下载方式**：AWS S3 公开数据集
- **格式**：Line-delimited JSON（NDJSON），按机构分包
- **AWS 路径**：`s3://smithsonian-open-access/`

**下载相关机构数据：**
```bash
# 安装 AWS CLI（无需账号）
brew install awscli

# 列出所有机构包
aws s3 ls s3://smithsonian-open-access/metadata/edan/ --no-sign-request

# 下载 Hirshhorn（史密森当代艺术博物馆）
aws s3 sync s3://smithsonian-open-access/metadata/edan/hmsg/ \
    data/smithsonian_hmsg/ --no-sign-request
```

**相关机构：**
- `hmsg` — Hirshhorn Museum（当代艺术，最相关）
- `saam` — Smithsonian American Art Museum
- `chndm` — Cooper Hewitt 设计博物馆

---

#### Wikidata（全球艺术家实体对齐）

- **用途**：将本地数据库中的艺术家姓名与全球权威 ID 对齐
- **端点**：`https://query.wikidata.org/sparql`
- **密钥**：❌ 无需

**实体对齐示例：**
```sparql
SELECT ?artist ?artistLabel ?birthDate ?nationality WHERE {
  ?artist wdt:P106 wd:Q1028181 ;    # 职业=画家
          wdt:P569 ?birthDate ;
          wdt:P27 ?country .
  ?country rdfs:label ?nationality FILTER(LANG(?nationality)="en")
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,zh" }
}
LIMIT 100
```

**集成价值：**
- 统一 MoMA（`WikidataID`）、Tate（`WikidataID`）、NGA 等数据集的艺术家实体
- 补充艺术家完整履历（出生地、主要机构、主要展览）
- 为知识图谱构建提供基础

---

## 实施优先级

```
立即可做（无密钥）:
  ① V&A API            → 800K件，设计/时尚强项
  ② Europeana SPARQL   → 覆盖整个欧洲

申请密钥后（高价值）:
  ③ Harvard API        → 220K件 + 珍贵展览记录
  ④ Rijksmuseum API    → 800K件 + 高清图片

按需集成（大体量）:
  ⑤ Smithsonian AWS   → 史密森当代馆 HMSG
  ⑥ Wikidata SPARQL   → 艺术家实体对齐
```

---

## 新机构接入模板

接入新的 API 数据源时，在 `src/sites/` 下新建解析器：

```python
# src/sites/new_museum.py
from src.sites.base import BaseSiteParser

class NewMuseumParser:
    source = "Museum Name"
    city = "City"
    list_url = "https://api.example.com/exhibitions"

    def get_api_exhibitions(self, since_year=None, limit=None):
        """分页拉取展览，返回标准化 dict 列表"""
        exhibitions = []
        # ... API 调用逻辑
        return exhibitions
```

然后在 `src/sites/__init__.py` 中注册：
```python
from src.sites.new_museum import NewMuseumParser
SITES["new_museum"] = NewMuseumParser()
```

同时更新 [data/MUSEUM_DIGITAL_RESOURCES.md](../data/MUSEUM_DIGITAL_RESOURCES.md) 中的状态。
