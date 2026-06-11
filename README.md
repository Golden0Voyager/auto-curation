<div align="center">

# Auto Curation

**AI-powered global art exhibition data pipeline**

*Structured exhibition data from 61 world-class institutions — automated, validated, open.*

[![Sponsor Me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/golden_voyager)

[English](#overview) · [中文](README.zh-CN.md)

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Golden0Voyager/auto-curation/ci.yml?branch=main&label=CI&logo=github)](.github/workflows/ci.yml)
[![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](.github/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-601%20passed-brightgreen)](tests/)
[![mypy](https://img.shields.io/badge/mypy-0%20errors-success)](mypy.ini)
[![ruff](https://img.shields.io/badge/ruff-passing-brightgreen)](pyproject.toml)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why Auto Curation?](#why-auto-curation)
- [Features](#features)
- [Architecture](#architecture)
- [Supported Institutions](#supported-institutions)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [Support & Sponsor](#support--sponsor-☕)
- [License](#license)

---

## Overview

**Auto Curation** is a production-grade AI ETL pipeline that automatically collects, extracts, and structures exhibition data from 61 of the world's leading art institutions — including MoMA, Tate Modern, Guggenheim, Whitney Museum, and the Venice Biennale.

It runs daily via **GitHub Actions**, uses a **multi-strategy LLM extraction engine** with multi-provider fallback, and enforces strict **no-synthetic-data governance**: every field must come from real source data or remain empty.

This project provides structured global art exhibition data that is otherwise inaccessible at scale — enabling researchers, digital humanities developers, and AI-assisted cultural analytics platforms to build on top of a reliable, continuously updated dataset.

> [!NOTE]
> **Active Development Status:** This project is currently in active development.
> As of June 2026, the database tracks:
> - **11,651+** structured contemporary art exhibitions.
> - **1883 to Present / Ongoing** temporal coverage.
> - **61** world-class art institutions and biennials across **38** global cities (including London, New York, Tokyo, Paris, Beijing, Shanghai, Seoul, Sydney, São Paulo, Venice, and more).

---

## Why Auto Curation?

| Problem | Auto Curation's Solution |
|---------|--------------------------|
| Exhibition data is scattered across 61 different websites with inconsistent formats | Unified schema with 6 adaptive collection strategies |
| LLM extraction is unreliable without fallback | Multi-provider chain: MIMO → Gemini → SiliconFlow |
| Scraped data is often synthetic or hallucinated | Hard governance: zero synthetic fields, missing data left empty |
| Manual maintenance doesn't scale to 61 institutions | Auto-registered parsers — add a file, get a new institution |
| Data quality degrades silently | Daily health checks + GitHub Actions alerts |

---

## Features

- **6 Collection Strategies** — `HTML_LLM` / `CSV_LOCAL` / `CSV_REMOTE` / `REST_API` / `SPARQL` / `ARTWORK_ONLY` — automatically routed per institution
- **61 Registered Institutions** — MoMA, Tate, M+, Whitney, Guggenheim, Venice Biennale, and more across 4 continents
- **Multi-provider LLM Fallback** — MIMO v2.5-pro → Gemini 2.5 Flash → DeepSeek-V3, with Pydantic-validated output
- **Auto-registered Parsers** — `pkgutil`-based scan in `src/sites/__init__.py`; no manual import needed
- **Quality Monitoring** — daily health checks + post-scrape data validation + GitHub Actions alerts (UTC 08:03)
- **Zero Synthetic Data** — all fields sourced from real data; missing values left null, never templated
- **601 Tests, 100% Coverage** — mypy-clean, ruff-passing, production-ready codebase

---

## Architecture

```
[URL Discovery / CSV Read / API Pagination]
         │
         ▼
 [Strategy Dispatcher] ── HTML_LLM ──▶ [HTML Cleaner] ──▶ [LLM Extractor] ──▶ Pydantic Validation
                │                                          │
                ├── CSV_LOCAL   ──▶ [Python Aggregator] ──┤
                ├── CSV_REMOTE  ──▶ [Download + Parse]  ──┤
                ├── REST_API    ──▶ [JSON Mapper]        ──┤
                ├── SPARQL      ──▶ [Wikidata Query]     ──┤
                └── ARTWORK_ONLY ▶ [Artwork Aggregator]  ──┤
                                                          │
                                                          ▼
                                              [Dedup Check — url UNIQUE]
                                                          │
                                                          ▼
                                                   [exhibitions.db]
```

### Core Modules

| File | Responsibility |
|:-----|:---------------|
| `run_collector.py` | CLI entry point, argument parsing |
| `src/scraper.py` | `ExhibitionScraper` orchestrator, strategy dispatch |
| `src/database.py` | SQLite connection + CRUD + unique deduplication |
| `src/llm_parser.py` | Multi-provider fallback chain + Pydantic models |
| `src/sites/base.py` | Parser base class + strategy enums |
| `src/sites/<key>.py` | 61 institution-specific parsers |

---

## Supported Institutions

<details>
<summary>View all 61 institutions</summary>

| Institution | City | Country | Strategy |
|:------------|:-----|:--------|:---------|
| MoMA | New York | 🇺🇸 USA | CSV_REMOTE |
| Tate Modern | London | 🇬🇧 UK | HTML_LLM |
| M+ Museum | Hong Kong | 🇭🇰 HK | HTML_LLM |
| Serpentine Galleries | London | 🇬🇧 UK | HTML_LLM |
| Mori Art Museum | Tokyo | 🇯🇵 Japan | HTML_LLM |
| Art Institute of Chicago | Chicago | 🇺🇸 USA | REST_API |
| Venice Biennale | Venice | 🇮🇹 Italy | HTML_LLM |
| Whitney Museum | New York | 🇺🇸 USA | REST_API |
| Guggenheim | New York | 🇺🇸 USA | HTML_LLM |
| Barbican | London | 🇬🇧 UK | HTML_LLM |
| Pompidou | Paris | 🇫🇷 France | HTML_LLM |
| Palais de Tokyo | Paris | 🇫🇷 France | HTML_LLM |
| Reina Sofía | Madrid | 🇪🇸 Spain | HTML_LLM |
| MAXXI | Rome | 🇮🇹 Italy | HTML_LLM |
| Hamburger Bahnhof | Berlin | 🇩🇪 Germany | HTML_LLM |
| ZKM | Karlsruhe | 🇩🇪 Germany | HTML_LLM |
| Kunsthaus Zürich | Zürich | 🇨🇭 Switzerland | HTML_LLM |
| Fondation Louis Vuitton | Paris | 🇫🇷 France | HTML_LLM |
| Louisiana Museum | Humlebæk | 🇩🇰 Denmark | HTML_LLM |
| National Gallery of Australia | Canberra | 🇦🇺 Australia | HTML_LLM |
| NGV | Melbourne | 🇦🇺 Australia | HTML_LLM |
| MCA Australia | Sydney | 🇦🇺 Australia | HTML_LLM |
| National Gallery of Art | Washington D.C. | 🇺🇸 USA | ARTWORK_ONLY |
| National Gallery Singapore | Singapore | 🇸🇬 Singapore | HTML_LLM |
| MAIIAM | Chiang Mai | 🇹🇭 Thailand | HTML_LLM |
| UCCA | Beijing | 🇨🇳 China | HTML_LLM |
| Leeum | Seoul | 🇰🇷 Korea | HTML_LLM |
| Kanazawa21 | Kanazawa | 🇯🇵 Japan | HTML_LLM |
| MOMAT | Tokyo | 🇯🇵 Japan | HTML_LLM |
| Sydney Biennale | Sydney | 🇦🇺 Australia | HTML_LLM |
| Taipei Biennial | Taipei | 🇹🇼 Taiwan | HTML_LLM |
| São Paulo Biennial | São Paulo | 🇧🇷 Brazil | HTML_LLM |
| Berlin Biennale | Berlin | 🇩🇪 Germany | HTML_LLM |
| Liverpool Biennial | Liverpool | 🇬🇧 UK | HTML_LLM |
| Sharjah Biennial | Sharjah | 🇦🇪 UAE | HTML_LLM |
| Yokohama Triennale | Yokohama | 🇯🇵 Japan | HTML_LLM |
| Documenta | Kassel | 🇩🇪 Germany | HTML_LLM |
| Hirshhorn | Washington D.C. | 🇺🇸 USA | REST_API |
| LACMA | Los Angeles | 🇺🇸 USA | HTML_LLM |
| Brooklyn Museum | New York | 🇺🇸 USA | HTML_LLM |
| New Museum | New York | 🇺🇸 USA | HTML_LLM |
| Hammer Museum | Los Angeles | 🇺🇸 USA | HTML_LLM |
| MCA Chicago | Chicago | 🇺🇸 USA | HTML_LLM |
| Mass MoCA | North Adams | 🇺🇸 USA | HTML_LLM |
| DIA | New York | 🇺🇸 USA | HTML_LLM |
| Whitechapel Gallery | London | 🇬🇧 UK | HTML_LLM |
| Hayward Gallery | London | 🇬🇧 UK | HTML_LLM |
| South London Gallery | London | 🇬🇧 UK | HTML_LLM |
| BALTIC | Gateshead | 🇬🇧 UK | HTML_LLM |
| V&A | London | 🇬🇧 UK | HTML_LLM |
| PSA | Shanghai | 🇨🇳 China | HTML_LLM |
| Astrup Fearnley | Oslo | 🇳🇴 Norway | HTML_LLM |
| Beyeler Foundation | Basel | 🇨🇭 Switzerland | HTML_LLM |
| Pinakothek der Moderne | Munich | 🇩🇪 Germany | HTML_LLM |
| Museum Ludwig | Cologne | 🇩🇪 Germany | HTML_LLM |
| Lenbachhaus | Munich | 🇩🇪 Germany | HTML_LLM |
| KW Institute | Berlin | 🇩🇪 Germany | HTML_LLM |
| Kunsthal Rotterdam | Rotterdam | 🇳🇱 Netherlands | HTML_LLM |
| Whitney Biennial | New York | 🇺🇸 USA | HTML_LLM |
| Nam June Paik Art Center | Yongin | 🇰🇷 Korea | HTML_LLM |
| The Met | New York | 🇺🇸 USA | HTML_LLM |
| Wikidata | Various | 🌐 Global | SPARQL |

*Full status at runtime: `python run_collector.py --list-sites`*
</details>

---

## Installation

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Golden0Voyager/auto-curation.git
cd auto-curation
uv pip install -r requirements.txt
```

---

## Usage

```bash
# List all supported institutions
python run_collector.py --list-sites

# Collect a single institution
python run_collector.py --site mplus

# Collect all institutions
python run_collector.py --all

# Dry run (no database writes)
python run_collector.py --site mori --dry-run --limit 2

# Filter by year
python run_collector.py --site moma --since 1970
```

Data is stored in `exhibitions.db` (SQLite, excluded from version control).

---

## Configuration

Set LLM credentials via environment variables (priority order):

| Variable | Model | Priority |
|:---------|:------|:--------:|
| `XIAOMI_MIMO_API_KEY` | mimo-v2.5-pro | 1 (default) |
| `GEMINI_API_KEY` | gemini-2.5-flash | 2 |
| `SILICONFLOW_API_KEY` | DeepSeek-V3 | 3 |

Optional overrides:
- `MIMO_BASE_URL`
- `GEMINI_BASE_URL`
- `SILICONFLOW_BASE_URL`

---

## Database Schema

| Table | Key Fields |
|:------|:-----------|
| `exhibitions` | `id`, `source`, `title`, `curators` (JSON), `start_date`, `end_date`, `url` (UNIQUE) |
| `artworks` | `id`, `exhibition_id` (FK), `artist_name`, `work_title`, `work_year` |

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Monitor run health
python scripts/monitor_runs.py --alert

# Validate data quality
python scripts/validate_post_scrape.py --all
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

**Adding a new institution in 5 steps:**

1. Create a parser in `src/sites/<key>.py` extending `BaseSiteParser`
2. Set required class attributes: `source`, `city`, `parser_key`, `list_url`
3. Declare `strategy = ParserStrategy.XXX`
4. Parser is **auto-registered** — no manual import needed
5. Add tests and open a PR

**Data Quality Rule — No Synthetic Data:**
All fields must come from real source data. Missing values must remain empty — never filled with templates or LLM guesses.

---

## Support & Sponsor ☕

If this project, tool, or dataset is helpful to you, please consider supporting my work to keep the servers running and the data updated!

👉 **[Support me on Ko-fi](https://ko-fi.com/golden_voyager)**

---

## License

[Apache-2.0 License](LICENSE) © 2026 Haining Yu (Golden0Voyager)

---

## Acknowledgements

- [MoMA GitHub](https://github.com/MuseumofModernArt/collection) — Open exhibition & collection dataset
- [Art Institute of Chicago](https://github.com/art-institute-of-chicago/data-tools) — Open access API & data tools
- [Scrapling](https://github.com/D4Vinci/Scrapling) — Underlying Fetcher / StealthyFetcher
- [Pydantic](https://docs.pydantic.dev/) — Data model validation
- [auto_hub](https://github.com/Golden0Voyager/auto-hub) — Shared LLM provider chain
