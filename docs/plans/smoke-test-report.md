# Smoke Test Report

Generated: 2026-05-27T12:36:08.707638

## Summary

| Metric | Count | Percentage |
|--------|------:|------------|
| Total  | 60 | 100% |
| Green  | 49 | 81.7% |
| Yellow | 3 | 5.0% |
| Red    | 8 | 13.3% |

## Green (>=5 URLs)

- `aic` — 1 URLs in 2.3s
- `astrup_fearnley` — 6 URLs in 2.03s
- `baltic` — 6 URLs in 1.95s
- `barbican` — 34 URLs in 0.57s
- `berlin_biennale` — 30 URLs in 2.04s
- `beyeler` — 20 URLs in 27.15s
- `brooklyn_museum` — 23 URLs in 8.84s
- `documenta` — 15 URLs in 4.38s
- `hamburger_bahnhof` — 14 URLs in 6.01s
- `hammer_museum` — 7 URLs in 1.55s
- `kanazawa21` — 5 URLs in 4.09s
- `kunsthal` — 9 URLs in 2.77s
- `kunsthaus` — 31 URLs in 1.69s
- `kw_institute` — 31 URLs in 3.22s
- `lenbachhaus` — 120 URLs in 4.36s
- `liverpool_biennial` — 21 URLs in 1.46s
- `louisiana` — 131 URLs in 5.72s
- `maiiam` — 25 URLs in 6.58s
- `maxxi` — 53 URLs in 2.72s
- `mca_australia` — 361 URLs in 43.66s
- `mca_chicago` — 11 URLs in 2.88s
- `met` — 43 URLs in 2.45s
- `moma` — 1727 URLs in 0.21s
- `momat` — 15 URLs in 1.0s
- `mori` — 72 URLs in 3.78s
- `mplus` — 38 URLs in 3.28s
- `museum_ludwig` — 6 URLs in 1.41s
- `national_gallery_sg` — 10 URLs in 0.41s
- `new_museum` — 10 URLs in 22.62s
- `nga` — 1 URLs in 1.64s
- `ngv` — 22 URLs in 4.91s
- `njpac` — 22 URLs in 2.41s
- `palaistokyo` — 8 URLs in 5.18s
- `pompidou` — 52 URLs in 9.12s
- `psa` — 24 URLs in 22.38s
- `reina_sofia` — 9 URLs in 2.39s
- `saopaulo_biennial` — 50 URLs in 4.71s
- `serpentine` — 60 URLs in 52.32s
- `sharjah_biennale` — 17 URLs in 4.57s
- `sydney_biennale` — 34 URLs in 2.14s
- `taipei_biennale` — 6 URLs in 1.13s
- `tate` — 16 URLs in 0.46s
- `ucca` — 28 URLs in 3.72s
- `venice_biennale` — 16 URLs in 5.57s
- `whitney` — 1 URLs in 2.22s
- `whitney_biennial` — 19 URLs in 1.63s
- `wikidata` — 1 URLs in 2.22s
- `yokohama_triennale` — 34 URLs in 2.63s
- `zkm` — 7 URLs in 4.01s

## Yellow (1-4 URLs)

