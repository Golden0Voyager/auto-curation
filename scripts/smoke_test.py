#!/usr/bin/env python3
"""Phase 4 Task 1: 全量 Smoke Test — 验证所有 parser 的 URL 发现能力

直接导入模式（替代旧版 subprocess 模式），避免环境隔离导致的误判。
"""

import concurrent.futures
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scraper import ExhibitionScraper  # noqa: E402
from src.sites import SITES  # noqa: E402

MAX_WORKERS = 4
TIMEOUT_SECONDS = 90


def run_single_smoke(site_key: str) -> dict[str, Any]:
    """Run smoke test for a single site using direct imports."""
    start = time.time()
    result: dict[str, Any] = {
        "site": site_key,
        "status": "unknown",
        "urls_found": 0,
        "error": None,
        "elapsed": 0.0,
    }

    # Skip known blocked sites immediately
    parser = SITES.get(site_key)
    blocked_status = getattr(parser, "status", None)
    if blocked_status:
        result["status"] = blocked_status
        result["error"] = f"Parser declared as {blocked_status}"
        return result

    scraper = None
    try:
        scraper = ExhibitionScraper()
        stats = scraper.scrape_site(site_key, limit=1, dry_run=True)
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)

        if "error" in stats:
            result["status"] = "FAIL"
            result["error"] = stats["error"]
            return result

        url_count = stats.get("discovered", 0)
        result["urls_found"] = url_count

        # For non-HTML_LLM strategies, limit=1 naturally caps results to 1.
        # Any positive count means the pipeline works.
        strategy = getattr(parser, "strategy", None)
        is_html = strategy is None or strategy.name == "HTML_LLM"

        if url_count >= 5:
            result["status"] = "PASS"
        elif url_count > 0 and not is_html:
            result["status"] = "PASS"
        elif url_count > 0:
            result["status"] = "WARN"
        else:
            # Check for known blockers in error context
            err_str = str(stats)
            if "403" in err_str:
                result["status"] = "BLOCKED_403"
            elif "SSL" in err_str or "CERTIFICATE" in err_str.upper():
                result["status"] = "BLOCKED_SSL"
            else:
                result["status"] = "ZERO_URLS"

    except Exception as exc:
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)
        err_msg = str(exc)
        if "403" in err_msg:
            result["status"] = "BLOCKED_403"
        elif "SSL" in err_msg or "CERTIFICATE" in err_msg.upper():
            result["status"] = "BLOCKED_SSL"
        elif "timeout" in err_msg.lower():
            result["status"] = "TIMEOUT"
        else:
            result["status"] = "FAIL"
        result["error"] = err_msg[:500]
    finally:
        if scraper:
            try:
                scraper.close()
            except Exception:
                pass

    return result


def categorize(result: dict) -> str:
    status = result["status"]
    if status == "PASS":
        return "green"
    if status == "WARN":
        return "yellow"
    return "red"


def main():
    sites = sorted(SITES.keys())
    print(f"Smoke Test started at {datetime.now().isoformat()}")
    print(f"Sites: {len(sites)} | Workers: {MAX_WORKERS} | Mode: direct import")
    print("=" * 60)

    results: list[dict[str, Any]] = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_site = {
            executor.submit(run_single_smoke, site): site
            for site in sites
        }
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                res = future.result(timeout=TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                completed += 1
                print(
                    f"[{completed:2d}/{len(sites)}] "
                    f"{site:20s} | TIMEOUT       | URLs:   0 | {TIMEOUT_SECONDS:5.1f}s | red"
                )
                results.append({
                    "site": site,
                    "status": "TIMEOUT",
                    "urls_found": 0,
                    "error": f"Timed out after {TIMEOUT_SECONDS}s",
                    "elapsed": TIMEOUT_SECONDS,
                })
                continue

            results.append(res)
            completed += 1
            cat = categorize(res)
            print(
                f"[{completed:2d}/{len(sites)}] "
                f"{res['site']:20s} | "
                f"{res['status']:12s} | "
                f"URLs: {res['urls_found']:3d} | "
                f"{res['elapsed']:5.1f}s | "
                f"{cat}"
            )

    # Sort by site name
    results.sort(key=lambda r: r["site"])

    categories = {"green": [], "yellow": [], "red": []}
    for r in results:
        cat = categorize(r)
        categories[cat].append(r)

    total = len(results)
    green = len(categories["green"])
    yellow = len(categories["yellow"])
    red = len(categories["red"])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total:   {total:2d}")
    print(f"Green:   {green:2d} ({green / total * 100:.0f}%) — >=5 URLs")
    print(f"Yellow:  {yellow:2d} ({yellow / total * 100:.0f}%) — 1-4 URLs")
    print(f"Red:     {red:2d} ({red / total * 100:.0f}%) — 0 URLs or error")

    # Markdown report
    report_dir = Path("docs/plans")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "smoke-test-report.md"

    lines = [
        "# Smoke Test Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"\n## Summary\n",
        f"| Metric | Count | Percentage |",
        f"|--------|------:|------------|",
        f"| Total  | {total} | 100% |",
        f"| Green  | {green} | {green / total * 100:.1f}% |",
        f"| Yellow | {yellow} | {yellow / total * 100:.1f}% |",
        f"| Red    | {red} | {red / total * 100:.1f}% |",
        "\n## Green (>=5 URLs)\n",
    ]

    for r in categories["green"]:
        lines.append(f"- `{r['site']}` — {r['urls_found']} URLs in {r['elapsed']}s")

    lines.append("\n## Yellow (1-4 URLs)\n")
    for r in categories["yellow"]:
        lines.append(f"- `{r['site']}` — {r['urls_found']} URLs in {r['elapsed']}s")

    lines.append("\n## Red (0 URLs or Error)\n")
    for r in categories["red"]:
        err = (r.get("error") or "").replace("\n", " ").strip()[:100]
        lines.append(f"- `{r['site']}` — {r['status']} — {err}")

    lines.append("\n## Raw Data\n")
    lines.append("```json")
    lines.append(json.dumps(results, indent=2, ensure_ascii=False))
    lines.append("```\n")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")

    json_path = report_dir / "smoke-test-results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Raw data saved to: {json_path}")


if __name__ == "__main__":
    main()
