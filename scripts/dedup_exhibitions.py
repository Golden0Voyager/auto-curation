#!/usr/bin/env python3
"""Phase 4 Task 4.3: 重复展览检测

基于 (source, title) 或 (source, title, start_date) 检测重复记录，
输出候选重复列表供人工审核。

Usage:
    python scripts/dedup_exhibitions.py
    python scripts/dedup_exhibitions.py --threshold 0.9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ExhibitionDatabase  # noqa: E402


def find_duplicates(db_path: str) -> dict[str, Any]:
    """Find duplicate exhibitions based on (parser_key, title)."""
    db = ExhibitionDatabase(db_path)
    conn = db._get_connection()
    cursor = conn.cursor()

    # Exact duplicate detection on (parser_key, title)
    cursor.execute("""
        SELECT parser_key, title, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM exhibitions
        WHERE title IS NOT NULL AND title != ''
        GROUP BY parser_key, title
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)
    exact_dups = [dict(row) for row in cursor.fetchall()]

    # Near-duplicate detection on (parser_key, title, start_date)
    cursor.execute("""
        SELECT parser_key, title, start_date, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM exhibitions
        WHERE title IS NOT NULL AND title != '' AND start_date IS NOT NULL
        GROUP BY parser_key, title, start_date
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)
    near_dups = [dict(row) for row in cursor.fetchall()]

    # Duplicate URLs (shouldn't happen due to UNIQUE constraint, but check anyway)
    cursor.execute("""
        SELECT url, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM exhibitions
        WHERE url IS NOT NULL AND url != ''
        GROUP BY url
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)
    url_dups = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "exact_duplicates": exact_dups,
        "near_duplicates": near_dups,
        "url_duplicates": url_dups,
    }


def write_report(data: dict[str, Any], path: str) -> None:
    """Write duplicate detection results as Markdown."""
    lines = [
        "# Duplicate Exhibition Detection Report",
        "",
        f"## Exact Duplicates (by parser_key + title): {len(data['exact_duplicates'])} groups",
        "",
    ]

    if data["exact_duplicates"]:
        lines.append("| Source | Title | Count | IDs |")
        lines.append("|--------|-------|------:|-----|")
        for d in data["exact_duplicates"][:50]:
            title = d["title"].replace("|", "\\|")[:60]
            lines.append(f"| `{d['parser_key']}` | {title} | {d['cnt']} | {d['ids']} |")
        if len(data["exact_duplicates"]) > 50:
            lines.append(f"| ... | *{len(data['exact_duplicates']) - 50} more groups* | | |")
    else:
        lines.append("No exact duplicates found.")

    lines.extend([
        "",
        f"## Near Duplicates (by parser_key + title + start_date): {len(data['near_duplicates'])} groups",
        "",
    ])

    if data["near_duplicates"]:
        lines.append("| Source | Title | Start Date | Count | IDs |")
        lines.append("|--------|-------|------------|------:|-----|")
        for d in data["near_duplicates"][:50]:
            title = d["title"].replace("|", "\\|")[:60]
            lines.append(f"| `{d['parser_key']}` | {title} | {d['start_date']} | {d['cnt']} | {d['ids']} |")
        if len(data["near_duplicates"]) > 50:
            lines.append(f"| ... | *{len(data['near_duplicates']) - 50} more groups* | | | |")
    else:
        lines.append("No near duplicates found.")

    lines.extend([
        "",
        f"## URL Duplicates: {len(data['url_duplicates'])} groups",
        "",
    ])

    if data["url_duplicates"]:
        lines.append("| URL | Count | IDs |")
        lines.append("|-----|------:|-----|")
        for d in data["url_duplicates"]:
            url = d["url"].replace("|", "\\|")[:80]
            lines.append(f"| {url} | {d['cnt']} | {d['ids']} |")
    else:
        lines.append("No URL duplicates found.")

    lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Detect duplicate exhibitions in database")
    arg_parser.add_argument("--db", default="exhibitions.db", help="SQLite database path")
    arg_parser.add_argument("--output", default="docs/plans/duplicate-report.md", help="Output markdown path")
    args = arg_parser.parse_args()

    print(f"Scanning {args.db} for duplicates...")
    data = find_duplicates(args.db)

    total_groups = len(data["exact_duplicates"]) + len(data["near_duplicates"]) + len(data["url_duplicates"])
    print(f"Exact duplicates: {len(data['exact_duplicates'])} groups")
    print(f"Near duplicates:  {len(data['near_duplicates'])} groups")
    print(f"URL duplicates:   {len(data['url_duplicates'])} groups")
    print(f"Total: {total_groups} duplicate groups")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_report(data, args.output)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
