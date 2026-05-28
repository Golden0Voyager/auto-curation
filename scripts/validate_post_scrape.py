#!/usr/bin/env python3
"""Post-scrape data quality validator — 从数据库验证展览数据质量。

检查 title、dates、concept、artworks 等字段的完整性和格式。

Usage:
    python scripts/validate_post_scrape.py                   # 全量验证
    python scripts/validate_post_scrape.py --site tate       # 按 parser 验证
    python scripts/validate_post_scrape.py --limit 100       # 限制检查数量
    python scripts/validate_post_scrape.py --output report.md
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

# Navigation noise words that should not appear as titles
NOISE_WORDS = {
    "home", "menu", "exhibitions", "exhibition", "about", "contact",
    "visit", "support", "donate", "shop", "search", "events", "news",
    "education", "collections", "artists", "programs", "gallery",
    "museum", "foundation", "press", "privacy", "terms", "cookies",
    "subscribe", "newsletter", "login", "sign up", "loading",
    "back", "next", "previous", "close", "open", "more", "less",
}


def _is_strict_date(value: str) -> bool:
    """Check if value is strict YYYY-MM-DD format."""
    if not value:
        return True  # null is OK
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value))


def validate_exhibition(row: dict) -> list[dict]:
    """Validate a single exhibition record. Returns list of issues."""
    issues = []

    # Title checks
    title = row.get("title", "")
    if not title or len(title.strip()) < 3:
        issues.append({"field": "title", "severity": "error", "detail": "Missing or too short"})
    elif title.strip().lower() in NOISE_WORDS:
        issues.append({"field": "title", "severity": "error", "detail": f"Noise word: '{title.strip()}'"})

    # Date format checks
    start = row.get("start_date", "")
    end = row.get("end_date", "")
    if start and not _is_strict_date(start):
        issues.append({"field": "start_date", "severity": "warn", "detail": f"Non-standard format: '{start}'"})
    if end and not _is_strict_date(end):
        issues.append({"field": "end_date", "severity": "warn", "detail": f"Non-standard format: '{end}'"})

    # Date logic
    if start and end and _is_strict_date(start) and _is_strict_date(end):
        if start > end:
            issues.append({"field": "dates", "severity": "error", "detail": f"start_date ({start}) > end_date ({end})"})

    # Concept check (only for HTML_LLM sources, skip CSV/API)
    source = row.get("source", "")
    strategy_hint = row.get("parser_key", "")
    concept = row.get("concept", "")
    if not concept:
        issues.append({"field": "concept", "severity": "warn", "detail": "Missing"})
    elif len(concept.strip()) < 50:
        issues.append({"field": "concept", "severity": "warn", "detail": f"Too short ({len(concept.strip())} chars)"})

    # Preface check
    preface = row.get("preface", "")
    if not preface:
        issues.append({"field": "preface", "severity": "info", "detail": "Missing"})

    # City check
    city = row.get("city", "")
    if not city:
        issues.append({"field": "city", "severity": "warn", "detail": "Missing"})

    # Parser key check
    pk = row.get("parser_key", "")
    if not pk:
        issues.append({"field": "parser_key", "severity": "error", "detail": "Empty"})

    # Artwork checks
    artworks = row.get("artworks", [])
    if isinstance(artworks, str):
        try:
            artworks = json.loads(artworks)
        except json.JSONDecodeError:
            artworks = []

    for art in artworks:
        art_issues = []
        if not art.get("artist_name", "").strip():
            art_issues.append("missing artist_name")
        if not art.get("work_title", "").strip():
            art_issues.append("missing work_title")
        if art.get("artist_name", "").strip() == art.get("work_title", "").strip() and art.get("artist_name"):
            art_issues.append("artist_name == work_title (possible hallucination)")
        if art_issues:
            issues.append({"field": "artwork", "severity": "warn", "detail": f"ID {art.get('id', '?')}: {', '.join(art_issues)}"})

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-scrape data quality validator")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    parser.add_argument("--site", help="Filter by parser_key")
    parser.add_argument("--limit", type=int, default=0, help="Max exhibitions to check (0=all)")
    parser.add_argument("--output", help="Output report path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    conditions = []
    params = []
    if args.site:
        conditions.append("parser_key = ?")
        params.append(args.site)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    limit = f" LIMIT {args.limit}" if args.limit else ""

    cursor.execute(f"SELECT * FROM exhibitions{where} ORDER BY scraped_at DESC{limit}", params)
    rows = cursor.fetchall()

    if not rows:
        print("No exhibitions found.")
        conn.close()
        return

    # Validate each exhibition
    all_issues: list[dict] = []
    issue_counts: dict[str, int] = defaultdict(int)
    source_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "issues": 0, "errors": 0})

    for row in rows:
        ex = dict(row)
        # Load artworks
        cursor.execute("SELECT * FROM artworks WHERE exhibition_id = ?", (ex["id"],))
        ex["artworks"] = [dict(r) for r in cursor.fetchall()]

        issues = validate_exhibition(ex)
        source = ex.get("source", "unknown")
        source_stats[source]["total"] += 1

        if issues:
            source_stats[source]["issues"] += 1
            has_error = any(i["severity"] == "error" for i in issues)
            if has_error:
                source_stats[source]["errors"] += 1

            for issue in issues:
                all_issues.append({
                    "exhibition_id": ex["id"],
                    "source": source,
                    "title": ex.get("title", "")[:60],
                    **issue,
                })
                issue_counts[f"{issue['field']}:{issue['severity']}"] += 1

    conn.close()

    # Output
    total = len(rows)
    with_issues = sum(1 for s in source_stats.values() if s["issues"] > 0)

    if args.json:
        print(json.dumps({
            "total_checked": total,
            "sources": dict(source_stats),
            "issue_counts": dict(issue_counts),
            "issues": all_issues[:100],
        }, indent=2, ensure_ascii=False))
        return

    # Markdown report
    report_lines = []
    report_lines.append("# Post-Scrape Validation Report")
    report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total checked: {total} exhibitions")

    # Summary table
    report_lines.append("\n## Source Summary\n")
    report_lines.append(f"| Source | Total | With Issues | Errors | Issue Rate |")
    report_lines.append(f"|--------|------:|------------:|-------:|-----------:|")
    for source, stats in sorted(source_stats.items(), key=lambda x: x[1]["total"], reverse=True):
        rate = f"{stats['issues'] / stats['total'] * 100:.1f}%" if stats["total"] else "0%"
        report_lines.append(f"| {source} | {stats['total']} | {stats['issues']} | {stats['errors']} | {rate} |")

    # Issue breakdown
    report_lines.append("\n## Issue Breakdown\n")
    for key, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"- **{key}**: {count}")

    # Top issues
    report_lines.append("\n## Top Issues (first 50)\n")
    for issue in all_issues[:50]:
        severity_icon = {"error": "ERROR", "warn": "WARN", "info": "INFO"}.get(issue["severity"], "?")
        report_lines.append(f"- [{severity_icon}] {issue['source']} / ID {issue['exhibition_id']}: "
                          f"{issue['field']} — {issue['detail']}")

    report = "\n".join(report_lines)

    if args.output:
        Path(args.output).write_text(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)

    # Summary
    error_count = sum(1 for i in all_issues if i["severity"] == "error")
    warn_count = sum(1 for i in all_issues if i["severity"] == "warn")
    print(f"\nSummary: {error_count} errors, {warn_count} warnings across {total} exhibitions")


if __name__ == "__main__":
    main()
