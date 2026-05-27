#!/usr/bin/env python3
"""从 MoMA CSV 重新聚合策展人并回填到现有数据库记录（标题匹配版）。

由于 MoMA 网站 URL 中的 ExhibitionID 与 CSV 中的 ExhibitionID
属于两套不同编号体系，本脚本改用展览标题匹配。

Usage:
    uv run python scripts/backfill_moma_curators.py --dry-run
    uv run python scripts/backfill_moma_curators.py
"""

import argparse
import csv
import json
import logging
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, ".")

from src.database import ExhibitionDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_moma_curators")

MOMA_LOCAL_CSV_PATH = Path("data/moma_github/MoMAExhibitions1929to1989.csv")


def _normalize_title(title: str) -> str:
    """Normalize title for matching: NFKC + lowercase + strip."""
    if not title:
        return ""
    return unicodedata.normalize("NFKC", title).strip().lower()


def main():
    parser = argparse.ArgumentParser(description="Backfill MoMA curators from CSV by title matching")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    args = parser.parse_args()

    if not MOMA_LOCAL_CSV_PATH.exists():
        logger.error(f"MoMA CSV not found: {MOMA_LOCAL_CSV_PATH}")
        return

    db = ExhibitionDatabase(args.db)
    conn = db._get_connection()
    cursor = conn.cursor()

    # 1. 读取 CSV，按规范化标题聚合策展人
    logger.info("Reading MoMA CSV and aggregating curators by title...")
    curator_map: dict[str, list[str]] = {}
    # 保留原始标题用于调试输出
    original_titles: dict[str, str] = {}

    with open(MOMA_LOCAL_CSV_PATH, encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get("ExhibitionTitle", "").strip()
            display_name = row.get("DisplayName", "").strip()
            role = row.get("ExhibitionRole", "").strip()

            if not title or not display_name:
                continue

            if "Curator" in role or "Director" in role or "Organiz" in role:
                norm = _normalize_title(title)
                if norm not in curator_map:
                    curator_map[norm] = []
                    original_titles[norm] = title
                if display_name not in curator_map[norm]:
                    curator_map[norm].append(display_name)

    logger.info(f"Aggregated curators for {len(curator_map)} exhibitions from CSV.")

    # 2. 查询数据库中所有 MoMA 且 curators='[]' 的记录
    cursor.execute(
        "SELECT id, url, title FROM exhibitions WHERE source = 'MoMA' AND (curators IS NULL OR curators = '' OR curators = '[]')"
    )
    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} MoMA records with empty curators in DB.")

    updated = 0
    skipped_no_csv_match = 0
    skipped_csv_no_curator = 0
    failed = 0

    for row in rows:
        ex_db_id = row["id"]
        title = row["title"]

        if not title:
            skipped_csv_no_curator += 1
            continue

        norm_title = _normalize_title(title)
        curators = curator_map.get(norm_title)

        if not curators:
            # 检查是否 CSV 中有这个标题但无策展人数据
            if norm_title in original_titles:
                skipped_csv_no_curator += 1
            else:
                skipped_no_csv_match += 1
            continue

        if args.dry_run:
            logger.info(f"[DRY-RUN] Would update '{title}' with curators: {curators}")
            updated += 1
        else:
            try:
                cursor.execute(
                    "UPDATE exhibitions SET curators = ? WHERE id = ?",
                    (json.dumps(curators, ensure_ascii=False), ex_db_id),
                )
                conn.commit()
                logger.info(f"Updated '{title}' with curators: {curators}")
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update '{title}': {e}")
                failed += 1

    conn.close()
    logger.info("=" * 50)
    logger.info(
        f"Done: processed={len(rows)}, updated={updated}, "
        f"skipped_no_csv_match={skipped_no_csv_match}, "
        f"skipped_csv_no_curator={skipped_csv_no_curator}, failed={failed}"
    )
    logger.info(f"MoMA curator coverage: {updated + 414} / 1723 expected")


if __name__ == "__main__":
    main()
