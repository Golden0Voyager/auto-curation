#!/usr/bin/env python3
"""Artwork data quality checker — 验证 artworks 表的数据质量。

检查孤儿作品、缺失字段、可疑模式、数量异常等。

Usage:
    python scripts/validate_artworks.py                  # 全量检查
    python scripts/validate_artworks.py --source "MoMA"  # 按来源过滤
    python scripts/validate_artworks.py --json           # JSON 输出
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_orphaned(cursor: sqlite3.Cursor) -> list[dict]:
    """Find artworks with no matching exhibition."""
    cursor.execute("""
        SELECT a.id, a.exhibition_id, a.artist_name, a.work_title
        FROM artworks a
        LEFT JOIN exhibitions e ON a.exhibition_id = e.id
        WHERE e.id IS NULL
        LIMIT 100
    """)
    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "orphaned",
            "severity": "error",
            "artwork_id": r["id"],
            "exhibition_id": r["exhibition_id"],
            "detail": f"No exhibition for artwork '{r['artist_name']} / {r['work_title']}'",
        })
    return issues


def check_missing_fields(cursor: sqlite3.Cursor, source_filter: str | None = None) -> list[dict]:
    """Find artworks with missing artist_name or work_title."""
    conditions = []
    params = []
    if source_filter:
        conditions.append("e.source = ?")
        params.append(source_filter)

    where = " AND " + " AND ".join(conditions) if conditions else ""

    cursor.execute(f"""
        SELECT a.id, a.exhibition_id, a.artist_name, a.work_title, e.source
        FROM artworks a
        JOIN exhibitions e ON a.exhibition_id = e.id
        WHERE (a.artist_name IS NULL OR TRIM(a.artist_name) = ''
               OR a.work_title IS NULL OR TRIM(a.work_title) = '')
        {where}
        LIMIT 200
    """, params)

    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        missing = []
        if not r["artist_name"] or not r["artist_name"].strip():
            missing.append("artist_name")
        if not r["work_title"] or not r["work_title"].strip():
            missing.append("work_title")
        issues.append({
            "type": "missing_field",
            "severity": "warn",
            "artwork_id": r["id"],
            "exhibition_id": r["exhibition_id"],
            "source": r["source"],
            "detail": f"Missing: {', '.join(missing)}",
        })
    return issues


def check_suspicious_patterns(cursor: sqlite3.Cursor) -> list[dict]:
    """Find suspicious artwork records (artist == title, URL in name, etc.)."""
    cursor.execute("""
        SELECT a.id, a.exhibition_id, a.artist_name, a.work_title, e.source
        FROM artworks a
        JOIN exhibitions e ON a.exhibition_id = e.id
        WHERE a.artist_name IS NOT NULL AND a.work_title IS NOT NULL
          AND TRIM(a.artist_name) != '' AND TRIM(a.work_title) != ''
    """)

    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        artist = r["artist_name"].strip()
        title = r["work_title"].strip()

        # artist == title
        if artist.lower() == title.lower():
            issues.append({
                "type": "suspicious",
                "severity": "warn",
                "artwork_id": r["id"],
                "source": r["source"],
                "detail": f"artist_name == work_title: '{artist[:50]}'",
            })

        # URL in name
        if re.search(r"https?://", artist) or re.search(r"https?://", title):
            issues.append({
                "type": "suspicious",
                "severity": "warn",
                "artwork_id": r["id"],
                "source": r["source"],
                "detail": f"URL detected in name: artist='{artist[:30]}', title='{title[:30]}'",
            })

        # Very long names (likely parsing error)
        if len(artist) > 200 or len(title) > 200:
            issues.append({
                "type": "suspicious",
                "severity": "warn",
                "artwork_id": r["id"],
                "source": r["source"],
                "detail": f"Abnormally long: artist={len(artist)} chars, title={len(title)} chars",
            })

    return issues


def check_artwork_counts(cursor: sqlite3.Cursor) -> list[dict]:
    """Flag exhibitions with 0 or >500 artworks."""
    # Zero artworks (excluding strategies that don't produce artworks)
    cursor.execute("""
        SELECT e.id, e.source, e.title, e.parser_key,
               (SELECT COUNT(*) FROM artworks WHERE exhibition_id = e.id) as art_count
        FROM exhibitions e
        WHERE e.parser_key NOT IN ('aic', 'wikidata', 'rijksmuseum', 'met', 'whitney')
          AND (SELECT COUNT(*) FROM artworks WHERE exhibition_id = e.id) = 0
        LIMIT 50
    """)

    issues = []
    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "zero_artworks",
            "severity": "info",
            "exhibition_id": r["id"],
            "source": r["source"],
            "detail": f"'{r['title'][:50]}' has 0 artworks",
        })

    # Excessive artworks
    cursor.execute("""
        SELECT e.id, e.source, e.title,
               (SELECT COUNT(*) FROM artworks WHERE exhibition_id = e.id) as art_count
        FROM exhibitions e
        WHERE (SELECT COUNT(*) FROM artworks WHERE exhibition_id = e.id) > 500
        ORDER BY art_count DESC
        LIMIT 20
    """)

    for row in cursor.fetchall():
        r = dict(row)
        issues.append({
            "type": "excessive_artworks",
            "severity": "warn",
            "exhibition_id": r["id"],
            "source": r["source"],
            "detail": f"'{r['title'][:50]}' has {r['art_count']} artworks (possible data error)",
        })

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Artwork data quality checker")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    parser.add_argument("--source", help="Filter by exhibition source")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    issues: list[dict] = []
    issues.extend(check_orphaned(cursor))
    issues.extend(check_missing_fields(cursor, args.source))
    issues.extend(check_suspicious_patterns(cursor))
    issues.extend(check_artwork_counts(cursor))

    conn.close()

    if args.json:
        print(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "issues": issues[:200],
        }, indent=2, ensure_ascii=False))
        return

    # Summary
    total = len(issues)
    by_type: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    for issue in issues:
        by_type[issue["type"]] += 1
        by_severity[issue["severity"]] += 1

    print(f"Artwork Validation Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total issues: {total}")
    print(f"  Errors: {by_severity.get('error', 0)}, Warnings: {by_severity.get('warn', 0)}, Info: {by_severity.get('info', 0)}")
    print(f"\nBy type:")
    for t, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {t}: {count}")

    # Print details
    if issues:
        print(f"\nDetails (first 50):")
        for issue in issues[:50]:
            sev = issue["severity"].upper()
            pk = issue.get("source", issue.get("parser_key", "?"))
            print(f"  [{sev}] {pk} | {issue['type']}: {issue['detail']}")


if __name__ == "__main__":
    main()
