#!/usr/bin/env python3
"""展览数据 Enrichment 主脚本 — 三层混合架构。

Tier 1: HTML_LLM 源重新抓取（concept / preface / curators / images）
Tier 2: CSV/API 源合成 concept（MoMA / AIC，零网络请求）
Tier 3: Image 统一提取（HTML 重新抓取 + AIC API 回填）

Usage:
    uv run python scripts/enrich_exhibitions.py --tier 2 --dry-run --limit 100
    uv run python scripts/enrich_exhibitions.py --tier all
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, ".")

from src.database import ExhibitionDatabase
from src.enrichment import synthesize_concept_moma, synthesize_concept_aic, synthesize_concept_whitney
from src.llm_parser import LLMExhibitionParser
from src.scraper import ExhibitionScraper, extract_images_from_html
from src.sites import SITES
from src.sites.base import ParserStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("enrich_exhibitions")


def _get_artists_for_exhibition(conn, ex_id: int) -> List[str]:
    """Query artworks table for artist names belonging to an exhibition."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT artist_name FROM artworks WHERE exhibition_id = ?",
        (ex_id,),
    )
    return [row["artist_name"] for row in cursor.fetchall() if row["artist_name"]]


def enrich_tier2(db: ExhibitionDatabase, limit: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Tier 2: 为 MoMA / AIC 合成 concept。零网络请求。"""
    conn = db._get_connection()
    cursor = conn.cursor()
    stats = {"moma": {"processed": 0, "updated": 0}, "aic": {"processed": 0, "updated": 0}}

    # --- MoMA ---
    cursor.execute(
        """
        SELECT id, title FROM exhibitions
        WHERE source = 'MoMA' AND (concept IS NULL OR concept = '')
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit or 999999,),
    )
    moma_rows = cursor.fetchall()
    logger.info(f"[Tier 2] MoMA: {len(moma_rows)} records missing concept")

    for row in moma_rows:
        ex_id = row["id"]
        title = row["title"]
        artists = _get_artists_for_exhibition(conn, ex_id)
        concept = synthesize_concept_moma(title, [{"artist_name": a} for a in artists])

        if not concept:
            continue
        stats["moma"]["processed"] += 1

        if dry_run:
            logger.info(f"[Tier 2] [DRY-RUN] MoMA '{title}' -> concept: {concept[:60]}...")
            stats["moma"]["updated"] += 1
        else:
            cursor.execute(
                "UPDATE exhibitions SET concept = ? WHERE id = ?",
                (concept, ex_id),
            )
            conn.commit()
            stats["moma"]["updated"] += 1

    # --- AIC ---
    cursor.execute(
        """
        SELECT id, title, preface FROM exhibitions
        WHERE source = 'Art Institute of Chicago' AND (concept IS NULL OR concept = '')
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit or 999999,),
    )
    aic_rows = cursor.fetchall()
    logger.info(f"[Tier 2] AIC: {len(aic_rows)} records missing concept")

    for row in aic_rows:
        ex_id = row["id"]
        title = row["title"]
        preface = row["preface"]
        artists = _get_artists_for_exhibition(conn, ex_id)
        concept = synthesize_concept_aic(title, preface, artists)

        if not concept:
            continue
        stats["aic"]["processed"] += 1

        if dry_run:
            logger.info(f"[Tier 2] [DRY-RUN] AIC '{title}' -> concept: {concept[:60]}...")
            stats["aic"]["updated"] += 1
        else:
            cursor.execute(
                "UPDATE exhibitions SET concept = ? WHERE id = ?",
                (concept, ex_id),
            )
            conn.commit()
            stats["aic"]["updated"] += 1

    # --- Whitney ---
    cursor.execute(
        """
        SELECT id, title, preface FROM exhibitions
        WHERE source = 'Whitney Museum of American Art' AND (concept IS NULL OR concept = '')
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit or 999999,),
    )
    whitney_rows = cursor.fetchall()
    stats["whitney"] = {"processed": 0, "updated": 0}
    logger.info(f"[Tier 2] Whitney: {len(whitney_rows)} records missing concept")

    for row in whitney_rows:
        ex_id = row["id"]
        title = row["title"]
        preface = row["preface"]
        concept = synthesize_concept_whitney(title, preface)

        if not concept:
            continue
        stats["whitney"]["processed"] += 1

        if dry_run:
            logger.info(f"[Tier 2] [DRY-RUN] Whitney '{title}' -> concept: {concept[:60]}...")
            stats["whitney"]["updated"] += 1
        else:
            cursor.execute(
                "UPDATE exhibitions SET concept = ? WHERE id = ?",
                (concept, ex_id),
            )
            conn.commit()
            stats["whitney"]["updated"] += 1

    conn.close()
    total_processed = stats["moma"]["processed"] + stats["aic"]["processed"] + stats["whitney"]["processed"]
    total_updated = stats["moma"]["updated"] + stats["aic"]["updated"] + stats["whitney"]["updated"]
    logger.info(
        f"[Tier 2] DONE | processed={total_processed}, updated={total_updated} "
        f"(MoMA: {stats['moma']['updated']}, AIC: {stats['aic']['updated']}, Whitney: {stats['whitney']['updated']})"
    )
    return stats


