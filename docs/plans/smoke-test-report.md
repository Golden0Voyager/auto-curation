# Smoke Test Report

Generated: 2026-05-27T10:18:16.688373

## Summary

| Metric | Count | Percentage |
|--------|------:|------------|
| Total  | 60 | 100% |
| Green  | 43 | 71.7% |
| Yellow | 9 | 15.0% |
| Red    | 8 | 13.3% |

## Green (>=5 URLs)

- `astrup_fearnley` — 6 URLs in 1.92s
- `baltic` — 6 URLs in 1.79s
- `barbican` — 34 URLs in 0.57s
- `berlin_biennale` — 30 URLs in 1.91s
- `brooklyn_museum` — 23 URLs in 15.6s
- `documenta` — 15 URLs in 3.94s
- `hamburger_bahnhof` — 14 URLs in 1.39s
- `hammer_museum` — 7 URLs in 7.82s
- `kanazawa21` — 5 URLs in 5.6s
- `kunsthal` — 9 URLs in 1.33s
- `kunsthaus` — 31 URLs in 0.21s
- `kw_institute` — 31 URLs in 1.96s
- `lenbachhaus` — 120 URLs in 4.29s
- `liverpool_biennial` — 21 URLs in 16.99s
- `maiiam` — 25 URLs in 4.12s
- `maxxi` — 54 URLs in 1.11s
- `mca_australia` — 361 URLs in 46.12s
- `mca_chicago` — 11 URLs in 1.85s
- `met` — 43 URLs in 43.98s
- `moma` — 1727 URLs in 0.16s
- `momat` — 15 URLs in 0.54s
- `mori` — 72 URLs in 3.66s
- `mplus` — 38 URLs in 4.71s
- `museum_ludwig` — 6 URLs in 1.14s
- `national_gallery_sg` — 10 URLs in 0.34s
- `new_museum` — 10 URLs in 17.25s
- `ngv` — 22 URLs in 3.59s
- `njpac` — 22 URLs in 1.78s
- `palaistokyo` — 8 URLs in 1.72s
- `pompidou` — 52 URLs in 0.98s
- `psa` — 24 URLs in 21.43s
- `reina_sofia` — 9 URLs in 1.46s
- `saopaulo_biennial` — 50 URLs in 3.61s
- `serpentine` — 60 URLs in 12.38s
- `sharjah_biennale` — 17 URLs in 4.53s
- `sydney_biennale` — 34 URLs in 2.09s
- `taipei_biennale` — 6 URLs in 3.99s
- `tate` — 16 URLs in 0.66s
- `ucca` — 28 URLs in 3.2s
- `venice_biennale` — 16 URLs in 1.2s
- `whitney_biennial` — 19 URLs in 1.66s
- `yokohama_triennale` — 34 URLs in 2.51s
- `zkm` — 7 URLs in 4.13s

## Yellow (1-4 URLs)

- `aic` — 1 URLs in 1.12s
- `beyeler` — 4 URLs in 19.38s
- `leeum` — 4 URLs in 11.92s
- `louisiana` — 1 URLs in 3.21s
- `nga` — 1 URLs in 1.5s
- `pinakothek` — 3 URLs in 26.52s
- `south_london_gallery` — 4 URLs in 1.36s
- `whitney` — 1 URLs in 2.14s
- `wikidata` — 1 URLs in 9.67s

## Red (0 URLs or Error)

- `dia` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE
- `flv` — BLOCKED_SPA — Parser declared as BLOCKED_SPA
- `guggenheim` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE
- `hayward` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE
- `hirshhorn` — BLOCKED_API_KEY — Parser declared as BLOCKED_API_KEY
- `lacma` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE
- `mass_moca` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE
- `whitechapel` — BLOCKED_CLOUDFLARE — Parser declared as BLOCKED_CLOUDFLARE

## Raw Data

