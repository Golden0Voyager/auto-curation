#!/usr/bin/env python3
"""Phase 4 Task 4.2: 日期格式标准化

将 exhibitions 表中混杂的日期格式统一为 YYYY-MM-DD：
- YYYY-MM-DD → 保持不变
- YYYY-MM    → YYYY-MM-01
- YYYY       → YYYY-01-01

不猜测未知月份/日期，只做确定性填充。

Usage:
    python scripts/normalize_dates.py --dry-run
    python scripts/normalize_dates.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ExhibitionDatabase  # noqa: E402

DATE_PATTERN = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


def normalize_date(val: str | None) -> tuple[str | None, bool]:
    """Normalize a date string. Returns (new_value, was_changed)."""
    if not val:
        return val, False

    match = DATE_PATTERN.match(val.strip())
    if not match:
        return val, False

    year, month, day = match.groups()
    if month and day:
        return val, False  # Already YYYY-MM-DD

    if month:
        new_val = f"{year}-{month}-01"
    else:
        new_val = f"{year}-01-01"

    return new_val, True


def analyze_and_fix(db_path: str, dry_run: bool = False) -> dict[str, Any]:
    """Analyze and optionally fix date formats."""
    db = ExhibitionDatabase(db_path)
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, start_date, end_date FROM exhibitions WHERE start_date IS NOT NULL OR end_date IS NOT NULL")
    rows = cursor.fetchall()

    changes = []
    for row in rows:
        ex_id = row["id"]
        old_start = row["start_date"]
        old_end = row["end_date"]

        new_start, changed_start = normalize_date(old_start)
        new_end, changed_end = normalize_date(old_end)

        if changed_start or changed_end:
            changes.append({
                "id": ex_id,
                "old_start": old_start,
                "new_start": new_start,
                "old_end": old_end,
                "new_end": new_end,
            })

            if not dry_run:
                cursor.execute(
                    "UPDATE exhibitions SET start_date = ?, end_date = ? WHERE id = ?",
                    (new_start, new_end, ex_id),
                )

    if not dry_run and changes:
        conn.commit()

    conn.close()

    return {
        "total_checked": len(rows),
        "changed": len(changes),
        "changes": changes,
    }


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Normalize date formats in exhibitions database")
    arg_parser.add_argument("--db", default="exhibitions.db", help="SQLite database path")
    arg_parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = arg_parser.parse_args()

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Normalizing dates in {args.db}...")
    result = analyze_and_fix(args.db, dry_run=args.dry_run)

    print(f"Total records checked: {result['total_checked']}")
    print(f"Records changed: {result['changed']}")

    if result["changes"]:
        print("\nSample changes:")
        for ch in result["changes"][:10]:
            start_info = f"{ch['old_start']} -> {ch['new_start']}" if ch["old_start"] != ch["new_start"] else f"start={ch['old_start']}"
            end_info = f"{ch['old_end']} -> {ch['new_end']}" if ch["old_end"] != ch["new_end"] else f"end={ch['old_end']}"
            print(f"  ID {ch['id']}: {start_info} | {end_info}")
        if len(result["changes"]) > 10:
            print(f"  ... and {len(result['changes']) - 10} more")

    if args.dry_run:
        print("\nDry run complete. Use without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