def _build_parser_key_mapping(html_llm_keys: set[str]) -> tuple[set[str], Dict[str, str]]:
    """Build mapping between SITES keys and DB parser_keys, including legacy names."""
    db_parser_keys: set[str] = set()
    key_to_sites_key: Dict[str, str] = {}
    for sites_key in html_llm_keys:
        parser = SITES[sites_key]
        pk = getattr(parser, "parser_key", "")
        if pk:
            db_parser_keys.add(pk)
            key_to_sites_key[pk] = sites_key
        db_parser_keys.add(sites_key)
        key_to_sites_key[sites_key] = sites_key
    return db_parser_keys, key_to_sites_key


def _add_legacy_mappings(db_parser_keys: set[str], key_to_sites_key: Dict[str, str], html_llm_keys: set[str], all_db_keys: set[str]) -> None:
    """Add known legacy parser_key mappings from older DB records."""
    legacy_map = {
        "serpentine_galleries": "serpentine",
        "tate_modern": "tate",
        "mori_art_museum": "mori",
        "m+_museum": "mplus",
        "art_institute_of_chicago": "aic",
    }
    for db_key, sites_key in legacy_map.items():
        if sites_key in html_llm_keys and db_key in all_db_keys:
            db_parser_keys.add(db_key)
            key_to_sites_key[db_key] = sites_key


def _build_missing_field_filter(fields: Optional[List[str]] = None) -> str:
    """Build SQL WHERE clause for missing field detection.

    Args:
        fields: List of field names to check. None = all fields (default behavior).
                Supported: concept, preface, curators, dates, images
    """
    if not fields:
        # Default: check all fields
        return (
            "(concept IS NULL OR concept = '' OR length(concept) < 50 "
            "OR preface IS NULL OR preface = '' OR curators = '[]' "
            "OR start_date IS NULL OR start_date = '')"
        )

    conditions = []
    for field in fields:
        if field == "concept":
            conditions.append("(concept IS NULL OR concept = '' OR length(concept) < 50)")
        elif field == "preface":
            conditions.append("(preface IS NULL OR preface = '')")
        elif field == "curators":
            conditions.append("(curators IS NULL OR curators = '[]' OR curators = '')")
        elif field in ("dates", "date"):
            conditions.append("(start_date IS NULL OR start_date = '')")
        elif field == "images":
            conditions.append("(images IS NULL OR images = '[]' OR images = '')")
    return " OR ".join(conditions) if conditions else "1=1"


def _should_update_field(field: str, parsed: Dict[str, Any], row, force: bool = False) -> bool:
    """Check if a field should be updated from parsed result.

    Args:
        field: Field name to check.
        parsed: LLM parsed result dict.
        row: sqlite3.Row from exhibitions table.
        force: If True, update even if existing value is present.
    """
    val = parsed.get(field)
    if not val:
        return False
    if field == "curators":
        if isinstance(val, list) and len(val) == 0:
            return False
    if force:
        return True
    # Only update if current value is empty/null
    existing = row[field] if field in row.keys() else None
    if existing is None or existing == "" or existing == "[]":
        return True
    return False


