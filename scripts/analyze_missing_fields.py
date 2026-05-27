#!/usr/bin/env python3
"""Phase 4 Task 4.1: 缺失字段分析

统计 exhibitions 表中各关键字段的缺失率，按 source 分组输出 Markdown 报告。

Usage:
    python scripts/analyze_missing_fields.py
    python scripts/analyze_missing_fields.py --db exhibitions.db --output docs/plans/missing-fields-report.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import ExhibitionDatabase  # noqa: E402


def analyze(db_path: str) -> dict[str, Any]:
    """Run missing-field analysis and return structured results."""
    db = ExhibitionDatabase(db_path)
    conn = db._get_connection()
    cursor = conn.cursor()

    fields = [
        ("title", "title IS NULL OR title = ''"),
        ("start_date", "start_date IS NULL"),
        ("end_date", "end_date IS NULL"),
        ("concept", "concept IS NULL OR concept = ''"),
        ("preface", "preface IS NULL OR preface = ''"),
        ("city", "city IS NULL OR city = ''"),
        ("location", "location IS NULL OR location = ''"),
        ("curators", "curators = '[]' OR curators IS NULL"),
    ]

    # Build dynamic query
    select_clauses = ["parser_key", "COUNT(*) AS total"]
    for name, condition in fields:
        select_clauses.append(
            f"SUM(CASE WHEN {condition} THEN 1 ELSE 0 END) AS missing_{name}"
        )

    sql = f"SELECT {', '.join(select_clauses)} FROM exhibitions GROUP BY parser_key ORDER BY total DESC"
    cursor.execute(sql)
    rows = cursor.fetchall()

    # Overall totals
    cursor.execute("SELECT COUNT(*) FROM exhibitions")
    total_records = cursor.fetchone()[0]

    overall = {"total": total_records}
    for name, condition in fields:
        cursor.execute(f"SELECT COUNT(*) FROM exhibitions WHERE {condition}")
        overall[f"missing_{name}"] = cursor.fetchone()[0]

    conn.close()

    return {
        "total_records": total_records,
        "overall": overall,
        "by_source": [dict(row) for row in rows],
        "fields": [f[0] for f in fields],
    }


def write_report(data: dict[str, Any], path: str) -> None:
    """Write analysis results as Markdown."""
    fields = data["fields"]
    overall = data["overall"]
    total = overall["total"]

    lines = [
        "# Missing Fields Analysis Report",
        "",
        f"**Total exhibitions**: {total}",
        "",
        "## Overall Missing Rate",
        "",
        "| Field | Missing | Rate |",
        "|-------|--------:|-----:|",
    ]

    for field in fields:
        missing = overall[f"missing_{field}"]
        rate = missing / total * 100 if total else 0
        lines.append(f"| {field} | {missing} | {rate:.1f}% |")

    lines.extend([
        "",
        "## By Source",
        "",
        "| Source | Total | " + " | ".join(fields) + " |",
        "|--------|------:| " + " | ".join([":-:"] * len(fields)) + " |",
    ])

    for row in data["by_source"]:
        src_total = row["total"]
        cells = [f"`{row['parser_key']}`", str(src_total)]
        for field in fields:
            missing = row[f"missing_{field}"]
            rate = missing / src_total * 100 if src_total else 0
            cells.append(f"{missing} ({rate:.0f}%)")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Analyze missing fields in exhibitions database")
    arg_parser.add_argument("--db", default="exhibitions.db", help="SQLite database path")
    arg_parser.add_argument("--output", default="docs/plans/missing-fields-report.md", help="Output markdown path")
    args = arg_parser.parse_args()

    print(f"Analyzing missing fields in {args.db}...")
    data = analyze(args.db)

    total = data["total_records"]
    print(f"Total exhibitions: {total}")
    print("Overall missing rates:")
    for field in data["fields"]:
        missing = data["overall"][f"missing_{field}"]
        rate = missing / total * 100 if total else 0
        print(f"  {field:12s}: {missing:4d} / {total} ({rate:.1f}%)")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_report(data, args.output)
    print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
