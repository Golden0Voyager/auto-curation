#!/usr/bin/env python3
"""批量回填 AIC 展览图片。

通过 AIC API /exhibitions/search 端点分页获取所有展览的 image_url，
匹配数据库中的 URL 并回填。

Usage:
    uv run python scripts/backfill_aic_images.py --dry-run --limit-pages 2
    uv run python scripts/backfill_aic_images.py
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Optional

import httpx

sys.path.insert(0, ".")

from src.database import ExhibitionDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_aic_images")

AIC_SEARCH_URL = "https://api.artic.edu/api/v1/exhibitions/search"
BATCH_SIZE = 100
REQUEST_DELAY = 0.2


def fetch_all_aic_images(limit_pages: Optional[int] = None) -> Dict[int, str]:
    """Fetch all AIC exhibition image URLs via paginated search API.

    Returns:
        Mapping of exhibition_id (int) -> image_url (str)
    """
    image_map: Dict[int, str] = {}
    offset = 0
    page = 0

    while True:
        if limit_pages and page >= limit_pages:
            logger.info(f"Reached page limit ({limit_pages}), stopping.")
            break

        try:
            resp = httpx.get(
                AIC_SEARCH_URL,
                params={
                    "fields": "id,image_url",
                    "limit": BATCH_SIZE,
                    "offset": offset,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("data", [])
            pagination = data.get("pagination", {})
            total = pagination.get("total", 0)

            if not items:
                break

            for item in items:
                ex_id = item.get("id")
                img_url = item.get("image_url")
                if ex_id and img_url:
                    image_map[ex_id] = img_url

            page += 1
            offset += BATCH_SIZE
            logger.info(
                f"[Page {page}] Fetched {len(items)} items, "
                f"images so far: {len(image_map)}, total API records: {total}"
            )

            if offset >= total:
                break

            time.sleep(REQUEST_DELAY)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error on page {page}: {e}")
            break
        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
            break

    return image_map


def main():
    parser = argparse.ArgumentParser(description="Backfill AIC exhibition images")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--limit-pages", type=int, help="Limit API pages for testing")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    args = parser.parse_args()

    logger.info("Fetching AIC exhibition images from API...")
    image_map = fetch_all_aic_images(limit_pages=args.limit_pages)
    logger.info(f"Total AIC exhibitions with image_url: {len(image_map)}")

    if not image_map:
        logger.warning("No images fetched from API. Exiting.")
        return

    db = ExhibitionDatabase(args.db)
    conn = db._get_connection()
    cursor = conn.cursor()

    # Query all AIC records missing images
    cursor.execute(
        """
        SELECT id, url, title FROM exhibitions
        WHERE source = 'Art Institute of Chicago'
          AND (images IS NULL OR images = '' OR images = '[]')
        """
    )
    rows = cursor.fetchall()
    logger.info(f"AIC records missing images in DB: {len(rows)}")

    updated = 0
    skipped = 0
    failed = 0

    for row in rows:
        ex_db_id = row["id"]
        url = row["url"] or ""
        title = row["title"]

        # Extract exhibition ID from URL: /exhibitions/{id}/...
        aic_id = None
        if "/exhibitions/" in url:
            try:
                aic_id_str = url.split("/exhibitions/")[-1].split("/")[0].split("?")[0].split("#")[0]
                aic_id = int(aic_id_str)
            except (ValueError, IndexError):
                pass

        if not aic_id or aic_id not in image_map:
            skipped += 1
            continue

        img_url = image_map[aic_id]

        if args.dry_run:
            logger.info(f"[DRY-RUN] Would update '{title}' -> {img_url}")
            updated += 1
        else:
            try:
                cursor.execute(
                    "UPDATE exhibitions SET images = ? WHERE id = ?",
                    (json.dumps([img_url], ensure_ascii=False), ex_db_id),
                )
                conn.commit()
                logger.info(f"Updated '{title}' -> {img_url}")
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update '{title}': {e}")
                failed += 1

    conn.close()
    logger.info("=" * 50)
    logger.info(
        f"Done: processed={len(rows)}, updated={updated}, skipped={skipped}, failed={failed}"
    )


if __name__ == "__main__":
    main()