def enrich_tier1(db: ExhibitionDatabase, scraper: ExhibitionScraper, limit: Optional[int] = None, dry_run: bool = False, site: Optional[str] = None, fields: Optional[List[str]] = None, force_reparse: bool = False) -> Dict[str, Any]:
    """Tier 1: 重新抓取 HTML_LLM 源缺失字段。

    Args:
        fields: Target specific fields to enrich. None = all fields.
                Supported: concept, preface, curators, dates, images
        force_reparse: Bypass LLM cache and force fresh parsing.
    """
    # Temporarily disable LLM cache if force_reparse
    original_cache = scraper.parser.cache
    if force_reparse:
        scraper.parser.cache = None
        logger.info("[Tier 1] LLM cache disabled (force-reparse mode)")
    conn = db._get_connection()
    cursor = conn.cursor()

    # 查询所有 HTML_LLM 策略且缺失指定字段的记录
    html_llm_keys = {
        key for key, parser in SITES.items()
        if getattr(parser, "strategy", ParserStrategy.HTML_LLM) == ParserStrategy.HTML_LLM
    }
    if site:
        html_llm_keys = {k for k in html_llm_keys if k == site}
    if not html_llm_keys:
        logger.warning("[Tier 1] No HTML_LLM parsers found.")
        return {"processed": 0, "updated": 0, "failed": 0}

    db_parser_keys, key_to_sites_key = _build_parser_key_mapping(html_llm_keys)

    cursor.execute("SELECT DISTINCT parser_key FROM exhibitions WHERE parser_key IS NOT NULL AND parser_key != ''")
    all_db_keys = {row["parser_key"] for row in cursor.fetchall()}
    _add_legacy_mappings(db_parser_keys, key_to_sites_key, html_llm_keys, all_db_keys)

    placeholders = ",".join("?" for _ in db_parser_keys)
    field_filter = _build_missing_field_filter(fields)
    cursor.execute(
        f"""
        SELECT id, url, title, parser_key, start_date, end_date,
               concept, preface, curators, images FROM exhibitions
        WHERE parser_key IN ({placeholders})
          AND {field_filter}
        ORDER BY id DESC
        LIMIT ?
        """,
        (*db_parser_keys, limit or 999999),
    )
    rows = cursor.fetchall()
    field_desc = f" fields={fields}" if fields else ""
    logger.info(f"[Tier 1] Found {len(rows)} HTML_LLM records with missing{field_desc}")

    updated = 0
    failed = 0

    for row in rows:
        ex_id = row["id"]
        url = row["url"]
        title = row["title"]
        parser_key = row["parser_key"]
        sites_key = key_to_sites_key.get(parser_key, parser_key)
        parser = SITES.get(sites_key)

        if not parser:
            continue

        logger.info(f"[Tier 1] Processing: {title}")
        try:
            response = scraper.client.get(url, timeout=getattr(parser, "request_timeout", 60.0))
            response.raise_for_status()
            clean_text = parser.clean_html(response.text)

            if not clean_text or len(clean_text.strip()) < 100:
                logger.warning(f"[Tier 1] Content too short: {url}")
                failed += 1
                continue

            parsed = scraper.parser.parse_exhibition_text(clean_text, parser.source, parser.city)
            if not parsed:
                logger.warning(f"[Tier 1] LLM returned None: {url}")
                failed += 1
                continue

            # 组装更新字段 — 只更新目标字段
            updates = {}
            target_fields = fields or ["concept", "preface", "curators", "images", "start_date", "end_date"]
            for field in target_fields:
                if field in ("start_date", "end_date"):
                    if parsed.get(field) and not row[field]:
                        updates[field] = parsed[field]
                elif field == "dates":
                    for df in ("start_date", "end_date"):
                        if parsed.get(df) and not row[df]:
                            updates[df] = parsed[df]
                elif field == "curators":
                    val = parsed.get("curators")
                    if val and isinstance(val, list) and len(val) > 0:
                        existing = row["curators"]
                        if not existing or existing == "[]" or existing == "":
                            updates["curators"] = json.dumps(val, ensure_ascii=False)
                elif field == "images":
                    imgs = parsed.get("images")
                    if imgs:
                        existing = row["images"]
                        if not existing or existing == "[]" or existing == "":
                            if isinstance(imgs, list):
                                updates["images"] = json.dumps(imgs, ensure_ascii=False)
                            elif isinstance(imgs, str):
                                updates["images"] = imgs
                elif field == "concept":
                    val = parsed.get("concept")
                    if val and len(val.strip()) >= 20:
                        existing = row["concept"]
                        if not existing or existing == "" or len(existing) < 50:
                            updates["concept"] = val
                elif field == "preface":
                    val = parsed.get("preface")
                    if val and len(val.strip()) >= 10:
                        existing = row["preface"]
                        if not existing or existing == "":
                            updates["preface"] = val

            if not updates:
                logger.info(f"[Tier 1] No new fields extracted: {url}")
                failed += 1
                continue

            if dry_run:
                logger.info(f"[Tier 1] [DRY-RUN] Would update {title}: {list(updates.keys())}")
                updated += 1
            else:
                set_clause = ", ".join(f"{k} = ?" for k in updates)
                cursor.execute(
                    f"UPDATE exhibitions SET {set_clause} WHERE id = ?",
                    (*updates.values(), ex_id),
                )
                conn.commit()
                logger.info(f"[Tier 1] Updated {title}: {list(updates.keys())}")
                updated += 1

        except Exception as e:
            logger.error(f"[Tier 1] Error processing {title}: {e}")
            failed += 1

    # Restore LLM cache
    if force_reparse:
        scraper.parser.cache = original_cache

    conn.close()
    logger.info(f"[Tier 1] DONE | processed={len(rows)}, updated={updated}, failed={failed}")
    return {"processed": len(rows), "updated": updated, "failed": failed}


