#!/usr/bin/env python3
"""Scraper 运行历史查询工具

查询 scraper_runs 表中的历史运行记录，支持按机构过滤、
失败筛选、时间范围查询。

Usage:
    python scripts/scraper_history.py                    # 最近 20 次运行
    python scripts/scraper_history.py --site moma        # 按机构过滤
    python scripts/scraper_history.py --failed           # 只看失败的运行
    python scripts/scraper_history.py --since 7d         # 最近 7 天
    python scripts/scraper_history.py --limit 50         # 显示 50 条
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ExhibitionDatabase  # noqa: E402


def parse_since(value: str) -> str:
    """Convert relative time (7d, 24h, 30m) to ISO timestamp."""
    now = datetime.now()
    if value.endswith("d"):
        delta = timedelta(days=int(value[:-1]))
    elif value.endswith("h"):
        delta = timedelta(hours=int(value[:-1]))
    elif value.endswith("m"):
        delta = timedelta(minutes=int(value[:-1]))
    else:
        return value  # Assume ISO format
    return (now - delta).isoformat()


def format_duration(started: str, finished: str | None) -> str:
    """Format run duration as human-readable string."""
    if not finished:
        return "running..."
    try:
        start = datetime.fromisoformat(started)
        end = datetime.fromisoformat(finished)
        delta = end - start
        secs = delta.total_seconds()
        if secs < 60:
            return f"{secs:.0f}s"
        if secs < 3600:
            return f"{secs / 60:.1f}m"
        return f"{secs / 3600:.1f}h"
    except (ValueError, TypeError):
        return "?"


def main() -> None:
    parser = argparse.ArgumentParser(description="Query scraper run history")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    parser.add_argument("--site", help="Filter by parser_key")
    parser.add_argument("--failed", action="store_true", help="Show only failed runs")
    parser.add_argument("--since", help="Time filter: 7d, 24h, 30m, or ISO date")
    parser.add_argument("--limit", type=int, default=20, help="Max rows (default 20)")
    args = parser.parse_args()

    db = ExhibitionDatabase(args.db)
    conn = db._get_connection()
    cursor = conn.cursor()

    conditions = []
    params: list[str | int] = []

    if args.site:
        conditions.append("parser_key = ?")
        params.append(args.site)

    if args.failed:
        conditions.append("error_message IS NOT NULL AND error_message != ''")

    if args.since:
        conditions.append("started_at >= ?")
        params.append(parse_since(args.since))

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
        SELECT id, parser_key, run_type, started_at, finished_at,
               urls_discovered, urls_parsed, exhibitions_saved,
               exhibitions_failed, error_message
        FROM scraper_runs
        {where}
        ORDER BY started_at DESC
        LIMIT ?
    """
    params.append(args.limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No scraper runs found.")
        return

    # Print table
    print(f"{'ID':>4} {'Parser':<22} {'Type':<8} {'Started':<17} {'Duration':>8} "
          f"{'Found':>5} {'Parsed':>6} {'Saved':>5} {'Failed':>6} {'Error':<30}")
    print("-" * 120)

    for row in rows:
        r = dict(row)
        started = (r["started_at"] or "")[:16]
        duration = format_duration(r["started_at"], r["finished_at"])
        error = (r["error_message"] or "")[:30].replace("\n", " ")

        print(
            f"{r['id']:>4} {r['parser_key']:<22} {r['run_type']:<8} "
            f"{started:<17} {duration:>8} "
            f"{r['urls_discovered']:>5} {r['urls_parsed']:>6} "
            f"{r['exhibitions_saved']:>5} {r['exhibitions_failed']:>6} "
            f"{error:<30}"
        )

    print(f"\nTotal: {len(rows)} run(s)")


if __name__ == "__main__":
    main()
