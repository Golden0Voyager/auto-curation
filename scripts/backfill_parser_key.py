#!/usr/bin/env python3
"""Backfill empty parser_key on v1 legacy exhibition records.

Usage:
    python scripts/backfill_parser_key.py              # Dry-run
    python scripts/backfill_parser_key.py --apply       # Apply changes
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


SOURCE_TO_KEY = {
    "Serpentine Galleries": "serpentine_galleries",
    "Mori Art Museum": "mori_art_museum",
    "M+ Museum": "m+_museum",
    "Tate Modern": "tate_modern",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill empty parser_key on v1 legacy records")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Count affected rows
    cursor.execute("SELECT source, count(*) as cnt FROM exhibitions WHERE parser_key IS NULL OR parser_key = '' GROUP BY source")
    rows = cursor.fetchall()

    if not rows:
        print("No records with empty parser_key found. Nothing to do.")
        conn.close()
        return

    total = 0
    print(f"{'Source':<30} {'Count':>6}  Target parser_key")
    print("-" * 70)
    for row in rows:
        source = row["source"]
        count = row["cnt"]
        key = SOURCE_TO_KEY.get(source, f"(unknown: {source})")
        print(f"{source:<30} {count:>6}  {key}")
        total += count

    print(f"\nTotal: {total} records to update")

    if not args.apply:
        print("\n[DRY-RUN] Use --apply to commit changes.")
        conn.close()
        return

    # Apply updates
    updated = 0
    for source, key in SOURCE_TO_KEY.items():
        cursor.execute(
            "UPDATE exhibitions SET parser_key = ? WHERE source = ? AND (parser_key IS NULL OR parser_key = '')",
            (key, source),
        )
        updated += cursor.rowcount

    conn.commit()
    print(f"\nUpdated {updated} records.")

    # Verify
    cursor.execute("SELECT parser_key, count(*) as cnt FROM exhibitions GROUP BY parser_key ORDER BY cnt DESC")
    print("\n=== Updated parser_key distribution ===")
    for row in cursor.fetchall():
        pk = row["parser_key"] or "(empty)"
        print(f"  {pk}: {row['cnt']}")

    conn.close()


if __name__ == "__main__":
    main()
