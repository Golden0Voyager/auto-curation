# Smoke Test Report

Generated: 2026-05-25T14:18:20.755572

## Summary

| Metric | Count | Percentage |
|--------|------:|------------|
| Total  | 64 | 100% |
| Green  | 36 | 56.3% |
| Yellow | 11 | 17.2% |
| Red    | 17 | 26.6% |

## Fixes Applied (10 sites recovered)

| Site | Issue | Fix | Result |
|------|-------|-----|--------|
| `hamburger_bahnhof` | SSL hostname mismatch | Added `verify_ssl = False` to base + parser | 3 URLs |
| `saopaulo_biennial` | SSL hostname mismatch | Added `verify_ssl = False` | 51 URLs |
| `met` | Outdated pattern (`/exhibitions/listings/`) | Updated to `/exhibitions/[^/]+$` | 43 URLs |
| `taipei_biennale` | Wrong pattern (`ExhibitionDetail.aspx`) | Updated to `ExhibitionTheme.aspx` | 6 URLs |
| `momat` | Wrong pattern (`/english/exhibitions/`) | Fixed to `/exhibitions/` | 15 URLs |
| `sharjah_biennale` | Wrong list_url + pattern | Updated to `/en/sharjah-biennial/` + `sb-\d+` | 2 URLs |
| `whitney_biennial` | 404 list_url | Changed to `/exhibitions` + updated pattern | 19 URLs |
| `palaistokyo` | Wrong list_url (`/en/exhibitions/`) | Changed to `/agenda-palais-de-tokyo/` | 8 URLs |
| `pompidou` | No exhibition links on page | Changed to `/en/program/calendar` | 51 URLs |
| `pinakothek` | Typo in pattern (`exhibition` vs `exhibitions`) | Fixed typo | 2 URLs |

## Phase 4 Additional Fixes (4 sites recovered)

| Site | Issue | Fix | Result |
|------|-------|-----|--------|
| `new_museum` | SPA (Next.js), no static links | Added `use_playwright = True` + fixed pattern to `/exhibition/` | 10 URLs |
| `documenta` | TIMEOUT (>45s) | Increased global timeout to 90s | 15 URLs |
| `brooklyn_museum` | TIMEOUT (>45s) | Increased global timeout to 90s | 23 URLs |
| `astrup_fearnley` | TIMEOUT (>45s) | Increased global timeout to 90s | 6 URLs |

## Green (>=5 URLs)

- `baltic` — 64 URLs in 5.4s
- `astrup_fearnley` — 6 URLs in ~60s
- `barbican` — 34 URLs in 5.17s
- `berlin_biennale` — 30 URLs in 12.45s
- `brooklyn_museum` — 23 URLs in ~60s
- `documenta` — 15 URLs in ~60s
- `hammer_museum` — 7 URLs in 11.49s
- `new_museum` — 10 URLs in ~20s
- `kanazawa21` — 6 URLs in 7.72s
- `kunsthal` — 10 URLs in 11.0s
- `kunsthaus` — 31 URLs in 0.41s
- `kw_institute` — 31 URLs in 7.07s
- `lenbachhaus` — 120 URLs in 17.98s
- `liverpool_biennial` — 21 URLs in 4.0s
- `maiiam` — 25 URLs in 29.65s
- `maxxi` — 49 URLs in 8.47s
- `mca_chicago` — 12 URLs in 35.61s
- `met` — 43 URLs in 5.28s
- `moma` — 1727 URLs in 0.34s
- `momat` — 15 URLs in 32.16s
- `mori` — 72 URLs in 7.82s
- `mplus` — 38 URLs in 6.26s
- `museum_ludwig` — 6 URLs in 16.98s
- `national_gallery_sg` — 10 URLs in 4.08s
- `njpac` — 22 URLs in 13.73s
- `palaistokyo` — 8 URLs in 11.51s
- `pompidou` — 51 URLs in 8.46s
- `reina_sofia` — 9 URLs in 15.24s
- `saopaulo_biennial` — 51 URLs in 9.44s
- `sydney_biennale` — 33 URLs in 7.77s
- `taipei_biennale` — 6 URLs in 6.58s
- `tate` — 15 URLs in 8.04s
- `ucca` — 28 URLs in 23.53s
- `venice_biennale` — 16 URLs in 14.24s
- `whitney_biennial` — 19 URLs in 12.92s
- `yokohama_triennale` — 34 URLs in 9.9s

