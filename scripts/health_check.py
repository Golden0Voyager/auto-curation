#!/usr/bin/env python3
"""Health Check — 快速验证所有 parser 的可用性并生成报告。

遍历所有已注册的 parser，每家执行 --limit 1 --dry-run，
记录 URL 发现数、耗时、HTTP 状态，并输出 Markdown 报告。

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --db exhibitions.db
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ExhibitionDatabase  # noqa: E402
from src.sites import SITES  # noqa: E402
from src.sites.base import ParserStrategy  # noqa: E402

MAX_WORKERS = 2
TIMEOUT_SECONDS = 90


def _extract_url_count(combined_output: str) -> int:
    """从 scraper 输出中提取发现的 URL 数量。"""
    for line in combined_output.splitlines():
        if "发现 URL" in line or "发现URL" in line:
            try:
                return int(line.split(":")[-1].strip())
            except (ValueError, IndexError):
                continue
        if "Discovered" in line and "URLs" in line:
            try:
                return int(line.split("Discovered")[1].split("URLs")[0].strip())
            except (ValueError, IndexError):
                continue
        if "'discovered':" in line:
            try:
                return int(line.split("'discovered':")[1].split(",")[0].strip())
            except (ValueError, IndexError):
                continue
        if '"discovered":' in line:
            try:
                return int(line.split('"discovered":')[1].split(",")[0].strip())
            except (ValueError, IndexError):
                continue
    return 0


def _extract_http_status(combined_output: str) -> int | None:
    """尝试从 httpx 日志中提取最近的 HTTP 状态码。"""
    status: int | None = None
    for line in combined_output.splitlines():
        if "HTTP Request:" in line:
            # e.g. 'HTTP Request: GET https://... "HTTP/1.1 403 Forbidden"'
            parts = line.split('"')
            for part in parts:
                if part.startswith("HTTP/") and len(part.split()) >= 2:
                    try:
                        status = int(part.split()[1])
                    except (ValueError, IndexError):
                        continue
    return status


def run_single(site_key: str, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    """对单个 parser 执行健康检查。"""
    start = time.time()
    result: dict[str, Any] = {
        "site": site_key,
        "status": "unknown",
        "urls_found": 0,
        "http_status": None,
        "elapsed": 0.0,
        "error": None,
    }

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "run_collector.py"),
        "--site", site_key,
        "--limit", "1",
        "--dry-run",
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)

        combined = proc.stdout + "\n" + proc.stderr
        url_count = _extract_url_count(combined)
        http_status = _extract_http_status(combined)
        result["urls_found"] = url_count
        result["http_status"] = http_status

        parser = SITES.get(site_key)
        has_status = getattr(parser, "status", None)

        if has_status:
            result["status"] = "SKIPPED"
            result["error"] = has_status
        elif proc.returncode != 0:
            result["status"] = "FAIL"
            result["error"] = (proc.stderr or proc.stdout)[:300]
        elif url_count == 0:
            if "403" in combined:
                result["status"] = "BLOCKED_403"
            elif "SSL" in combined or "CERTIFICATE" in combined.upper():
                result["status"] = "BLOCKED_SSL"
            elif "timeout" in combined.lower() or "timed out" in combined.lower():
                result["status"] = "TIMEOUT"
            elif "Playwright is required" in combined:
                result["status"] = "NEEDS_PLAYWRIGHT"
            else:
                result["status"] = "ZERO_URLS"
            result["error"] = (proc.stderr or proc.stdout)[:300]
        else:
            result["status"] = "PASS"

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["elapsed"] = round(time.time() - start, 2)
        result["error"] = f"Timed out after {timeout}s"
    except Exception as exc:
        result["status"] = "ERROR"
        result["elapsed"] = round(time.time() - start, 2)
        result["error"] = str(exc)[:300]

    return result


def _color(status: str) -> str:
    """终端颜色码（仅在支持时显示）。"""
    mapping = {
        "PASS": "\033[32m",
        "WARN": "\033[33m",
        "FAIL": "\033[31m",
        "BLOCKED_403": "\033[31m",
        "BLOCKED_SSL": "\033[31m",
        "TIMEOUT": "\033[31m",
        "ZERO_URLS": "\033[31m",
        "NEEDS_PLAYWRIGHT": "\033[31m",
        "ERROR": "\033[31m",
        "SKIPPED": "\033[36m",
    }
    reset = "\033[0m"
    return f"{mapping.get(status, '')}{status:15s}{reset}"


def check_database(db_path: str) -> dict[str, Any] | None:
    """检查数据库健康状态。"""
    if not Path(db_path).exists():
        return None

    try:
        db = ExhibitionDatabase(db_path)
        total_ex = db.count_exhibitions()
        total_art = db.count_artworks()

        conn = db._get_connection()
        cursor = conn.cursor()

        # Missing titles
        cursor.execute(
            "SELECT COUNT(*) FROM exhibitions WHERE title IS NULL OR title = ''"
        )
        missing_title = cursor.fetchone()[0]

        # Missing start_date
        cursor.execute("SELECT COUNT(*) FROM exhibitions WHERE start_date IS NULL")
        missing_date = cursor.fetchone()[0]

        # Missing concept
        cursor.execute(
            "SELECT COUNT(*) FROM exhibitions WHERE concept IS NULL OR concept = ''"
        )
        missing_concept = cursor.fetchone()[0]

        # Source distribution
        cursor.execute(
            "SELECT parser_key, COUNT(*) FROM exhibitions GROUP BY parser_key ORDER BY 2 DESC"
        )
        source_dist = cursor.fetchall()

        # Last scraper runs
        cursor.execute("""
            SELECT parser_key, started_at, finished_at, urls_discovered, urls_parsed,
                   exhibitions_saved, exhibitions_failed, error_message
            FROM scraper_runs
            WHERE id IN (
                SELECT MAX(id) FROM scraper_runs GROUP BY parser_key
            )
        """)
        last_runs = {row["parser_key"]: dict(row) for row in cursor.fetchall()}
        conn.close()

        return {
            "exhibitions": total_ex,
            "artworks": total_art,
            "missing_title": missing_title,
            "missing_date": missing_date,
            "missing_concept": missing_concept,
            "source_distribution": source_dist,
            "last_runs": last_runs,
        }
    except Exception as exc:
        return {"error": str(exc)}


def generate_report(
    results: list[dict[str, Any]],
    db_health: dict[str, Any] | None,
    out_dir: Path,
) -> Path:
    """生成 Markdown 健康报告。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"health-check-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    categories: dict[str, list[dict[str, Any]]] = {
        "green": [],
        "cyan": [],
        "red": [],
    }
    for r in results:
        if r["status"] == "PASS":
            cat = "green"
        elif r["status"] == "SKIPPED":
            cat = "cyan"
        else:
            cat = "red"
        categories[cat].append(r)

    total = len(results)
    green = len(categories["green"])
    cyan = len(categories["cyan"])
    red = len(categories["red"])

    lines: list[str] = [
        "# Health Check Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        "\n## Summary\n",
        "| Metric | Count | Percentage |",
        "|--------|------:|------------|",
        f"| Total   | {total} | 100% |",
        f"| PASS    | {green} | {green / total * 100:.1f}% |",
        f"| SKIPPED | {cyan} | {cyan / total * 100:.1f}% |",
        f"| FAIL    | {red} | {red / total * 100:.1f}% |",
    ]

    # Database health section
    if db_health:
        lines.extend([
            "\n## Database Health\n",
            f"- **Exhibitions**: {db_health.get('exhibitions', 'N/A')}",
            f"- **Artworks**: {db_health.get('artworks', 'N/A')}",
        ])
        if "error" not in db_health:
            total_ex = db_health.get("exhibitions", 0) or 1
            lines.extend([
                f"- **Missing title**: {db_health['missing_title']} ({db_health['missing_title'] / total_ex * 100:.1f}%)",
                f"- **Missing start_date**: {db_health['missing_date']} ({db_health['missing_date'] / total_ex * 100:.1f}%)",
                f"- **Missing concept**: {db_health['missing_concept']} ({db_health['missing_concept'] / total_ex * 100:.1f}%)",
                "\n### Source Distribution\n",
                "| Source | Count |",
                "|--------|------:|",
            ])
            for src, cnt in db_health.get("source_distribution", []):
                lines.append(f"| {src} | {cnt} |")
        else:
            lines.append(f"- **Error**: {db_health['error']}")

    # Last run info from db_health
    last_runs = db_health.get("last_runs", {}) if db_health else {}

    # Detailed results table
    lines.extend([
        "\n## Detailed Results\n",
        "| Site | Status | URLs | HTTP | Time | Last Run | Notes |",
        "|------|--------|-----:|------|-----:|----------|-------|",
    ])
    for r in sorted(results, key=lambda x: x["site"]):
        http = str(r["http_status"]) if r["http_status"] else "—"
        note = (r.get("error") or "").replace("\n", " ").strip()[:60]
        run_info = last_runs.get(r["site"])
        if run_info:
            started = run_info.get("started_at", "")[:16]  # YYYY-MM-DD HH:MM
            saved = run_info.get("exhibitions_saved", 0)
            last_run_str = f"{started} ({saved} saved)"
        else:
            last_run_str = "—"
        lines.append(
            f"| `{r['site']}` | {r['status']} | {r['urls_found']} | {http} | {r['elapsed']:.1f}s | {last_run_str} | {note} |"
        )

    # Raw JSON
    lines.extend([
        "\n## Raw Data\n",
        "```json",
        json.dumps(results, indent=2, ensure_ascii=False),
        "```\n",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Health check for all registered parsers")
    parser.add_argument("--db", default="exhibitions.db", help="SQLite database path for health check")
    parser.add_argument(
        "--out-dir",
        default="docs/plans",
        help="Output directory for reports",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Concurrent workers (default {MAX_WORKERS})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"Timeout per site in seconds (default {TIMEOUT_SECONDS})",
    )
    args = parser.parse_args()

    sites = list(SITES.keys())
    total = len(sites)

    print(f"Health Check started at {datetime.now().isoformat()}")
    print(f"Sites: {total} | Workers: {args.workers} | Timeout: {args.timeout}s")
    print("=" * 70)

    results: list[dict[str, Any]] = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_site = {executor.submit(run_single, site, args.timeout): site for site in sites}
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                res = future.result()
            except Exception as exc:
                res = {
                    "site": site,
                    "status": "EXCEPTION",
                    "urls_found": 0,
                    "http_status": None,
                    "elapsed": 0.0,
                    "error": str(exc)[:300],
                }
            results.append(res)
            completed += 1
            note = (res.get("error") or "")[:40]
            http_str = str(res["http_status"]) if res["http_status"] is not None else "—"
            print(
                f"[{completed:2d}/{total}] "
                f"{_color(res['status'])} | "
                f"{res['site']:22s} | "
                f"URLs: {res['urls_found']:3d} | "
                f"HTTP: {http_str:4s} | "
                f"{res['elapsed']:5.1f}s | "
                f"{note}"
            )

    # Sort for consistent report ordering
    # Retry TIMEOUT sites once (serial, longer timeout)
    timeouts = [r for r in results if r["status"] == "TIMEOUT"]
    if timeouts:
        print(f"\nRetrying {len(timeouts)} TIMEOUT site(s) with serial execution...")
        retry_timeout = min(args.timeout * 2, 300)
        for r in timeouts:
            site = r["site"]
            print(f"  Retrying {site} (timeout={retry_timeout}s)...")
            retry_res = run_single(site, timeout=retry_timeout)
            # Replace in results
            for i, existing in enumerate(results):
                if existing["site"] == site:
                    results[i] = retry_res
                    break
            print(f"  -> {retry_res['status']} | URLs: {retry_res['urls_found']}")

    results.sort(key=lambda r: r["site"])

    print("\n" + "=" * 70)
    green = sum(1 for r in results if r["status"] == "PASS")
    cyan = sum(1 for r in results if r["status"] == "SKIPPED")
    red = sum(1 for r in results if r["status"] not in ("PASS", "SKIPPED"))
    print(f"PASS: {green:2d} | SKIPPED: {cyan:2d} | FAIL: {red:2d}")
    print("=" * 70)

    # Database health
    db_health = check_database(args.db)
    if db_health and "error" not in db_health:
        print(
            f"DB: {db_health['exhibitions']} exhibitions, "
            f"{db_health['artworks']} artworks"
        )

    # Generate report
    report_path = generate_report(results, db_health, Path(args.out_dir))
    print(f"\nReport saved to: {report_path}")

    # Also save raw JSON
    json_path = Path(args.out_dir) / f"health-check-results-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Raw data saved to: {json_path}")


if __name__ == "__main__":
    main()
