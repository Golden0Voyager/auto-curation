#!/usr/bin/env python3
"""Batch scrape orchestrator — 按 tier 分组批量采集展览数据。

按优先级分组执行 parser，支持延迟、重试、结果报告。

Usage:
    python scripts/batch_scrape.py                    # 运行所有 tier
    python scripts/batch_scrape.py --tier E           # 只运行 Tier E
    python scripts/batch_scrape.py --tier A B         # 运行 Tier A + B
    python scripts/batch_scrape.py --site tate mori   # 运行指定 parser
    python scripts/batch_scrape.py --delay 10         # parser 间延迟 10s
    python scripts/batch_scrape.py --retry-failed     # 失败后重试一次
    python scripts/batch_scrape.py --dry-run          # 模拟运行
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Parser tier definitions
TIERS: dict[str, list[str]] = {
    "E": ["met", "whitney", "wikidata"],
    "A": [
        "mca_australia", "louisiana", "lenbachhaus", "maxxi", "pompidou",
        "saopaulo_biennial", "barbican", "sydney_biennale", "yokohama_triennale",
        "kunsthaus", "kw_institute",
    ],
    "B": [
        "berlin_biennale", "ucca", "maiiam", "psa", "brooklyn_museum",
        "ngv", "njpac", "liverpool_biennial", "beyeler", "whitney_biennial",
        "venice_biennale", "sharjah_biennale", "documenta", "momat",
        "hamburger_bahnhof", "vam",
    ],
    "C": [
        "mca_chicago", "national_gallery_sg", "new_museum", "kunsthal",
        "reina_sofia", "palaistokyo", "hammer_museum", "zkm",
        "astrup_fearnley", "baltic",
    ],
    "D": [
        "museum_ludwig", "taipei_biennale", "kanazawa21",
        "south_london_gallery", "leeum", "pinakothek",
    ],
}

# Parsers that already have full/near-full data (skip in batch)
SKIP_KEYS = {"aic", "moma", "serpentine", "tate", "mori", "mplus"}

# Blocked parsers (confirmed unfixable)
BLOCKED_KEYS = {"dia", "flv", "guggenheim", "hayward", "hirshhorn", "lacma", "mass_moca", "whitechapel"}


def _parse_stats(output: str) -> dict[str, int]:
    """Extract scrape stats from run_collector.py output."""
    stats = {"discovered": 0, "parsed": 0, "saved": 0, "skipped": 0, "failed": 0}
    for line in output.splitlines():
        for key in stats:
            # Match Chinese format: "发现 URL数  : 16" or "存入数据库  : 13"
            # Also match dict format: "'discovered': 16"
            patterns = [
                rf"'{key}':\s*(\d+)",
                rf'"{key}":\s*(\d+)',
            ]
            for pat in patterns:
                m = re.search(pat, line)
                if m:
                    stats[key] = int(m.group(1))
                    break
    return stats


def run_parser(site_key: str, timeout: int = 600, dry_run: bool = False) -> dict[str, Any]:
    """Run a single parser via run_collector.py."""
    cmd = [sys.executable, str(PROJECT_ROOT / "run_collector.py"), "--site", site_key, "--concurrent"]
    if dry_run:
        cmd.append("--dry-run")

    start = time.time()
    result: dict[str, Any] = {
        "site": site_key,
        "started_at": datetime.now().isoformat(),
        "success": False,
        "stats": {},
        "duration_s": 0,
        "error": None,
    }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        elapsed = time.time() - start
        result["duration_s"] = round(elapsed, 1)
        result["exit_code"] = proc.returncode

        combined = proc.stdout + "\n" + proc.stderr
        result["stats"] = _parse_stats(combined)

        if proc.returncode == 0:
            result["success"] = True
        else:
            # Extract last error line
            for line in reversed(proc.stderr.splitlines()):
                if "Error" in line or "ERROR" in line:
                    result["error"] = line.strip()[:200]
                    break
            if not result["error"]:
                result["error"] = f"Exit code {proc.returncode}"

    except subprocess.TimeoutExpired:
        result["duration_s"] = timeout
        result["error"] = f"Timeout after {timeout}s"
    except Exception as e:
        result["duration_s"] = round(time.time() - start, 1)
        result["error"] = str(e)[:200]

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch scrape orchestrator")
    parser.add_argument("--tier", nargs="+", choices=list(TIERS.keys()), help="Tiers to run")
    parser.add_argument("--site", nargs="+", help="Specific parser keys to run")
    parser.add_argument("--delay", type=int, default=5, help="Delay between parsers (seconds)")
    parser.add_argument("--timeout", type=int, default=600, help="Per-parser timeout (seconds)")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed parsers once")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing to DB")
    parser.add_argument("--output", help="Output JSON path (default: docs/plans/batch-scrape-{ts}.json)")
    args = parser.parse_args()

    # Determine which parsers to run
    if args.site:
        run_keys = args.site
    elif args.tier:
        run_keys = []
        for t in args.tier:
            run_keys.extend(TIERS[t])
    else:
        run_keys = []
        for t in ["E", "A", "B", "C", "D"]:
            run_keys.extend(TIERS[t])

    # Filter out skipped and blocked
    run_keys = [k for k in run_keys if k not in SKIP_KEYS and k not in BLOCKED_KEYS]

    print(f"Batch scrape: {len(run_keys)} parsers | delay={args.delay}s | timeout={args.timeout}s")
    if args.dry_run:
        print("[DRY-RUN MODE]")
    print(f"Parsers: {', '.join(run_keys)}")
    print("=" * 60)

    results: list[dict[str, Any]] = []
    failed_keys: list[str] = []

    for i, key in enumerate(run_keys, 1):
        print(f"\n[{i}/{len(run_keys)}] Scraping {key}...")
        r = run_parser(key, timeout=args.timeout, dry_run=args.dry_run)
        results.append(r)

        status = "OK" if r["success"] else "FAIL"
        stats = r["stats"]
        print(f"  {status} | {r['duration_s']}s | discovered={stats.get('discovered', 0)} "
              f"saved={stats.get('saved', 0)} failed={stats.get('failed', 0)}")

        if not r["success"]:
            failed_keys.append(key)
            print(f"  Error: {r['error']}")

        # Delay between parsers (skip after last)
        if i < len(run_keys) and args.delay > 0:
            time.sleep(args.delay)

    # Retry failed parsers
    if args.retry_failed and failed_keys:
        print(f"\n{'=' * 60}")
        print(f"Retrying {len(failed_keys)} failed parsers...")
        for key in failed_keys:
            print(f"\n[RETRY] {key}...")
            r = run_parser(key, timeout=args.timeout * 2, dry_run=args.dry_run)
            # Update the original result
            for orig in results:
                if orig["site"] == key:
                    orig["retry"] = r
                    if r["success"]:
                        orig["success"] = True
                        orig["stats"] = r["stats"]
                        orig["error"] = None
                    break
            status = "OK" if r["success"] else "FAIL"
            print(f"  {status} | {r['duration_s']}s")

    # Summary
    total_ok = sum(1 for r in results if r["success"])
    total_fail = sum(1 for r in results if not r["success"])
    total_saved = sum(r["stats"].get("saved", 0) for r in results)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {total_ok} ok / {total_fail} failed / {total_saved} exhibitions saved")

    if total_fail > 0:
        print("Failed parsers:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['site']}: {r['error']}")

    # Save results
    output_path = args.output or str(
        PROJECT_ROOT / "docs" / "plans" / f"batch-scrape-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "dry_run": args.dry_run,
            "total_parsers": len(run_keys),
            "ok": total_ok,
            "failed": total_fail,
            "exhibitions_saved": total_saved,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