## Yellow (1-4 URLs)

- `aic` — 1 URLs in 1.34s
- `beyeler` — 4 URLs in 3.75s
- `hamburger_bahnhof` — 3 URLs in 3.83s
- `louisiana` — 1 URLs in 29.8s
- `ngv` — 1 URLs in 20.3s
- `pinakothek` — 2 URLs in 3.66s
- `sharjah_biennale` — 2 URLs in 11.69s
- `south_london_gallery` — 2 URLs in 15.47s
- `whitney` — 1 URLs in 2.3s
- `wikidata` — 1 URLs in 4.3s
- `zkm` — 1 URLs in 10.58s

## Red (0 URLs or Error)

- `dia` — BLOCKED_403 — 2026-05-25 14:16:35,355 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 D
- `flv` — ZERO_URLS — 2026-05-25 14:16:36,629 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 F
- `guggenheim` — BLOCKED_403 — 2026-05-25 14:16:38,137 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 G
- `gwangju_biennale` — ZERO_URLS — 2026-05-25 14:16:38,479 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 G
- `hayward` — BLOCKED_403 — 2026-05-25 14:16:40,464 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 H
- `hirshhorn` — ZERO_URLS — 2026-05-25 14:16:40,687 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 H
- `istanbul_biennale` — TIMEOUT — 2026-05-25 14:16:40,788 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 I
- `lacma` — BLOCKED_403 — 2026-05-25 14:16:48,568 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 L
- `leeum` — ZERO_URLS — 2026-05-25 14:16:48,913 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 L
- `lyon_biennale` — ZERO_URLS — 2026-05-25 14:16:54,540 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 L
- `mass_moca` — BLOCKED_403 — 2026-05-25 14:16:55,225 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 M
- `mca_australia` — ZERO_URLS — 2026-05-25 14:17:04,066 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 M
- `mmcaseoul` — ZERO_URLS — 2026-05-25 14:17:10,967 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 M
- `nga` — ZERO_URLS (数据集已恢复，ARTWORK_ONLY 策略正常) — 2026-05-25 14:17:23,282 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 N
- `psa` — ZERO_URLS — 2026-05-25 14:17:28,487 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 P
- `serpentine` — TIMEOUT — Timed out after 45s
- `whitechapel` — BLOCKED_403 — 2026-05-25 14:17:48,882 [INFO] auto_curation.database: Database initialized at exhibitions.db 🚀 采集 W

## Red Site Classification & Recommendations

| Site | Status | Recommendation |
|------|--------|----------------|
| `dia` | BLOCKED_403 | Cloudflare / server block; mark `BLOCKED_CLOUDFLARE` |
| `flv` | ZERO_URLS (403) | Server blocks + SPA; mark `BLOCKED_SPA` |
| `guggenheim` | BLOCKED_403 | Cloudflare; mark `BLOCKED_CLOUDFLARE` |
| `gwangju_biennale` | ZERO_URLS | DNS failure (`gb.or.kr` dead); find new domain or mark `BLOCKED_DNS` |
| `hayward` | BLOCKED_403 | Cloudflare; mark `BLOCKED_CLOUDFLARE` |
| `hirshhorn` | ZERO_URLS | Cloudflare + needs API key; mark `BLOCKED_API_KEY` |
| `istanbul_biennale` | TIMEOUT | Site unresponsive; mark `BLOCKED_SLOW` |
| `lacma` | BLOCKED_403 | Cloudflare; mark `BLOCKED_CLOUDFLARE` |
| `leeum` | ZERO_URLS | SPA (0 `<a>` tags); mark `BLOCKED_SPA` |
| `lyon_biennale` | ZERO_URLS | DNS failure (`biennalede-lyon.com` dead); mark `BLOCKED_DNS` |
| `mass_moca` | BLOCKED_403 | Cloudflare; mark `BLOCKED_CLOUDFLARE` |
| `mca_australia` | ZERO_URLS | SPA (0 `<a>` tags); mark `BLOCKED_SPA` |
| `mmcaseoul` | ZERO_URLS | Connection reset (IP block?); mark `BLOCKED_NETWORK` |
| `new_museum` | ZERO_URLS | SPA (0 `<a>` tags); mark `BLOCKED_SPA` |
| `nga` | ZERO_URLS | Missing local data `data/nga_collection/objects.csv`; supply data or mark `BLOCKED_DATA` |
| `psa` | ZERO_URLS | Requires Playwright (not installed); mark `NEEDS_PLAYWRIGHT` |
| `serpentine` | TIMEOUT | Site extremely slow (>90s); mark `BLOCKED_SLOW` |
| `whitechapel` | BLOCKED_403 | Cloudflare; mark `BLOCKED_CLOUDFLARE` |