def enrich_tier3(db: ExhibitionDatabase, scraper: ExhibitionScraper, limit: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Tier 3: Image 统一提取。"""
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, url, title, parser_key, source FROM exhibitions
        WHERE (images IS NULL OR images = '[]')
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit or 999999,),
    )
    rows = cursor.fetchall()
    logger.info(f"[Tier 3] Found {len(rows)} records missing images")

    updated = 0
    failed = 0

    for row in rows:
        ex_id = row["id"]
        url = row["url"]
        title = row["title"]
        parser_key = row["parser_key"]
        source = row["source"]

        image_urls: List[str] = []

        # HTML_LLM 源：重新抓取页面提取图片
        if parser_key and parser_key in SITES:
            parser = SITES[parser_key]
            strategy = getattr(parser, "strategy", ParserStrategy.HTML_LLM)
            if strategy == ParserStrategy.HTML_LLM:
                try:
                    response = scraper.client.get(url, timeout=getattr(parser, "request_timeout", 60.0))
                    if response.status_code == 200:
                        image_urls = extract_images_from_html(response.text, url, max_images=8)
                except Exception as e:
                    logger.warning(f"[Tier 3] Failed to fetch {url}: {e}")

        # AIC：尝试从 URL 提取 exhibition ID，调 API 取 image_url
        if source == "Art Institute of Chicago" and not image_urls:
            try:
                if "/exhibitions/" in url:
                    aic_id = url.split("/exhibitions/")[-1].split("/")[0].split("?")[0].split("#")[0]
                    if aic_id.isdigit():
                        import httpx
                        api_url = f"https://api.artic.edu/api/v1/exhibitions/{aic_id}"
                        resp = httpx.get(api_url, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json().get("data", {})
                            img = data.get("image_url")
                            if img:
                                image_urls = [img]
            except Exception as e:
                logger.warning(f"[Tier 3] AIC API error for {url}: {e}")

        if not image_urls:
            failed += 1
            continue

        if dry_run:
            logger.info(f"[Tier 3] [DRY-RUN] Would update '{title}' with {len(image_urls)} images")
            updated += 1
        else:
            cursor.execute(
                "UPDATE exhibitions SET images = ? WHERE id = ?",
                (json.dumps(image_urls, ensure_ascii=False), ex_id),
            )
            conn.commit()
            logger.info(f"[Tier 3] Updated '{title}' with {len(image_urls)} images")
            updated += 1

    conn.close()
    logger.info(f"[Tier 3] DONE | processed={len(rows)}, updated={updated}, failed={failed}")
    return {"processed": len(rows), "updated": updated, "failed": failed}


def main():
    parser = argparse.ArgumentParser(description="Enrich exhibition records with missing fields")
    parser.add_argument("--tier", choices=["1", "2", "3", "all"], default="all", help="Which tier to run")
    parser.add_argument("--site", help="Limit to a specific parser_key (Tier 1/3 only)")
    parser.add_argument("--fields", help="Comma-separated fields to enrich (Tier 1 only): concept,preface,curators,dates,images")
    parser.add_argument("--force-reparse", action="store_true", help="Bypass LLM cache and force fresh parsing (Tier 1 only)")
    parser.add_argument("--limit", type=int, help="Max records per tier")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing")
    parser.add_argument("--db", default="exhibitions.db", help="Database path")
    args = parser.parse_args()

    db = ExhibitionDatabase(args.db)
    scraper = None
    if args.tier in ("1", "3", "all"):
        scraper = ExhibitionScraper()

    fields = args.fields.split(",") if args.fields else None
    tiers_to_run = ["1", "2", "3"] if args.tier == "all" else [args.tier]
    all_stats = {}

    for tier in tiers_to_run:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running Tier {tier}")
        logger.info(f"{'='*50}")
        if tier == "1" and scraper:
            stats = enrich_tier1(db, scraper, limit=args.limit, dry_run=args.dry_run, site=args.site, fields=fields, force_reparse=args.force_reparse)
        elif tier == "2":
            stats = enrich_tier2(db, limit=args.limit, dry_run=args.dry_run)
        elif tier == "3" and scraper:
            stats = enrich_tier3(db, scraper, limit=args.limit, dry_run=args.dry_run)
        else:
            continue
        all_stats[f"tier{tier}"] = stats

    if scraper:
        scraper.close()

    logger.info(f"\n{'='*50}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*50}")
    for name, stats in all_stats.items():
        logger.info(f"{name}: {stats}")


if __name__ == "__main__":
    main()