```json
[
  {
    "site": "aic",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 1.12
  },
  {
    "site": "astrup_fearnley",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.92
  },
  {
    "site": "baltic",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.79
  },
  {
    "site": "barbican",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 0.57
  },
  {
    "site": "berlin_biennale",
    "status": "PASS",
    "urls_found": 30,
    "error": null,
    "elapsed": 1.91
  },
  {
    "site": "beyeler",
    "status": "WARN",
    "urls_found": 4,
    "error": null,
    "elapsed": 19.38
  },
  {
    "site": "brooklyn_museum",
    "status": "PASS",
    "urls_found": 23,
    "error": null,
    "elapsed": 15.6
  },
  {
    "site": "dia",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "documenta",
    "status": "PASS",
    "urls_found": 15,
    "error": null,
    "elapsed": 3.94
  },
  {
    "site": "flv",
    "status": "BLOCKED_SPA",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_SPA",
    "elapsed": 0.0
  },
  {
    "site": "guggenheim",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "hamburger_bahnhof",
    "status": "PASS",
    "urls_found": 14,
    "error": null,
    "elapsed": 1.39
  },
  {
    "site": "hammer_museum",
    "status": "PASS",
    "urls_found": 7,
    "error": null,
    "elapsed": 7.82
  },
  {
    "site": "hayward",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "hirshhorn",
    "status": "BLOCKED_API_KEY",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_API_KEY",
    "elapsed": 0.0
  },
  {
    "site": "kanazawa21",
    "status": "PASS",
    "urls_found": 5,
    "error": null,
    "elapsed": 5.6
  },
  {
    "site": "kunsthal",
    "status": "PASS",
    "urls_found": 9,
    "error": null,
    "elapsed": 1.33
  },
  {
    "site": "kunsthaus",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 0.21
  },
  {
    "site": "kw_institute",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 1.96
  },
  {
    "site": "lacma",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "leeum",
    "status": "WARN",
    "urls_found": 4,
    "error": null,
    "elapsed": 11.92
  },
  {
    "site": "lenbachhaus",
    "status": "PASS",
    "urls_found": 120,
    "error": null,
    "elapsed": 4.29
  },
  {
    "site": "liverpool_biennial",
    "status": "PASS",
    "urls_found": 21,
    "error": null,
    "elapsed": 16.99
  },
  {
    "site": "louisiana",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 3.21
  },
  {
    "site": "maiiam",
    "status": "PASS",
    "urls_found": 25,
    "error": null,
    "elapsed": 4.12
  },
  {
    "site": "mass_moca",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "maxxi",
    "status": "PASS",
    "urls_found": 54,
    "error": null,
    "elapsed": 1.11
  },
  {
    "site": "mca_australia",
    "status": "PASS",
    "urls_found": 361,
    "error": null,
    "elapsed": 46.12
  },
  {
    "site": "mca_chicago",
    "status": "PASS",
    "urls_found": 11,
    "error": null,
    "elapsed": 1.85
  },
  {
    "site": "met",
    "status": "PASS",
    "urls_found": 43,
    "error": null,
    "elapsed": 43.98
  },
  {
    "site": "moma",
    "status": "PASS",
    "urls_found": 1727,
    "error": null,
    "elapsed": 0.16
  },
  {
    "site": "momat",
    "status": "PASS",
    "urls_found": 15,
    "error": null,
    "elapsed": 0.54
  },
  {
    "site": "mori",
    "status": "PASS",
    "urls_found": 72,
    "error": null,
    "elapsed": 3.66
  },
  {
    "site": "mplus",
    "status": "PASS",
    "urls_found": 38,
    "error": null,
    "elapsed": 4.71
  },
  {
    "site": "museum_ludwig",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.14
  },
  {
    "site": "national_gallery_sg",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 0.34
  },
  {
    "site": "new_museum",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 17.25
  },
  {
    "site": "nga",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 1.5
  },
  {
    "site": "ngv",
    "status": "PASS",
    "urls_found": 22,
    "error": null,
    "elapsed": 3.59
  },
  {
    "site": "njpac",
    "status": "PASS",
    "urls_found": 22,
    "error": null,
    "elapsed": 1.78
  },
  {
    "site": "palaistokyo",
    "status": "PASS",
    "urls_found": 8,
    "error": null,
    "elapsed": 1.72
  },
  {
    "site": "pinakothek",
    "status": "WARN",
    "urls_found": 3,
    "error": null,
    "elapsed": 26.52
  },
  {
    "site": "pompidou",
    "status": "PASS",
    "urls_found": 52,
    "error": null,
    "elapsed": 0.98
  },
  {
    "site": "psa",
    "status": "PASS",
    "urls_found": 24,
    "error": null,
    "elapsed": 21.43
  },
  {
    "site": "reina_sofia",
    "status": "PASS",
    "urls_found": 9,
    "error": null,
    "elapsed": 1.46
  },
  {
    "site": "saopaulo_biennial",
    "status": "PASS",
    "urls_found": 50,
    "error": null,
    "elapsed": 3.61
  },
  {
    "site": "serpentine",
    "status": "PASS",
    "urls_found": 60,
    "error": null,
    "elapsed": 12.38
  },
  {
    "site": "sharjah_biennale",
    "status": "PASS",
    "urls_found": 17,
    "error": null,
    "elapsed": 4.53
  },
  {
    "site": "south_london_gallery",
    "status": "WARN",
    "urls_found": 4,
    "error": null,
    "elapsed": 1.36
  },
  {
    "site": "sydney_biennale",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 2.09
  },
  {
    "site": "taipei_biennale",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 3.99
  },
  {
    "site": "tate",
    "status": "PASS",
    "urls_found": 16,
    "error": null,
    "elapsed": 0.66
  },
  {
    "site": "ucca",
    "status": "PASS",
    "urls_found": 28,
    "error": null,
    "elapsed": 3.2
  },
  {
    "site": "venice_biennale",
    "status": "PASS",
    "urls_found": 16,
    "error": null,
    "elapsed": 1.2
  },
  {
    "site": "whitechapel",
    "status": "BLOCKED_CLOUDFLARE",
    "urls_found": 0,
    "error": "Parser declared as BLOCKED_CLOUDFLARE",
    "elapsed": 0.0
  },
  {
    "site": "whitney",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 2.14
  },
  {
    "site": "whitney_biennial",
    "status": "PASS",
    "urls_found": 19,
    "error": null,
    "elapsed": 1.66
  },
  {
    "site": "wikidata",
    "status": "WARN",
    "urls_found": 1,
    "error": null,
    "elapsed": 9.67
  },
  {
    "site": "yokohama_triennale",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 2.51
  },
  {
    "site": "zkm",
    "status": "PASS",
    "urls_found": 7,
    "error": null,
    "elapsed": 4.13
  }
]
```
