# Health Check Report

Generated: 2026-05-27T01:08:31.262365

## Summary

| Metric | Count | Percentage |
|--------|------:|------------|
| Total   | 60 | 100% |
| PASS    | 50 | 83.3% |
| SKIPPED | 2 | 3.3% |
| FAIL    | 8 | 13.3% |

## Database Health

- **Exhibitions**: 8554
- **Artworks**: 33014
- **Missing title**: 0 (0.0%)
- **Missing start_date**: 28 (0.3%)
- **Missing concept**: 8166 (95.5%)

### Source Distribution

| Source | Count |
|--------|------:|
| art_institute_of_chicago | 6253 |
| moma | 1726 |
|  | 497 |
| mori_art_museum | 48 |
| m+_museum | 21 |
| serpentine_galleries | 4 |
| tate_modern | 3 |
| rijksmuseum | 2 |

## Detailed Results

| Site | Status | URLs | HTTP | Time | Notes |
|------|--------|-----:|------|-----:|-------|
| `aic` | PASS | 1 | 200 | 7.3s |  |
| `astrup_fearnley` | PASS | 6 | 200 | 41.8s |  |
| `baltic` | PASS | 6 | 200 | 33.2s |  |
| `barbican` | PASS | 31 | 200 | 17.5s |  |
| `berlin_biennale` | PASS | 30 | 200 | 34.7s |  |
| `beyeler` | PASS | 4 | 200 | 1109.4s |  |
| `brooklyn_museum` | PASS | 23 | 200 | 36.5s |  |
| `dia` | SKIPPED | 0 | 403 | 0.4s | BLOCKED_CLOUDFLARE |
| `documenta` | PASS | 15 | 200 | 57.0s |  |
| `flv` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:35:22,771 [INFO] auto_curation.database: Datab |
| `guggenheim` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:35:22,941 [INFO] auto_curation.database: Datab |
| `hamburger_bahnhof` | PASS | 14 | 200 | 18.0s |  |
| `hammer_museum` | PASS | 7 | 200 | 23.4s |  |
| `hayward` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:35:59,130 [INFO] auto_curation.database: Datab |
| `hirshhorn` | SKIPPED | 0 | — | 0.2s | BLOCKED_API_KEY |
| `kanazawa21` | PASS | 5 | 200 | 18.2s |  |
| `kunsthal` | PASS | 9 | 200 | 22.6s |  |
| `kunsthaus` | PASS | 31 | 200 | 10.1s |  |
| `kw_institute` | PASS | 31 | 200 | 89.0s |  |
| `lacma` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:36:27,749 [INFO] auto_curation.database: Datab |
| `leeum` | PASS | 4 | 200 | 55.5s |  |
| `lenbachhaus` | PASS | 120 | 200 | 28.4s |  |
| `liverpool_biennial` | PASS | 21 | 200 | 43.0s |  |
| `louisiana` | PASS | 1 | 200 | 37.9s |  |
| `maiiam` | PASS | 25 | 200 | 56.3s |  |
| `mass_moca` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:38:34,831 [INFO] auto_curation.database: Datab |
| `maxxi` | PASS | 54 | 200 | 19.4s |  |
| `mca_australia` | TIMEOUT | 0 | — | 180.0s | Timed out after 180s |
| `mca_chicago` | PASS | 11 | 200 | 27.8s |  |
| `met` | PASS | 43 | 200 | 41.2s |  |
| `moma` | PASS | 1727 | — | 0.3s |  |
| `momat` | PASS | 15 | 200 | 34.2s |  |
| `mori` | PASS | 72 | 200 | 14.3s |  |
| `mplus` | PASS | 38 | 200 | 15.5s |  |
| `museum_ludwig` | PASS | 6 | 200 | 22.4s |  |
| `national_gallery_sg` | PASS | 10 | 200 | 16.2s |  |
| `new_museum` | PASS | 10 | — | 20.9s |  |
| `nga` | PASS | 1 | — | 1.9s |  |
| `ngv` | PASS | 22 | 200 | 24.4s |  |
| `njpac` | PASS | 22 | 200 | 45.0s |  |
| `palaistokyo` | PASS | 8 | 200 | 26.9s |  |
| `pinakothek` | PASS | 3 | 200 | 42.8s |  |
| `pompidou` | PASS | 52 | 200 | 17.6s |  |
| `psa` | TIMEOUT | 0 | — | 60.6s | 2026-05-27 01:07:30,867 [INFO] auto_curation.database: Datab |
| `reina_sofia` | PASS | 9 | 200 | 21.1s |  |
| `saopaulo_biennial` | PASS | 51 | 200 | 13.6s |  |
| `serpentine` | PASS | 60 | 200 | 85.6s |  |
| `sharjah_biennale` | PASS | 17 | 200 | 15.3s |  |
| `south_london_gallery` | PASS | 4 | 200 | 15.8s |  |
| `sydney_biennale` | PASS | 34 | 200 | 9.3s |  |
| `taipei_biennale` | PASS | 6 | 200 | 4.0s |  |
| `tate` | PASS | 16 | 200 | 21.6s |  |
| `ucca` | PASS | 28 | 200 | 26.4s |  |
| `venice_biennale` | PASS | 16 | 200 | 86.9s |  |
| `whitechapel` | ZERO_URLS | 0 | — | 0.2s | 2026-05-27 00:45:01,644 [INFO] auto_curation.database: Datab |
| `whitney` | PASS | 1 | 200 | 2.6s |  |
| `whitney_biennial` | PASS | 19 | 200 | 13.3s |  |
| `wikidata` | PASS | 1 | — | 35.9s |  |
| `yokohama_triennale` | PASS | 34 | 200 | 18.2s |  |
| `zkm` | PASS | 7 | 200 | 25.4s |  |