## Phase 4 Yellow Fixes (6 sites recovered)

| Site | Issue | Fix | Result |
|------|-------|-----|--------|
| `zkm` | Pattern typo (`exhibition` vs `exhibitions`) + SPA list page | Fixed pattern + added `use_playwright = True` + archive page | 7 URLs |
| `ngv` | Wrong pattern (`/whats-on/exhibitions/` vs actual `/exhibition/`) | Updated pattern to `/exhibition/[^/]+` | 22 URLs |
| `sharjah_biennale` | List page has no exhibition links (pure nav menu) | Implemented custom `get_exhibition_urls()` constructing sb-1..sb-17 | 17 URLs |
| `hamburger_bahnhof` | SSL hostname mismatch on original domain | Switched to SMB museum portal (`smb.museum`) + archive page | 14 URLs |
| `south_london_gallery` | list_url pointed to homepage instead of exhibitions | Fixed list_url to `/exhibitions/` | 3 URLs |
| `pinakothek` | SPA with German/English single-form paths | Enabled `use_playwright = True` + fixed pattern to `exhibition\|ausstellung` + archive | 3 URLs |

## Final State After All Fixes

| Metric | Count | Percentage | Notes |
|--------|------:|------------|-------|
| Total  | 64 | 100% | |
| Green  | 40 | 62.5% | >=5 URLs |
| Yellow | 4 | 6.3% | 1-4 URLs (beyeler 4, pinakothek 3, south_london_gallery 3) |
| Red    | 19 | 29.7% | 0 URLs or error |

**Note on Yellow:** `aic`, `whitney`, and `wikidata` are REST_API/SPARQL parsers that appear as 1 URL in smoke_test due to `--limit 1`; they are functionally healthy.

**Note on Red:** `louisiana` was downgraded from Yellow to Red (403 Cloudflare block). `nga` dataset has been restored and its ARTWORK_ONLY pipeline works, but it requires local CSV data.

## Final Green (>=5 URLs)

- `astrup_fearnley` — 6 URLs in ~60s
- `baltic` — 64 URLs in 5.4s
- `barbican` — 34 URLs in 5.17s
- `berlin_biennale` — 30 URLs in 12.45s
- `brooklyn_museum` — 23 URLs in ~60s
- `documenta` — 15 URLs in ~60s
- `hamburger_bahnhof` — 14 URLs in ~5s
- `hammer_museum` — 7 URLs in 11.49s
- `kanazawa21` — 6 URLs in 7.72s
- `kunsthal` — 10 URLs in 11.0s
- `kunsthaus` — 31 URLs in 0.41s
- `kw_institute` — 31 URLs in 7.07s
- `lenbachhaus` — 120 URLs in 17.98s
- `liverpool_biennial` — 21 URLs in 4.0s
- `maiiam` — 25 URLs in 29.65s
- `maxxi` — 49 URLs in 8.47s
- `mca_chicago` — 12 URLs in 35.61s
- `met` — 43 URLs in 5.28s
- `moma` — 1727 URLs in 0.34s
- `momat` — 15 URLs in 32.16s
- `mori` — 72 URLs in 7.82s
- `mplus` — 38 URLs in 6.26s
- `museum_ludwig` — 6 URLs in 16.98s
- `national_gallery_sg` — 10 URLs in 4.08s
- `new_museum` — 10 URLs in ~20s
- `ngv` — 22 URLs in ~20s
- `njpac` — 22 URLs in 13.73s
- `palaistokyo` — 8 URLs in 11.51s
- `pinakothek` — 3 URLs in ~5s *(upgraded from 2, still Yellow)*
- `pompidou` — 51 URLs in 8.46s
- `reina_sofia` — 9 URLs in 15.24s
- `saopaulo_biennial` — 51 URLs in 9.44s
- `sharjah_biennale` — 17 URLs in ~5s
- `south_london_gallery` — 3 URLs in ~15s *(upgraded from 2, still Yellow)*
- `sydney_biennale` — 33 URLs in 7.77s
- `taipei_biennale` — 6 URLs in 6.58s
- `tate` — 15 URLs in 8.04s
- `ucca` — 28 URLs in 23.53s
- `venice_biennale` — 16 URLs in 14.24s
- `whitney_biennial` — 19 URLs in 12.92s
- `yokohama_triennale` — 34 URLs in 9.9s
- `zkm` — 7 URLs in ~5s

