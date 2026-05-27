#!/usr/bin/env python3
"""策展人字段回填脚本

对高价值 HTML_LLM 机构的 curators='[]' 记录，重新抓取 HTML 并通过 LLM 提取策展人。

Usage:
    python scripts/backfill_curators.py --site mori --limit 10
    python scripts/backfill_curators.py --all --limit 5 --dry-run
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, ".")

from src.database import ExhibitionDatabase
from src.scraper import ExhibitionScraper
from src.sites import SITES
from src.sites.base import ParserStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_curators")

# 高价值机构列表（HTML_LLM 策略且策展人信息在页面中通常明确标注）
HIGH_VALUE_SITES = {
    "tate", "mori", "mplus", "serpentine", "momat",
    "whitney", "psa", "ucca", "whitney_biennial",
}


def backfill_site(
    scraper: ExhibitionScraper,
    db: ExhibitionDatabase,
    site_key: str,
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """对单个站点执行策展人回填。"""
    parser = SITES.get(site_key)
    if not parser:
        return {"site": site_key, "skipped": True, "reason": "parser not found"}

    strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
    if strategy != ParserStrategy.HTML_LLM:
        return {"site": site_key, "skipped": True, "reason": f"strategy is {strategy.value}"}

    # 查询缺失策展人的记录（按 source 字段匹配，更可靠）
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, url, title FROM exhibitions
        WHERE source = ? AND (curators = '[]' OR curators IS NULL)
        ORDER BY id DESC
        LIMIT ?
        """,
        (parser.source, limit or 9999),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"site": site_key, "processed": 0, "updated": 0, "failed": 0}

    updated = 0
    failed = 0

    for row in rows:
        ex_id = row["id"]
        url = row["url"]
        title = row["title"]

        logger.info(f"[{site_key}] Processing: {title}")

        try:
            # 重新抓取 HTML
            response = scraper.client.get(
                url, timeout=getattr(parser, "request_timeout", 60.0)
            )
            response.raise_for_status()
            clean_text = parser.clean_html(response.text)

            if not clean_text or len(clean_text.strip()) < 100:
                logger.warning(f"[{site_key}] Content too short: {url}")
                failed += 1
                continue

            # LLM 解析
            parsed = scraper.parser.parse_exhibition_text(
                clean_text, parser.source, parser.city
            )

            if not parsed:
                logger.warning(f"[{site_key}] LLM returned None: {url}")
                failed += 1
                continue

            curators = parsed.get("curators", [])
            if curators and len(curators) > 0:
                if not dry_run:
                    conn = db._get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE exhibitions SET curators = ? WHERE id = ?",
                        (json.dumps(curators, ensure_ascii=False), ex_id),
                    )
                    conn.commit()
                    conn.close()
                    logger.info(f"[{site_key}] Updated curators: {curators}")
                else:
                    logger.info(f"[{site_key}] Would update curators: {curators}")
                updated += 1
            else:
                logger.info(f"[{site_key}] No curators found: {url}")
                failed += 1

        except Exception as e:
            logger.error(f"[{site_key}] Error: {e}")
            failed += 1

    return {
        "site": site_key,
        "processed": len(rows),
        "updated": updated,
        "failed": failed,
    }


def main():
    arg_parser = argparse.ArgumentParser(description="Backfill curators for exhibitions")
    arg_parser.add_argument("--site", type=str, help="Target a single site")
    arg_parser.add_argument("--all", action="store_true", help="Target all high-value HTML_LLM sites")
    arg_parser.add_argument("--limit", type=int, default=10, help="Max records per site (default: 10)")
    arg_parser.add_argument("--dry-run", action="store_true", help="Simulate without writing to DB")
    arg_parser.add_argument("--db", default="exhibitions.db", help="Database path")
    args = arg_parser.parse_args()

    if not (args.site or args.all):
        print("Usage: python scripts/backfill_curators.py --site mori --limit 10")
        print("       python scripts/backfill_curators.py --all --limit 5 --dry-run")
        sys.exit(1)

    db = ExhibitionDatabase(args.db)
    scraper = ExhibitionScraper(args.db)

    if args.site:
        sites = [args.site]
    else:
        sites = sorted(HIGH_VALUE_SITES & set(SITES.keys()))

    logger.info(f"Backfilling curators for {len(sites)} site(s), limit={args.limit}")

    results = []
    for site_key in sites:
        result = backfill_site(scraper, db, site_key, args.limit, args.dry_run)
        results.append(result)
        status = "SKIPPED" if result.get("skipped") else "DONE"
        logger.info(
            f"[{site_key}] {status} | processed={result.get('processed', 0)} "
            f"updated={result.get('updated', 0)} failed={result.get('failed', 0)}"
        )

    scraper.close()

    # 汇总
    total_processed = sum(r.get("processed", 0) for r in results)
    total_updated = sum(r.get("updated", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)

    logger.info("=" * 50)
    logger.info(f"Summary: processed={total_processed}, updated={total_updated}, failed={total_failed}")


if __name__ == "__main__":
    main()