- `leeum` — 4 URLs in 12.26s
- `pinakothek` — 3 URLs in 38.56s
- `south_london_gallery` — 4 URLs in 1.25s

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
    "status": "PASS",
    "urls_found": 1,
    "error": null,
    "elapsed": 2.3
  },
  {
    "site": "astrup_fearnley",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 2.03
  },
  {
    "site": "baltic",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.95
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
    "elapsed": 2.04
  },
  {
    "site": "beyeler",
    "status": "PASS",
    "urls_found": 20,
    "error": null,
    "elapsed": 27.15
  },
  {
    "site": "brooklyn_museum",
    "status": "PASS",
    "urls_found": 23,
    "error": null,
    "elapsed": 8.84
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
    "elapsed": 4.38
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
    "elapsed": 6.01
  },
  {
    "site": "hammer_museum",
    "status": "PASS",
    "urls_found": 7,
    "error": null,
    "elapsed": 1.55
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
    "elapsed": 4.09
  },
  {
    "site": "kunsthal",
    "status": "PASS",
    "urls_found": 9,
    "error": null,
    "elapsed": 2.77
  },
  {
    "site": "kunsthaus",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 1.69
  },
  {
    "site": "kw_institute",
    "status": "PASS",
    "urls_found": 31,
    "error": null,
    "elapsed": 3.22
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
    "elapsed": 12.26
  },
  {
    "site": "lenbachhaus",
    "status": "PASS",
    "urls_found": 120,
    "error": null,
    "elapsed": 4.36
  },
  {
    "site": "liverpool_biennial",
    "status": "PASS",
    "urls_found": 21,
    "error": null,
    "elapsed": 1.46
  },
  {
    "site": "louisiana",
    "status": "PASS",
    "urls_found": 131,
    "error": null,
    "elapsed": 5.72
  },
  {
    "site": "maiiam",
    "status": "PASS",
    "urls_found": 25,
    "error": null,
    "elapsed": 6.58
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
    "urls_found": 53,
    "error": null,
    "elapsed": 2.72
  },
  {
    "site": "mca_australia",
    "status": "PASS",
    "urls_found": 361,
    "error": null,
    "elapsed": 43.66
  },
  {
    "site": "mca_chicago",
    "status": "PASS",
    "urls_found": 11,
    "error": null,
    "elapsed": 2.88
  },
  {
    "site": "met",
    "status": "PASS",
    "urls_found": 43,
    "error": null,
    "elapsed": 2.45
  },
  {
    "site": "moma",
    "status": "PASS",
    "urls_found": 1727,
    "error": null,
    "elapsed": 0.21
  },
  {
    "site": "momat",
    "status": "PASS",
    "urls_found": 15,
    "error": null,
    "elapsed": 1.0
  },
  {
    "site": "mori",
    "status": "PASS",
    "urls_found": 72,
    "error": null,
    "elapsed": 3.78
  },
  {
    "site": "mplus",
    "status": "PASS",
    "urls_found": 38,
    "error": null,
    "elapsed": 3.28
  },
  {
    "site": "museum_ludwig",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.41
  },
  {
    "site": "national_gallery_sg",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 0.41
  },
  {
    "site": "new_museum",
    "status": "PASS",
    "urls_found": 10,
    "error": null,
    "elapsed": 22.62
  },
  {
    "site": "nga",
    "status": "PASS",
    "urls_found": 1,
    "error": null,
    "elapsed": 1.64
  },
  {
    "site": "ngv",
    "status": "PASS",
    "urls_found": 22,
    "error": null,
    "elapsed": 4.91
  },
  {
    "site": "njpac",
    "status": "PASS",
    "urls_found": 22,
    "error": null,
    "elapsed": 2.41
  },
  {
    "site": "palaistokyo",
    "status": "PASS",
    "urls_found": 8,
    "error": null,
    "elapsed": 5.18
  },
  {
    "site": "pinakothek",
    "status": "WARN",
    "urls_found": 3,
    "error": null,
    "elapsed": 38.56
  },
  {
    "site": "pompidou",
    "status": "PASS",
    "urls_found": 52,
    "error": null,
    "elapsed": 9.12
  },
  {
    "site": "psa",
    "status": "PASS",
    "urls_found": 24,
    "error": null,
    "elapsed": 22.38
  },
  {
    "site": "reina_sofia",
    "status": "PASS",
    "urls_found": 9,
    "error": null,
    "elapsed": 2.39
  },
  {
    "site": "saopaulo_biennial",
    "status": "PASS",
    "urls_found": 50,
    "error": null,
    "elapsed": 4.71
  },
  {
    "site": "serpentine",
    "status": "PASS",
    "urls_found": 60,
    "error": null,
    "elapsed": 52.32
  },
  {
    "site": "sharjah_biennale",
    "status": "PASS",
    "urls_found": 17,
    "error": null,
    "elapsed": 4.57
  },
  {
    "site": "south_london_gallery",
    "status": "WARN",
    "urls_found": 4,
    "error": null,
    "elapsed": 1.25
  },
  {
    "site": "sydney_biennale",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 2.14
  },
  {
    "site": "taipei_biennale",
    "status": "PASS",
    "urls_found": 6,
    "error": null,
    "elapsed": 1.13
  },
  {
    "site": "tate",
    "status": "PASS",
    "urls_found": 16,
    "error": null,
    "elapsed": 0.46
  },
  {
    "site": "ucca",
    "status": "PASS",
    "urls_found": 28,
    "error": null,
    "elapsed": 3.72
  },
  {
    "site": "venice_biennale",
    "status": "PASS",
    "urls_found": 16,
    "error": null,
    "elapsed": 5.57
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
    "status": "PASS",
    "urls_found": 1,
    "error": null,
    "elapsed": 2.22
  },
  {
    "site": "whitney_biennial",
    "status": "PASS",
    "urls_found": 19,
    "error": null,
    "elapsed": 1.63
  },
  {
    "site": "wikidata",
    "status": "PASS",
    "urls_found": 1,
    "error": null,
    "elapsed": 2.22
  },
  {
    "site": "yokohama_triennale",
    "status": "PASS",
    "urls_found": 34,
    "error": null,
    "elapsed": 2.63
  },
  {
    "site": "zkm",
    "status": "PASS",
    "urls_found": 7,
    "error": null,
    "elapsed": 4.01
  }
]
```