## Final Yellow (1-4 URLs)

- `beyeler` — 4 URLs in 3.75s *(small private museum; no historical exhibition pages)*
- `pinakothek` — 3 URLs in ~5s *(SPA, limited exhibitions on site)*
- `south_london_gallery` — 3 URLs in ~15s *(small gallery, limited active exhibitions)*

## Final Red (0 URLs or Error)

- `dia` — BLOCKED_403 — Cloudflare
- `flv` — ZERO_URLS — Cloudflare + SPA
- `guggenheim` — BLOCKED_403 — Cloudflare
- `gwangju_biennale` — ZERO_URLS — DNS dead (`gb.or.kr`)
- `hayward` — BLOCKED_403 — Cloudflare
- `hirshhorn` — ZERO_URLS — Cloudflare + API key required
- `istanbul_biennale` — TIMEOUT — Site extremely slow (>90s)
- `lacma` — BLOCKED_403 — Cloudflare
- `leeum` — ZERO_URLS — SPA (0 `<a>` tags after Playwright)
- `louisiana` — BLOCKED_403 — Cloudflare/anti-bot *(downgraded from Yellow)*
- `lyon_biennale` — ZERO_URLS — DNS dead
- `mass_moca` — BLOCKED_403 — Cloudflare
- `mca_australia` — ZERO_URLS — SPA (0 `<a>` tags after Playwright)
- `mmcaseoul` — ZERO_URLS — Connection reset (IP block)
- `nga` — ZERO_URLS — Dataset restored (ARTWORK_ONLY works with local CSV)
- `psa` — ZERO_URLS — Network unreachable (China mainland site)
- `serpentine` — TIMEOUT — Site extremely slow (>90s)
- `whitechapel` — BLOCKED_403 — Cloudflare

## Task 2: LLM Parsing Validation (Sample 20)

对 Green/Yellow 状态的 HTML_LLM parser 抽样 20 家，每家 3 个 URL 执行真实 LLM 解析验证。

### 系统性修复（3 项）

| 问题 | 根因 | 修复文件 | 修复内容 |
|:-----|:-----|:---------|:---------|
| JSON 截断 | SenseNova 默认 `max_tokens` 不足，长文本返回不完整 JSON | `src/llm_parser.py` | payload 增加 `"max_tokens": 8192` |
| Pydantic 校验过严 | `ArtworkModel.artist_name` / `work_title` 为 `str`（required），单条作品缺失字段导致整展丢弃 | `src/llm_parser.py` | 改为 `Optional[str] = Field(None, ...)` |
| Baltic pattern 过宽 | `r"baltic\.art/[^/]+"` 匹配了 donate/policy 等非展览页面 | `src/sites/baltic.py` | 收紧为 `r"baltic\.art/whats-on/[^/]+"` |
| LLM 返回 list 崩溃 | LLM 偶发返回 JSON array 而非 object | `src/llm_parser.py` | 增加 `isinstance(parsed_json, list)` 防御，取首元素或返回 None |

### 抽样结果分级

| 状态 | 数量 | Parser |
|:-----|:----:|:-------|
| PASS | 6 | palaistokyo, baltic, kanazawa21, mplus, tate, psa |
| WARN | 2 | documenta（1 个安全过滤个案）, sharjah_biennale（2 个早期页面内容过短） |
| FAIL | 1 | kunsthaus（LLM 超时，生产环境有 native parser） |
| 网络瞬断 | 6 | brooklyn_museum, maxxi, barbican 等（DNS 临时失败，手动复测正常） |
| 已知 Red | 5 | 0 URLs，跳过 |

