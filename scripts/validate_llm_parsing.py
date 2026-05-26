#!/usr/bin/env python
"""Phase 4 Task 2: 有限深度 LLM 解析验证

对 Green/Yellow 状态的 HTML_LLM parser，每家抽样 3 个 URL，
执行真实 LLM 解析并验证输出质量。

Usage:
    python scripts/validate_llm_parsing.py --sample 10
    python scripts/validate_llm_parsing.py --site tate --limit 3
    python scripts/validate_llm_parsing.py --all
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, ".")

from src.scraper import ExhibitionScraper
from src.sites import SITES
from src.sites.base import ParserStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("validate_llm")


def validate_exhibition(data: Dict[str, Any]) -> List[str]:
    """Return list of quality issues found in parsed exhibition data."""
    issues = []

    # 1. Title validation
    title = data.get("title", "")
    if not title or len(title.strip()) < 3:
        issues.append("title missing or too short")
    elif title.lower() in ("home", "homepage", "menu", "untitled", "exhibition", "exhibitions"):
        issues.append(f"title looks like noise: '{title}'")

    # 2. Date format validation
    for field in ("start_date", "end_date"):
        val = data.get(field)
        if val and not _is_valid_date(val):
            issues.append(f"{field} invalid format: '{val}'")

    # 3. Curators validation
    curators = data.get("curators")
    if curators is not None and not isinstance(curators, list):
        issues.append(f"curators is not a list: {type(curators).__name__}")

    # 4. Concept validation
    concept = data.get("concept", "")
    if concept and len(concept.strip()) < 10:
        issues.append("concept too short (< 10 chars)")

    # 5. Artworks validation
    artworks = data.get("artworks")
    if artworks is not None and not isinstance(artworks, list):
        issues.append(f"artworks is not a list: {type(artworks).__name__}")

    # 6. City validation
    city = data.get("city", "")
    if not city:
        issues.append("city is missing")

    return issues


def _is_valid_date(val: str) -> bool:
    """Check if date string matches YYYY-MM-DD, YYYY-MM, or YYYY."""
    if not val:
        return True
    return bool(re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", val))


def test_parser(scraper: ExhibitionScraper, key: str, limit: int) -> Dict[str, Any]:
    """Test a single parser with up to `limit` URLs."""
    parser = SITES[key]
    strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)

    if strategy != ParserStrategy.HTML_LLM:
        return {
            "parser_key": key,
            "source": parser.source,
            "strategy": strategy.value,
            "skipped": True,
            "reason": "non-HTML_LLM strategy",
        }

    try:
        urls = parser.get_exhibition_urls(scraper.client)
    except Exception as e:
        return {
            "parser_key": key,
            "source": parser.source,
            "urls_found": 0,
            "urls_tested": 0,
            "errors": [f"URL discovery failed: {e}"],
            "results": [],
        }

    if not urls:
        return {
            "parser_key": key,
            "source": parser.source,
            "urls_found": 0,
            "urls_tested": 0,
            "errors": [],
            "results": [],
        }

    sample_urls = urls[:limit]
    results = []
    errors = []

    for url in sample_urls:
        try:
            response = scraper.client.get(url, timeout=30.0)
            response.raise_for_status()
            clean_text = parser.clean_html(response.text)

            if not clean_text or len(clean_text.strip()) < 100:
                results.append({
                    "url": url,
                    "title": None,
                    "artworks_count": 0,
                    "issues": ["content too short after cleaning"],
                })
                continue

            parsed = scraper.parser.parse_exhibition_text(
                clean_text, parser.source, parser.city
            )
            if not parsed:
                results.append({
                    "url": url,
                    "title": None,
                    "artworks_count": 0,
                    "issues": ["LLM returned None"],
                })
                continue

            issues = validate_exhibition(parsed)
            results.append({
                "url": url,
                "title": parsed.get("title", ""),
                "start_date": parsed.get("start_date"),
                "end_date": parsed.get("end_date"),
                "curators_count": len(parsed.get("curators") or []),
                "artworks_count": len(parsed.get("artworks") or []),
                "concept_length": len(parsed.get("concept") or ""),
                "issues": issues,
            })

        except Exception as e:
            results.append({
                "url": url,
                "title": None,
                "artworks_count": 0,
                "issues": [f"exception: {e}"],
            })
            errors.append(str(e))

    return {
        "parser_key": key,
        "source": parser.source,
        "urls_found": len(urls),
        "urls_tested": len(sample_urls),
        "errors": errors,
        "results": results,
    }


def write_markdown_report(all_results: List[Dict[str, Any]], path: str) -> None:
    """Write validation results as a Markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# LLM Parsing Validation Report\n\n")
        f.write(f"Generated: {now}\n\n")

        total_tested = sum(r["urls_tested"] for r in all_results if not r.get("skipped"))
        total_issues = sum(
            len(u["issues"])
            for r in all_results
            if not r.get("skipped")
            for u in r["results"]
        )
        f.write(f"## Summary\n\n")
        f.write(f"- Total parsers tested: {len([r for r in all_results if not r.get('skipped')])}\n")
        f.write(f"- Total URLs tested: {total_tested}\n")
        f.write(f"- Total issues found: {total_issues}\n\n")

        for r in all_results:
            if r.get("skipped"):
                continue

            issues_count = sum(len(u["issues"]) for u in r["results"])
            if issues_count == 0:
                status = "PASS"
            elif issues_count <= 2:
                status = "WARN"
            else:
                status = "FAIL"

            f.write(f"## {r['parser_key']} ({r['source']}) — {status}\n\n")
            f.write(f"- URLs found: {r['urls_found']}\n")
            f.write(f"- URLs tested: {r['urls_tested']}\n")
            f.write(f"- Issues: {issues_count}\n\n")

            for u in r["results"]:
                f.write(f"### {u['url']}\n")
                f.write(f"- **Title**: `{u.get('title') or 'N/A'}`\n")
                f.write(f"- **Dates**: {u.get('start_date') or '?'} → {u.get('end_date') or '?'}\n")
                f.write(f"- **Curators**: {u.get('curators_count', 'N/A')}\n")
                f.write(f"- **Artworks**: {u.get('artworks_count', 'N/A')}\n")
                f.write(f"- **Concept length**: {u.get('concept_length', 'N/A')} chars\n")
                if u["issues"]:
                    f.write("- **Issues**:\n")
                    for issue in u["issues"]:
                        f.write(f"  - {issue}\n")
                else:
                    f.write("- **No issues detected**\n")
                f.write("\n")

            if r["errors"]:
                f.write("**Other errors**:\n")
                for err in r["errors"]:
                    f.write(f"- {err}\n")
                f.write("\n")


