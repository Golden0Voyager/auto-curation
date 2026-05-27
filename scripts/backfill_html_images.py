#!/usr/bin/env python3
"""重新抓取 HTML_LLM 来源展览页面并提取图片。

针对未被 Cloudflare 拦截的来源，批量重新抓取详情页，
用 BeautifulSoup 提取图片 URL 并回填到数据库。

Usage:
    uv run python scripts/backfill_html_images.py --dry-run --limit 10
    uv run python scripts/backfill_html_images.py --source "Mori Art Museum"
    uv run python scripts/backfill_html_images.py
"""

import argparse
import json
import logging
import sys
import time
from typing import List, Optional

import httpx

sys.path.insert(0, ".")

from src.database import ExhibitionDatabase
from src.scraper import extract_images_from_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_html_images")

# Sources known to be blocked or problematic — skip these
BLOCKED_SOURCES = {
    "Guggenheim",
    "LACMA",
    "Dia Art Foundation",
    "Whitechapel Gallery",
    "Hayward Gallery",
    "MASS MoCA",
    "Fondation Louis Vuitton",
    "Hirshhorn Museum",
}

DEFAULT_TIMEOUT = 30.0
REQUEST_DELAY = 0.3


def fetch_images_for_url(client: httpx.Client, url: str, timeout: float = DEFAULT_TIMEOUT) -> List[str]:
    """Fetch a single exhibition page and extract image URLs."""
    try:
        response = client.get(url, timeout=timeout, follow_redirects=True)
        if response.status_code == 404:
            logger.debug(f"Page not found: {url}")
            return []
        if response.status_code >= 500:
            logger.warning(f"Server error {response.status_code} for {url}")
            return []
        if response.status_code != 200:
            logger.debug(f"Unexpected status {response.status_code} for {url}")
            return []
        return extract_images_from_html(response.text, url, max_images=8)
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url}")
        return []
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Backfill exhibition images from HTML re-scraping")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--source", help="Limit to a specific source")
    parser.add_argument("--limit", type=int, help="Max records to process")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    args = parser.parse_args()

    db = ExhibitionDatabase(args.db)
    conn = db._get_connection()
    cursor = conn.cursor()

    # Build query
    query = """
        SELECT id, url, title, source FROM exhibitions
        WHERE (images IS NULL OR images = '' OR images = '[]')
    """
    params = []

    if args.source:
        query += " AND source = ?"
        params.append(args.source)
    else:
        # Exclude CSV/API sources and blocked sources
        excluded = ["Art Institute of Chicago", "MoMA", "National Gallery of Art",
                    "The Met", "Wikidata", "Rijksmuseum"] + list(BLOCKED_SOURCES)
        placeholders = ",".join("?" for _ in excluded)
        query += f" AND source NOT IN ({placeholders})"
        params.extend(excluded)

    query += " ORDER BY id DESC"
    if args.limit:
        query += " LIMIT ?"
        params.append(args.limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} records missing images to process.")

    if not rows:
        conn.close()
        return

    updated = 0
    failed = 0
    skipped_no_images = 0

    with httpx.Client(follow_redirects=True) as client:
        for row in rows:
            ex_id = row["id"]
            url = row["url"]
            title = row["title"]
            source = row["source"]

            if not url:
                skipped_no_images += 1
                continue

            logger.info(f"[{source}] Fetching: {title}")
            image_urls = fetch_images_for_url(client, url)

            if not image_urls:
                skipped_no_images += 1
                continue

            if args.dry_run:
                logger.info(f"[DRY-RUN] Would update '{title}' with {len(image_urls)} images")
                updated += 1
            else:
                try:
                    cursor.execute(
                        "UPDATE exhibitions SET images = ? WHERE id = ?",
                        (json.dumps(image_urls, ensure_ascii=False), ex_id),
                    )
                    conn.commit()
                    logger.info(f"Updated '{title}' with {len(image_urls)} images")
                    updated += 1
                except Exception as e:
                    logger.error(f"Failed to update '{title}': {e}")
                    failed += 1

            time.sleep(REQUEST_DELAY)

    conn.close()
    logger.info("=" * 50)
    logger.info(
        f"Done: processed={len(rows)}, updated={updated}, "
        f"skipped_no_images={skipped_no_images}, failed={failed}"
    )


if __name__ == "__main__":
    main()