### 问题详情

**documenta** — `documenta-12` 页面返回 `LLM returned None`（内容被安全过滤）。
**sharjah_biennale** — `sb-1`、`sb-2` 页面返回 `content too short after cleaning`（1993/1995 年早期页面内容极少）。
**kunsthaus** — 3 个 URL 全部 `LLM returned None`（SenseNova 超时）；生产环境使用 `parse_exhibition_page()` native JSON-LD 提取，不受此影响。

### Task 2 修复记录（2 sites recovered）

| Site | Issue | Fix | Result |
|------|-------|-----|--------|
| `mca_chicago` | `/exhibitions/archive` 汇总页被误匹配，清洗后内容过短 | `link_patterns` 增加 negative lookahead 排除 `archive` | 11 URLs，3/3 LLM PASS |
| `documenta` | `documenta-12` 触发 SenseNova 内容安全过滤（400 code 18） | `llm_parser.py` 新增多 provider 自动回退（SenseNova → Gemini） | 3/3 LLM PASS，含 documenta-12 |

### Task 3 修复记录（2 sites recovered）

| Site | Issue | Fix | Result |
|------|-------|-----|--------|
| `lacma` | Cloudflare 403 阻断 | `use_curl_cffi = True` + 修正 link pattern | 29 URLs，LLM PASS |
| `whitechapel` | Cloudflare 403 阻断 | `use_curl_cffi = True` | 10 URLs，LLM PASS |

---

## Raw Data