## Raw Data

```json
[
  {
    "site": "aic",
    "status": "PASS",
    "urls_found": 1,
    "http_status": 200,
    "elapsed": 7.27,
    "error": null
  },
  {
    "site": "astrup_fearnley",
    "status": "PASS",
    "urls_found": 6,
    "http_status": 200,
    "elapsed": 41.83,
    "error": null
  },
  {
    "site": "baltic",
    "status": "PASS",
    "urls_found": 6,
    "http_status": 200,
    "elapsed": 33.19,
    "error": null
  },
  {
    "site": "barbican",
    "status": "PASS",
    "urls_found": 31,
    "http_status": 200,
    "elapsed": 17.52,
    "error": null
  },
  {
    "site": "berlin_biennale",
    "status": "PASS",
    "urls_found": 30,
    "http_status": 200,
    "elapsed": 34.68,
    "error": null
  },
  {
    "site": "beyeler",
    "status": "PASS",
    "urls_found": 4,
    "http_status": 200,
    "elapsed": 1109.37,
    "error": null
  },
  {
    "site": "brooklyn_museum",
    "status": "PASS",
    "urls_found": 23,
    "http_status": 200,
    "elapsed": 36.55,
    "error": null
  },
  {
    "site": "dia",
    "status": "SKIPPED",
    "urls_found": 0,
    "http_status": 403,
    "elapsed": 0.41,
    "error": "BLOCKED_CLOUDFLARE"
  },
  {
    "site": "documenta",
    "status": "PASS",
    "urls_found": 15,
    "http_status": 200,
    "elapsed": 57.04,
    "error": null
  },
  {
    "site": "flv",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.17,
    "error": "2026-05-27 00:35:22,771 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:35:22,771 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 Fondation Louis Vuitton... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:35:22,797 [INFO] auto_cura"
  },
  {
    "site": "guggenheim",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.17,
    "error": "2026-05-27 00:35:22,941 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:35:22,942 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 Guggenheim Museum... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:35:22,968 [INFO] auto_curation.s"
  },
  {
    "site": "hamburger_bahnhof",
    "status": "PASS",
    "urls_found": 14,
    "http_status": 200,
    "elapsed": 17.97,
    "error": null
  },
  {
    "site": "hammer_museum",
    "status": "PASS",
    "urls_found": 7,
    "http_status": 200,
    "elapsed": 23.45,
    "error": null
  },
  {
    "site": "hayward",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.17,
    "error": "2026-05-27 00:35:59,130 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:35:59,130 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 Hayward Gallery... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:35:59,156 [INFO] auto_curation.scr"
  },
  {
    "site": "hirshhorn",
    "status": "SKIPPED",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.17,
    "error": "BLOCKED_API_KEY"
  },
  {
    "site": "kanazawa21",
    "status": "PASS",
    "urls_found": 5,
    "http_status": 200,
    "elapsed": 18.18,
    "error": null
  },
  {
    "site": "kunsthal",
    "status": "PASS",
    "urls_found": 9,
    "http_status": 200,
    "elapsed": 22.56,
    "error": null
  },
  {
    "site": "kunsthaus",
    "status": "PASS",
    "urls_found": 31,
    "http_status": 200,
    "elapsed": 10.11,
    "error": null
  },
  {
    "site": "kw_institute",
    "status": "PASS",
    "urls_found": 31,
    "http_status": 200,
    "elapsed": 89.02,
    "error": null
  },
  {
    "site": "lacma",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.18,
    "error": "2026-05-27 00:36:27,749 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:36:27,749 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 LACMA... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:36:27,780 [INFO] auto_curation.scraper: Star"
  },
  {
    "site": "leeum",
    "status": "PASS",
    "urls_found": 4,
    "http_status": 200,
    "elapsed": 55.5,
    "error": null
  },
  {
    "site": "lenbachhaus",
    "status": "PASS",
    "urls_found": 120,
    "http_status": 200,
    "elapsed": 28.41,
    "error": null
  },
  {
    "site": "liverpool_biennial",
    "status": "PASS",
    "urls_found": 21,
    "http_status": 200,
    "elapsed": 42.99,
    "error": null
  },
  {
    "site": "louisiana",
    "status": "PASS",
    "urls_found": 1,
    "http_status": 200,
    "elapsed": 37.89,
    "error": null
  },
  {
    "site": "maiiam",
    "status": "PASS",
    "urls_found": 25,
    "http_status": 200,
    "elapsed": 56.33,
    "error": null
  },
  {
    "site": "mass_moca",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.18,
    "error": "2026-05-27 00:38:34,831 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:38:34,831 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 MASS MoCA... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:38:34,858 [INFO] auto_curation.scraper: "
  },
  {
    "site": "maxxi",
    "status": "PASS",
    "urls_found": 54,
    "http_status": 200,
    "elapsed": 19.35,
    "error": null
  },
  {
    "site": "mca_australia",
    "status": "TIMEOUT",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 180.01,
    "error": "Timed out after 180s"
  },
  {
    "site": "mca_chicago",
    "status": "PASS",
    "urls_found": 11,
    "http_status": 200,
    "elapsed": 27.84,
    "error": null
  },
  {
    "site": "met",
    "status": "PASS",
    "urls_found": 43,
    "http_status": 200,
    "elapsed": 41.18,
    "error": null
  },
  {
    "site": "moma",
    "status": "PASS",
    "urls_found": 1727,
    "http_status": null,
    "elapsed": 0.34,
    "error": null
  },
  {
    "site": "momat",
    "status": "PASS",
    "urls_found": 15,
    "http_status": 200,
    "elapsed": 34.24,
    "error": null
  },
  {
    "site": "mori",
    "status": "PASS",
    "urls_found": 72,
    "http_status": 200,
    "elapsed": 14.28,
    "error": null
  },
  {
    "site": "mplus",
    "status": "PASS",
    "urls_found": 38,
    "http_status": 200,
    "elapsed": 15.46,
    "error": null
  },
  {
    "site": "museum_ludwig",
    "status": "PASS",
    "urls_found": 6,
    "http_status": 200,
    "elapsed": 22.39,
    "error": null
  },
  {
    "site": "national_gallery_sg",
    "status": "PASS",
    "urls_found": 10,
    "http_status": 200,
    "elapsed": 16.25,
    "error": null
  },
  {
    "site": "new_museum",
    "status": "PASS",
    "urls_found": 10,
    "http_status": null,
    "elapsed": 20.87,
    "error": null
  },
  {
    "site": "nga",
    "status": "PASS",
    "urls_found": 1,
    "http_status": null,
    "elapsed": 1.93,
    "error": null
  },
  {
    "site": "ngv",
    "status": "PASS",
    "urls_found": 22,
    "http_status": 200,
    "elapsed": 24.35,
    "error": null
  },
  {
    "site": "njpac",
    "status": "PASS",
    "urls_found": 22,
    "http_status": 200,
    "elapsed": 44.97,
    "error": null
  },
  {
    "site": "palaistokyo",
    "status": "PASS",
    "urls_found": 8,
    "http_status": 200,
    "elapsed": 26.92,
    "error": null
  },
  {
    "site": "pinakothek",
    "status": "PASS",
    "urls_found": 3,
    "http_status": 200,
    "elapsed": 42.75,
    "error": null
  },
  {
    "site": "pompidou",
    "status": "PASS",
    "urls_found": 52,
    "http_status": 200,
    "elapsed": 17.61,
    "error": null
  },
  {
    "site": "psa",
    "status": "TIMEOUT",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 60.57,
    "error": "2026-05-27 01:07:30,867 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 01:07:30,867 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 Power Station of Art... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 01:07:30,898 [INFO] auto_curatio"
  },
  {
    "site": "reina_sofia",
    "status": "PASS",
    "urls_found": 9,
    "http_status": 200,
    "elapsed": 21.15,
    "error": null
  },
  {
    "site": "saopaulo_biennial",
    "status": "PASS",
    "urls_found": 51,
    "http_status": 200,
    "elapsed": 13.62,
    "error": null
  },
  {
    "site": "serpentine",
    "status": "PASS",
    "urls_found": 60,
    "http_status": 200,
    "elapsed": 85.59,
    "error": null
  },
  {
    "site": "sharjah_biennale",
    "status": "PASS",
    "urls_found": 17,
    "http_status": 200,
    "elapsed": 15.31,
    "error": null
  },
  {
    "site": "south_london_gallery",
    "status": "PASS",
    "urls_found": 4,
    "http_status": 200,
    "elapsed": 15.77,
    "error": null
  },
  {
    "site": "sydney_biennale",
    "status": "PASS",
    "urls_found": 34,
    "http_status": 200,
    "elapsed": 9.26,
    "error": null
  },
  {
    "site": "taipei_biennale",
    "status": "PASS",
    "urls_found": 6,
    "http_status": 200,
    "elapsed": 4.05,
    "error": null
  },
  {
    "site": "tate",
    "status": "PASS",
    "urls_found": 16,
    "http_status": 200,
    "elapsed": 21.61,
    "error": null
  },
  {
    "site": "ucca",
    "status": "PASS",
    "urls_found": 28,
    "http_status": 200,
    "elapsed": 26.36,
    "error": null
  },
  {
    "site": "venice_biennale",
    "status": "PASS",
    "urls_found": 16,
    "http_status": 200,
    "elapsed": 86.94,
    "error": null
  },
  {
    "site": "whitechapel",
    "status": "ZERO_URLS",
    "urls_found": 0,
    "http_status": null,
    "elapsed": 0.16,
    "error": "2026-05-27 00:45:01,644 [INFO] auto_curation.database: Database initialized at exhibitions.db\n2026-05-27 00:45:01,644 [INFO] auto_curation.llm_parser: LLM response caching enabled.\n🚀 采集 Whitechapel Gallery... 数据库: exhibitions.db\n⚠️  [DRY-RUN] 模拟运行，不写入数据库。\n2026-05-27 00:45:01,669 [INFO] auto_curation"
  },
  {
    "site": "whitney",
    "status": "PASS",
    "urls_found": 1,
    "http_status": 200,
    "elapsed": 2.63,
    "error": null
  },
  {
    "site": "whitney_biennial",
    "status": "PASS",
    "urls_found": 19,
    "http_status": 200,
    "elapsed": 13.33,
    "error": null
  },
  {
    "site": "wikidata",
    "status": "PASS",
    "urls_found": 1,
    "http_status": null,
    "elapsed": 35.88,
    "error": null
  },
  {
    "site": "yokohama_triennale",
    "status": "PASS",
    "urls_found": 34,
    "http_status": 200,
    "elapsed": 18.24,
    "error": null
  },
  {
    "site": "zkm",
    "status": "PASS",
    "urls_found": 7,
    "http_status": 200,
    "elapsed": 25.4,
    "error": null
  }
]
```