def main():
    arg_parser = argparse.ArgumentParser(description="Phase 4 Task 2: LLM parsing validation")
    arg_parser.add_argument("--site", type=str, help="Test a single parser")
    arg_parser.add_argument("--sample", type=int, help="Randomly sample N parsers")
    arg_parser.add_argument("--all", action="store_true", help="Test all HTML_LLM parsers")
    arg_parser.add_argument("--limit", type=int, default=3, help="Max URLs per parser (default: 3)")
    arg_parser.add_argument("--output", type=str, default=None, help="Output markdown path")
    args = arg_parser.parse_args()

    if not (args.site or args.sample or args.all):
        print("Usage: python scripts/validate_llm_parsing.py --site tate --limit 3")
        print("       python scripts/validate_llm_parsing.py --sample 10")
        print("       python scripts/validate_llm_parsing.py --all")
        sys.exit(1)

    scraper = ExhibitionScraper("exhibitions.db")

    # Determine which parsers to test
    candidates = []
    for key, parser in sorted(SITES.items()):
        strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
        if strategy != ParserStrategy.HTML_LLM:
            continue
        candidates.append(key)

    if args.site:
        keys = [args.site]
    elif args.sample:
        import random
        random.seed(42)
        keys = random.sample(candidates, min(args.sample, len(candidates)))
    else:
        keys = candidates

    all_results = []
    for key in keys:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {key}")
        result = test_parser(scraper, key, args.limit)
        all_results.append(result)

        if result.get("skipped"):
            logger.info(f"Skipped: {result['reason']}")
        else:
            issues = sum(len(u["issues"]) for u in result["results"])
            logger.info(
                f"Result: {result['urls_tested']} URLs tested, {issues} issues, "
                f"{len(result['errors'])} errors"
            )

    scraper.close()

    # Write report
    if args.output:
        report_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"docs/plans/llm-validation-report-{ts}.md"

    write_markdown_report(all_results, report_path)
    logger.info(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
