#!/usr/bin/env python3
"""Phase 4 Task 1: 全量 Smoke Test — 验证所有 parser 的 URL 发现能力"""

import subprocess
import concurrent.futures
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 64 registered sites (from --list-sites output)
SITES = [
    "aic", "astrup_fearnley", "baltic", "barbican", "berlin_biennale",
    "beyeler", "brooklyn_museum", "dia", "documenta", "flv",
    "guggenheim", "gwangju_biennale", "hamburger_bahnhof", "hammer_museum",
    "hayward", "hirshhorn", "istanbul_biennale", "kanazawa21", "kunsthal",
    "kunsthaus", "kw_institute", "lacma", "leeum", "lenbachhaus",
    "liverpool_biennial", "louisiana", "lyon_biennale", "maiiam", "mass_moca",
    "maxxi", "mca_australia", "mca_chicago", "met", "mmcaseoul", "moma",
    "momat", "mori", "mplus", "museum_ludwig", "national_gallery_sg",
    "new_museum", "nga", "ngv", "njpac", "palaistokyo", "pinakothek",
    "pompidou", "psa", "reina_sofia", "saopaulo_biennial", "serpentine",
    "sharjah_biennale", "south_london_gallery", "sydney_biennale",
    "taipei_biennale", "tate", "ucca", "venice_biennale", "whitechapel",
    "whitney", "whitney_biennial", "wikidata", "yokohama_triennale", "zkm"
]

MAX_WORKERS = 8
TIMEOUT_SECONDS = 45


def run_single_smoke(site: str) -> dict:
    """Run smoke test for a single site."""
    start = time.time()
    result = {
        "site": site,
        "status": "unknown",
        "urls_found": 0,
        "error": None,
        "elapsed": 0.0,
    }

    cmd = [
        sys.executable, "run_collector.py",
        "--site", site,
        "--limit", "1",
        "--dry-run"
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)

        stdout = proc.stdout
        stderr = proc.stderr
        combined = stdout + "\n" + stderr

        # Extract URL count from output (supports Chinese & English formats)
        url_count = 0
        for line in combined.splitlines():
            # Chinese format: "发现 URL数  : 15"
            if "发现 URL" in line or "发现URL" in line:
                try:
                    url_count = int(line.split(":")[-1].strip())
                except (ValueError, IndexError):
                    pass
            # English format: "Discovered 15 URLs"
            elif "Discovered" in line and "URLs" in line:
                try:
                    url_count = int(line.split("Discovered")[1].split("URLs")[0].strip())
                except (ValueError, IndexError):
                    pass
            # Log dict format: "'discovered': 15"
            elif "'discovered':" in line:
                try:
                    url_count = int(line.split("'discovered':")[1].split(",")[0].strip())
                except (ValueError, IndexError):
                    pass
            elif '"discovered":' in line:
                try:
                    url_count = int(line.split('"discovered":')[1].split(",")[0].strip())
                except (ValueError, IndexError):
                    pass

        # Determine status
        if proc.returncode != 0:
            result["status"] = "FAIL"
            result["error"] = (stderr or stdout)[:500]
        elif url_count == 0:
            # Check for known blockers
            if "403" in combined:
                result["status"] = "BLOCKED_403"
            elif "SSL" in combined or "CERTIFICATE" in combined.upper():
                result["status"] = "BLOCKED_SSL"
            elif "timeout" in combined.lower():
                result["status"] = "TIMEOUT"
            else:
                result["status"] = "ZERO_URLS"
            result["error"] = (stderr or stdout)[:500]
        elif url_count >= 5:
            result["status"] = "PASS"
        else:
            result["status"] = "WARN"  # 1-4 URLs

        result["urls_found"] = url_count

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["elapsed"] = round(time.time() - start, 2)
        result["error"] = f"Timed out after {TIMEOUT_SECONDS}s"
    except Exception as e:
        result["status"] = "ERROR"
        result["elapsed"] = round(time.time() - start, 2)
        result["error"] = str(e)[:500]

    return result


def categorize(result: dict) -> str:
    status = result["status"]
    urls = result["urls_found"]

    if status == "PASS":
        return "green"
    if status == "WARN":
        return "yellow"
    if status in ("FAIL", "ZERO_URLS", "BLOCKED_403", "BLOCKED_SSL", "TIMEOUT", "ERROR"):
        return "red"
    return "red"


def main():
    print(f"Phase 4 Smoke Test started at {datetime.now().isoformat()}")
    print(f"Sites: {len(SITES)} | Workers: {MAX_WORKERS} | Timeout: {TIMEOUT_SECONDS}s")
    print("=" * 60)

    results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_site = {
            executor.submit(run_single_smoke, site): site
            for site in SITES
        }
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                res = future.result()
                results.append(res)
                completed += 1
                cat = categorize(res)
                print(
                    f"[{completed:2d}/{len(SITES)}] "
                    f"{res['site']:20s} | "
                    f"{res['status']:12s} | "
                    f"URLs: {res['urls_found']:3d} | "
                    f"{res['elapsed']:5.1f}s | "
                    f"{cat}"
                )
            except Exception as e:
                print(f"[{completed:2d}/{len(SITES)}] {site:20s} | EXCEPTION: {e}")
                results.append({
                    "site": site,
                    "status": "EXCEPTION",
                    "urls_found": 0,
                    "error": str(e),
                    "elapsed": 0,
                })

    # Sort by site name
    results.sort(key=lambda r: r["site"])

    # Summary
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
    report_path = Path("docs/plans/smoke-test-report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

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
        err = r.get("error", "").replace("\n", " ").strip()[:100]
        lines.append(f"- `{r['site']}` — {r['status']} — {err}")

    lines.append("\n## Raw Data\n")
    lines.append("```json")
    lines.append(json.dumps(results, indent=2, ensure_ascii=False))
    lines.append("```\n")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {report_path}")

    # Save raw JSON for downstream tasks
    json_path = Path("docs/plans/smoke-test-results.json")
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Raw data saved to: {json_path}")


if __name__ == "__main__":
    main()