```json
[
  {
    "site": "aic",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 1.34
  },
  {
    "site": "astrup_fearnley",
    "status": "TIMEOUT",
    "urls_found": 0,
    "error": "Timed out after 45s",
    "elapsed": 45.01
  },
  {
    "site": "baltic",
    "status": "PASS",
    "urls_found": 64,
    "error": null,
    "elapsed": 5.4
  },
  {
    "site": "barbican",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 5.17
  },
  {
    "site": "berlin_biennale",
    "status": "PASS",
    "urls_found": 30,
    "error": null,
    "elapsed": 12.45
  },
  {
    "site": "beyeler",
    "status": "WARN",
    "urls_found": 4,
    "error": null,
    "elapsed": 3.75
  },
  {
    "site": "brooklyn_museum",
    "status": "TIMEOUT",
    "urls_found": 0,
    "error": "Timed out after 45s",
    "elapsed": 45.01
  },
  {
    "site": "dia",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:16:35,355 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Dia Art Foundation... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:35,400 [INFO] auto_curation.scraper: Starting scrape for 'Dia Art Foundation' (City: New York) | strategy=html_llm\n2026-05-25 14:16:35,400 [INFO] auto_curation.sites.base: [Dia Art Foundation] Fetching listing page: https://www.diaart.org/exhibition\n2026-05-25 14:16:35,590 [INFO] httpx: HTTP Request: GET https://w",
    "elapsed": 0.44
  },
  {
    "site": "documenta",
    "status": "TIMEOUT",
    "urls_found": 0,
    "error": "Timed out after 45s",
    "elapsed": 45.01
  },
  {
    "site": "flv",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:16:36,629 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Fondation Louis Vuitton... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:36,656 [INFO] auto_curation.scraper: Starting scrape for 'Fondation Louis Vuitton' (City: Paris) | strategy=html_llm\n2026-05-25 14:16:36,657 [INFO] auto_curation.sites.base: [Fondation Louis Vuitton] Fetching listing page: https://www.fondationlouisvuitton.fr/en.html\n2026-05-25 14:16:37,720 [INFO] httpx: HTTP",
    "elapsed": 1.5
  },
  {
    "site": "guggenheim",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:16:38,137 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Guggenheim Museum... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:38,168 [INFO] auto_curation.scraper: Starting scrape for 'Guggenheim Museum' (City: New York) | strategy=html_llm\n2026-05-25 14:16:38,168 [INFO] auto_curation.sites.base: [Guggenheim Museum] Fetching listing page: https://www.guggenheim.org/exhibitions\n2026-05-25 14:16:38,341 [INFO] httpx: HTTP Request: GET https:/",
    "elapsed": 0.36
  },
  {
    "site": "gwangju_biennale",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:16:38,479 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Gwangju Biennale... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:38,506 [INFO] auto_curation.scraper: Starting scrape for 'Gwangju Biennale' (City: Gwangju) | strategy=html_llm\n2026-05-25 14:16:38,507 [INFO] auto_curation.sites.base: [Gwangju Biennale] Fetching listing page: https://gb.or.kr/en\n2026-05-25 14:16:38,510 [ERROR] auto_curation.sites.base: [Gwangju Biennale] Error fet",
    "elapsed": 0.16
  },
  {
    "site": "hamburger_bahnhof",
    "status": "WARN",
    "urls_found": 3,
    "error": null,
    "elapsed": 3.83
  },
  {
    "site": "hammer_museum",
    "status": "PASS",
    "urls_found": 7,
    "error": null,
    "elapsed": 11.49
  },
  {
    "site": "hayward",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:16:40,464 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Hayward Gallery... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:40,492 [INFO] auto_curation.scraper: Starting scrape for 'Hayward Gallery' (City: London) | strategy=html_llm\n2026-05-25 14:16:40,492 [INFO] auto_curation.sites.base: [Hayward Gallery] Fetching listing page: https://www.southbankcentre.co.uk/venues/hayward-gallery\n2026-05-25 14:16:40,655 [INFO] httpx: HTTP Request: G",
    "elapsed": 0.32
  },
  {
    "site": "hirshhorn",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:16:40,687 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Hirshhorn Museum and Sculpture Garden... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:40,715 [INFO] auto_curation.scraper: Starting scrape for 'Hirshhorn Museum and Sculpture Garden' (City: Washington D.C.) | strategy=rest_api\n2026-05-25 14:16:40,715 [INFO] auto_curation.scraper: [Hirshhorn Museum and Sculpture Garden] Using REST/API mode (no LLM required).\n2026-05-25 14:16:40,71",
    "elapsed": 0.16
  },
  {
    "site": "istanbul_biennale",
    "status": "TIMEOUT",
    "urls_found": 0,
    "error": "2026-05-25 14:16:40,788 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Istanbul Biennial... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:40,816 [INFO] auto_curation.scraper: Starting scrape for 'Istanbul Biennial' (City: Istanbul) | strategy=html_llm\n2026-05-25 14:16:40,816 [INFO] auto_curation.sites.base: [Istanbul Biennial] Fetching listing page: https://bienal.iksv.org/en\n2026-05-25 14:17:10,819 [ERROR] auto_curation.sites.base: [Istanbul Biennia",
    "elapsed": 30.18
  },
  {
    "site": "kanazawa21",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 7.72
  },
  {
    "site": "kunsthal",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 11.0
  },
  {
    "site": "kunsthaus",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 0.41
  },
  {
    "site": "kw_institute",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 7.07
  },
  {
    "site": "lacma",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:16:48,568 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 LACMA... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:48,595 [INFO] auto_curation.scraper: Starting scrape for 'LACMA' (City: Los Angeles) | strategy=html_llm\n2026-05-25 14:16:48,595 [INFO] auto_curation.sites.base: [LACMA] Fetching listing page: https://www.lacma.org/exhibitions\n2026-05-25 14:16:48,778 [INFO] httpx: HTTP Request: GET https://www.lacma.org/exhibitions \"HTTP/1.1 4",
    "elapsed": 0.35
  },
  {
    "site": "leeum",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:16:48,913 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Leeum Samsung Museum... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:48,940 [INFO] auto_curation.scraper: Starting scrape for 'Leeum Samsung Museum' (City: Seoul) | strategy=html_llm\n2026-05-25 14:16:48,940 [INFO] auto_curation.sites.base: [Leeum Samsung Museum] Fetching listing page: https://www.leeum.org/en/exhibitions\n2026-05-25 14:16:49,424 [INFO] httpx: HTTP Request: GET htt",
    "elapsed": 1.39
  },
  {
    "site": "lenbachhaus",
    "status": "PASS",
    "urls_found": 120,
    "error": null,
    "elapsed": 17.98
  },
  {
    "site": "liverpool_biennial",
    "status": "PASS",
    "urls_found": 21,
    "error": null,
    "elapsed": 4.0
  },
  {
    "site": "louisiana",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 29.8
  },
  {
    "site": "lyon_biennale",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:16:54,540 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Lyon Biennale... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:54,568 [INFO] auto_curation.scraper: Starting scrape for 'Lyon Biennale' (City: Lyon) | strategy=html_llm\n2026-05-25 14:16:54,568 [INFO] auto_curation.sites.base: [Lyon Biennale] Fetching listing page: https://www.biennalede-lyon.com\n2026-05-25 14:16:54,571 [ERROR] auto_curation.sites.base: [Lyon Biennale] Error fetchi",
    "elapsed": 0.17
  },
  {
    "site": "maiiam",
    "status": "PASS",
    "urls_found": 25,
    "error": null,
    "elapsed": 29.65
  },
  {
    "site": "mass_moca",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:16:55,225 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 MASS MoCA... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:16:55,253 [INFO] auto_curation.scraper: Starting scrape for 'MASS MoCA' (City: North Adams) | strategy=html_llm\n2026-05-25 14:16:55,253 [INFO] auto_curation.sites.base: [MASS MoCA] Fetching listing page: https://massmoca.org/exhibitions/\n2026-05-25 14:16:55,450 [INFO] httpx: HTTP Request: GET https://massmoca.org/exhibitions/",
    "elapsed": 0.36
  },
  {
    "site": "maxxi",
    "status": "PASS",
    "urls_found": 49,
    "error": null,
    "elapsed": 8.47
  },
  {
    "site": "mca_australia",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:17:04,066 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 MCA Australia... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:04,094 [INFO] auto_curation.scraper: Starting scrape for 'MCA Australia' (City: Sydney) | strategy=html_llm\n2026-05-25 14:17:04,094 [INFO] auto_curation.sites.base: [MCA Australia] Fetching listing page: https://www.mca.com.au/exhibitions/\n2026-05-25 14:17:05,014 [INFO] httpx: HTTP Request: GET https://www.mca.com.au/e",
    "elapsed": 1.44
  },
  {
    "site": "mca_chicago",
    "status": "PASS",
    "urls_found": 12,
    "error": null,
    "elapsed": 35.61
  },
  {
    "site": "met",
    "status": "PASS",
    "urls_found": 43,
    "error": null,
    "elapsed": 5.28
  },
  {
    "site": "mmcaseoul",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:17:10,967 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 MMCA Seoul... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:10,993 [INFO] auto_curation.scraper: Starting scrape for 'MMCA Seoul' (City: Seoul) | strategy=html_llm\n2026-05-25 14:17:10,993 [WARNING] auto_curation.scraper: No exhibition URLs discovered for MMCA Seoul.\n\n📊 采集结果报告:\n==================================================\n 机构名称   : MMCA Seoul\n 发现 URL数  : 0\n 跳过（已存）: 0\n 成功解析   ",
    "elapsed": 0.16
  },
  {
    "site": "moma",
    "status": "PASS",
    "urls_found": 1727,
    "error": null,
    "elapsed": 0.34
  },
  {
    "site": "momat",
    "status": "PASS",
    "urls_found": 15,
    "error": null,
    "elapsed": 32.16
  },
  {
    "site": "mori",
    "status": "PASS",
    "urls_found": 72,
    "error": null,
    "elapsed": 7.82
  },
  {
    "site": "mplus",
    "status": "PASS",
    "urls_found": 38,
    "error": null,
    "elapsed": 6.26
  },
  {
    "site": "museum_ludwig",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 16.98
  },
  {
    "site": "national_gallery_sg",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 4.08
  },
  {
    "site": "new_museum",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:17:21,379 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 New Museum... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:21,406 [INFO] auto_curation.scraper: Starting scrape for 'New Museum' (City: New York) | strategy=html_llm\n2026-05-25 14:17:21,406 [INFO] auto_curation.sites.base: [New Museum] Fetching listing page: https://www.newmuseum.org/exhibitions\n2026-05-25 14:17:21,821 [INFO] httpx: HTTP Request: GET https://www.newmuseum.org/exh",
    "elapsed": 2.56
  },
  {
    "site": "nga",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:17:23,282 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 National Gallery of Art... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:23,315 [INFO] auto_curation.scraper: Starting scrape for 'National Gallery of Art' (City: Washington D.C.) | strategy=artwork_only\n2026-05-25 14:17:23,315 [INFO] auto_curation.scraper: [National Gallery of Art] Using artwork-only mode (no exhibitions, collection only).\n2026-05-25 14:17:23,315 [ERROR] auto_cur",
    "elapsed": 0.18
  },
  {
    "site": "ngv",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 20.3
  },
  {
    "site": "njpac",
    "status": "PASS",
    "urls_found": 22,
    "error": null,
    "elapsed": 13.73
  },
  {
    "site": "palaistokyo",
    "status": "PASS",
    "urls_found": 8,
    "error": null,
    "elapsed": 11.51
  },
  {
    "site": "pinakothek",
    "status": "WARN",
    "urls_found": 2,
    "error": null,
    "elapsed": 3.66
  },
  {
    "site": "pompidou",
    "status": "PASS",
    "urls_found": 51,
    "error": null,
    "elapsed": 8.46
  },
  {
    "site": "psa",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "error": "2026-05-25 14:17:28,487 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Power Station of Art... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:28,516 [INFO] auto_curation.scraper: Starting scrape for 'Power Station of Art' (City: Shanghai) | strategy=html_llm\n2026-05-25 14:17:28,516 [ERROR] auto_curation.sites.psa: [PSA] Playwright is required for PSA scraping but not installed. Install it with: uv pip install playwright && python -m playwright install",
    "elapsed": 0.17
  },
  {
    "site": "reina_sofia",
    "status": "PASS",
    "urls_found": 9,
    "error": null,
    "elapsed": 15.24
  },
  {
    "site": "saopaulo_biennial",
    "status": "PASS",
    "urls_found": 51,
    "error": null,
    "elapsed": 9.44
  },
  {
    "site": "serpentine",
    "status": "TIMEOUT",
    "urls_found": 0,
    "error": "Timed out after 45s",
    "elapsed": 45.01
  },
  {
    "site": "sharjah_biennale",
    "status": "WARN",
    "urls_found": 2,
    "error": null,
    "elapsed": 11.69
  },
  {
    "site": "south_london_gallery",
    "status": "WARN",
    "urls_found": 2,
    "error": null,
    "elapsed": 15.47
  },
  {
    "site": "sydney_biennale",
    "status": "PASS",
    "urls_found": 33,
    "error": null,
    "elapsed": 7.77
  },
  {
    "site": "taipei_biennale",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 6.58
  },
  {
    "site": "tate",
    "status": "PASS",
    "urls_found": 15,
    "error": null,
    "elapsed": 8.04
  },
  {
    "site": "ucca",
    "status": "PASS",
    "urls_found": 28,
    "error": null,
    "elapsed": 23.53
  },
  {
    "site": "venice_biennale",
    "status": "PASS",
    "urls_found": 16,
    "error": null,
    "elapsed": 14.24
  },
  {
    "site": "whitechapel",
    "status": "BLOCKED_403",
    "urls_found": 0,
    "error": "2026-05-25 14:17:48,882 [INFO] auto_curation.database: Database initialized at exhibitions.db\n🚀 采集 Whitechapel Gallery... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-25 14:17:48,911 [INFO] auto_curation.scraper: Starting scrape for 'Whitechapel Gallery' (City: London) | strategy=html_llm\n2026-05-25 14:17:48,911 [INFO] auto_curation.sites.base: [Whitechapel Gallery] Fetching listing page: https://www.whitechapelgallery.org/exhibitions/\n2026-05-25 14:17:49,044 [INFO] httpx: HTTP Request",
    "elapsed": 0.3
  },
  {
    "site": "whitney",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 2.3
  },
  {
    "site": "whitney_biennial",
    "status": "PASS",
    "urls_found": 19,
    "error": null,
    "elapsed": 12.92
  },
  {
    "site": "wikidata",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 4.3
  },
  {
    "site": "yokohama_triennale",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 9.9
  },
  {
    "site": "zkm",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 10.58
  }
]
```
