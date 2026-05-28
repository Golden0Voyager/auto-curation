#!/usr/bin/env python3
"""Scraper run monitor — 检测采集运行异常。

分析 scraper_runs 表，检测失败、回归、零保存、过期等问题。

Usage:
    python scripts/monitor_runs.py              # 完整报告
    python scripts/monitor_runs.py --failed     # 仅失败
    python scripts/monitor_runs.py --since 7d   # 最近 7 天
    python scripts/monitor_runs.py --alert      # CI 模式（有问题 exit 1）
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_since(value: str) -> str:
    """Convert relative time to ISO timestamp."""
    now = datetime.now()
    if value.endswith("d"):
        delta = timedelta(days=int(value[:-1]))
    elif value.endswith("h"):
        delta = timedelta(hours=int(value[:-1]))
    else:
        return value
    return (now - delta).isoformat()


def format_duration(started: str, finished: str | None) -> str:
    if not finished:
        return "running..."
    try:
        start = datetime.fromisoformat(started)
        end = datetime.fromisoformat(finished)
        secs = (end - start).total_seconds()
        if secs < 60:
            return f"{secs:.0f}s"
        if secs < 3600:
            return f"{secs / 60:.1f}m"
        return f"{secs / 3600:.1f}h"
    except (ValueError, TypeError):
        return "?"


def check_failures(cursor: sqlite3.Cursor) -> list[dict]:
    """Find runs with errors or failures."""
    cursor.execute("""
        SELECT id, parser_key, started_at, finished_at, error_message,
               exhibitions_saved, exhibitions_failed
        FROM scraper_runs
        WHERE error_message IS NOT NULL AND error_message != ''
        ORDER BY started_at DESC
        LIMIT 20
    """)
    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "failure",
            "severity": "error",
            "run_id": r["id"],
            "parser_key": r["parser_key"],
            "started_at": r["started_at"],
            "error": r["error_message"][:100],
        })
    return issues


def check_zero_saves(cursor: sqlite3.Cursor) -> list[dict]:
    """Find the latest run per parser that discovered URLs but saved nothing."""
    cursor.execute("""
        SELECT r.id, r.parser_key, r.started_at, r.urls_discovered, r.exhibitions_saved, r.run_type
        FROM scraper_runs r
        INNER JOIN (
            SELECT parser_key, MAX(started_at) as max_ts
            FROM scraper_runs
            WHERE run_type != 'dry_run'
            GROUP BY parser_key
        ) latest ON r.parser_key = latest.parser_key AND r.started_at = latest.max_ts
        WHERE r.urls_discovered > 0 AND r.exhibitions_saved = 0
        ORDER BY r.started_at DESC
        LIMIT 20
    """)
    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "zero_save",
            "severity": "warn",
            "run_id": r["id"],
            "parser_key": r["parser_key"],
            "started_at": r["started_at"],
            "detail": f"Discovered {r['urls_discovered']} URLs but saved 0",
        })
    return issues


def check_regression(cursor: sqlite3.Cursor) -> list[dict]:
    """Detect URL discovery regression (>20% drop between consecutive runs)."""
    cursor.execute("""
        SELECT DISTINCT parser_key FROM scraper_runs
    """)
    parser_keys = [row[0] for row in cursor.fetchall()]

    issues = []
    for pk in parser_keys:
        cursor.execute("""
            SELECT urls_discovered, started_at FROM scraper_runs
            WHERE parser_key = ? AND run_type != 'dry_run'
            ORDER BY started_at DESC
            LIMIT 2
        """, (pk,))
        rows = cursor.fetchall()
        if len(rows) < 2:
            continue

        latest = dict(rows[0])
        previous = dict(rows[1])
        prev_urls = previous["urls_discovered"]
        curr_urls = latest["urls_discovered"]

        if prev_urls > 0 and curr_urls < prev_urls * 0.8:
            drop = (1 - curr_urls / prev_urls) * 100
            issues.append({
                "type": "regression",
                "severity": "warn",
                "parser_key": pk,
                "detail": f"URL discovery dropped {drop:.0f}%: {prev_urls} -> {curr_urls}",
                "latest_at": latest["started_at"],
            })
    return issues


def check_staleness(cursor: sqlite3.Cursor, days: int = 7) -> list[dict]:
    """Find parsers with no recent runs."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute("""
        SELECT parser_key, MAX(started_at) as last_run
        FROM scraper_runs
        GROUP BY parser_key
        HAVING last_run < ?
        ORDER BY last_run ASC
    """, (cutoff,))
    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "stale",
            "severity": "info",
            "parser_key": r["parser_key"],
            "detail": f"No run since {r['last_run'][:10]}",
        })
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper run monitor")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    parser.add_argument("--failed", action="store_true", help="Show only failures")
    parser.add_argument("--since", help="Time filter: 7d, 24h, or ISO date")
    parser.add_argument("--alert", action="store_true", help="Exit 1 if issues found (CI mode)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    issues: list[dict] = []

    # Run checks
    issues.extend(check_failures(cursor))
    issues.extend(check_zero_saves(cursor))
    issues.extend(check_regression(cursor))

    if not args.failed:
        issues.extend(check_staleness(cursor))

    conn.close()

    if not issues:
        print("No issues detected.")
        if args.alert:
            sys.exit(0)
        return

    # Severity counts
    errors = [i for i in issues if i["severity"] == "error"]
    warns = [i for i in issues if i["severity"] == "warn"]
    infos = [i for i in issues if i["severity"] == "info"]

    # Print report
    print(f"Monitor Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Issues: {len(errors)} errors, {len(warns)} warnings, {len(infos)} info")
    print("=" * 60)

    for severity_label, items in [("ERROR", errors), ("WARNING", warns), ("INFO", infos)]:
        if not items:
            continue
        print(f"\n--- {severity_label} ({len(items)}) ---")
        for item in items:
            pk = item.get("parser_key", "?")
            detail = item.get("detail") or item.get("error", "")
            print(f"  [{pk}] {item['type']}: {detail}")

    # Alert mode
    if args.alert and (errors or warns):
        print(f"\nExiting with code 1 ({len(errors)} errors, {len(warns)} warnings)")
        sys.exit(1)


if __name__ == "__main__":
    main()
