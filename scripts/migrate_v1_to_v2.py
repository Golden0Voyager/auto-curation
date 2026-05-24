#!/usr/bin/env python3
"""
Database migration script: v1 -> v2

Adds fields introduced by Phase 0 architecture refactoring:
- exhibitions.curators (JSON list)
- exhibitions.institution_type
- exhibitions.parser_key
- New indexes for performance at scale
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "exhibitions.db")


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate(db_path: str):
    print(f"🔄 Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Add curators column
    if not column_exists(conn, "exhibitions", "curators"):
        cursor.execute("ALTER TABLE exhibitions ADD COLUMN curators TEXT DEFAULT '[]';")
        print("  ✅ Added column: curators")
    else:
        print("  ⏭️  Column curators already exists")

    # 2. Add institution_type column
    if not column_exists(conn, "exhibitions", "institution_type"):
        cursor.execute("ALTER TABLE exhibitions ADD COLUMN institution_type TEXT DEFAULT 'museum';")
        print("  ✅ Added column: institution_type")
    else:
        print("  ⏭️  Column institution_type already exists")

    # 3. Add parser_key column
    if not column_exists(conn, "exhibitions", "parser_key"):
        cursor.execute("ALTER TABLE exhibitions ADD COLUMN parser_key TEXT;")
        print("  ✅ Added column: parser_key")
    else:
        print("  ⏭️  Column parser_key already exists")

    # 4. Create indexes
    indexes = [
        ("idx_exhibitions_source", "CREATE INDEX IF NOT EXISTS idx_exhibitions_source ON exhibitions(source);"),
        ("idx_exhibitions_city", "CREATE INDEX IF NOT EXISTS idx_exhibitions_city ON exhibitions(city);"),
        ("idx_exhibitions_start_date", "CREATE INDEX IF NOT EXISTS idx_exhibitions_start_date ON exhibitions(start_date);"),
        ("idx_exhibitions_parser_key", "CREATE INDEX IF NOT EXISTS idx_exhibitions_parser_key ON exhibitions(parser_key);"),
    ]
    for idx_name, sql in indexes:
        cursor.execute(sql)
        print(f"  ✅ Created index: {idx_name}")

    # 5. Backfill parser_key from source
    cursor.execute("SELECT COUNT(*) FROM exhibitions WHERE parser_key IS NULL OR parser_key = '';")
    null_count = cursor.fetchone()[0]
    if null_count > 0:
        cursor.execute("""
            UPDATE exhibitions
            SET parser_key = LOWER(REPLACE(REPLACE(REPLACE(source, ' ', '_'), "'", ''), '.', ''))
            WHERE parser_key IS NULL OR parser_key = '';
        """)
        print(f"  ✅ Backfilled parser_key for {cursor.rowcount} records")
    else:
        print("  ⏭️  No parser_key backfill needed")

    # 6. Backfill institution_type
    cursor.execute("SELECT COUNT(*) FROM exhibitions WHERE institution_type IS NULL OR institution_type = '';")
    null_count = cursor.fetchone()[0]
    if null_count > 0:
        cursor.execute("UPDATE exhibitions SET institution_type = 'museum' WHERE institution_type IS NULL OR institution_type = '';")
        print(f"  ✅ Backfilled institution_type for {cursor.rowcount} records")
    else:
        print("  ⏭️  No institution_type backfill needed")

    conn.commit()

    # 7. Report
    cursor.execute("SELECT COUNT(*) FROM exhibitions")
    total_ex = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM artworks")
    total_art = cursor.fetchone()[0]
    print(f"\n📊 Migration complete. Database state: {total_ex} exhibitions | {total_art} artworks")
    conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    migrate(db)
