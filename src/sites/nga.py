"""
National Gallery of Art (NGA) Open Data Parser.

NGA 通过 GitHub 以 CC0 协议发布了完整馆藏数据集，包含：
- 145,655 件作品（含 medium、dimensions 字段）
- 多个关联表：constituents（艺术家）、objects_constituents（关联）、objects_dimensions（尺寸详表）

GitHub: https://github.com/NationalGalleryOfArt/opendata
本地路径: data/nga_collection/
"""

import csv
import logging
import os
from typing import Any

from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.nga")

NGA_LOCAL_DIR = "data/nga_collection"
NGA_OBJECTS_PATH = f"{NGA_LOCAL_DIR}/objects.csv"
NGA_CONSTITUENTS_PATH = f"{NGA_LOCAL_DIR}/constituents.csv"
NGA_OBJECTS_CONSTITUENTS_PATH = f"{NGA_LOCAL_DIR}/objects_constituents.csv"
NGA_DIMENSIONS_PATH = f"{NGA_LOCAL_DIR}/objects_dimensions.csv"

NGA_GITHUB_BASE = "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data"


class NGAParser:
    """National Gallery of Art CSV Parser.

    从本地 NGA 数据集构建结构化展览/作品记录。
    NGA 数据集是纯作品数据（无展览历史），因此我们将其以
    「按艺术家聚合的专题组」形式注入 artworks 表，配合 Met/MoMA 展览数据使用。
    """

    source = "National Gallery of Art"
    city = "Washington D.C."
    strategy = ParserStrategy.ARTWORK_ONLY
    parser_key = "nga"
    institution_type = "museum"
    list_url = NGA_OBJECTS_PATH

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        return [NGA_OBJECTS_PATH]

    def get_exhibition_urls(self, client, since_year: int | None = None) -> list[str]:
        """Compatibility stub — NGA uses get_csv_artworks() directly."""
        return []

    def _ensure_local_files(self) -> bool:
        """Check that local CSV files exist."""
        if not os.path.exists(NGA_OBJECTS_PATH):
            logger.error(f"[NGA] Local data not found: {NGA_OBJECTS_PATH}")
            logger.error(f"[NGA] Please download from: {NGA_GITHUB_BASE}/objects.csv")
            return False
        return True

    def get_csv_artworks(
        self,
        since_year: int | None = None,
        classification: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Loads and parses NGA artwork records from local CSV.

        Joins objects → objects_constituents → constituents to attach
        artist names and biographical data to each artwork.

        Args:
            since_year: Filter artworks created from this year onwards (beginyear).
            classification: Filter by artwork type (e.g. 'Painting', 'Sculpture').
            limit: Max records to return.

        Returns:
            List of artwork dicts with full artist metadata.
        """
        if not self._ensure_local_files():
            return []

        logger.info("[NGA] Loading constituents index...")
        constituents: dict[str, dict] = {}
        if os.path.exists(NGA_CONSTITUENTS_PATH):
            with open(NGA_CONSTITUENTS_PATH, encoding="utf-8", errors="replace") as f:
                for row in csv.DictReader(f):
                    cid = row.get("constituentid", "")
                    if cid:
                        constituents[cid] = row

        logger.info("[NGA] Loading object→constituent links...")
        obj_to_artists: dict[str, list[dict]] = {}
        if os.path.exists(NGA_OBJECTS_CONSTITUENTS_PATH):
            with open(NGA_OBJECTS_CONSTITUENTS_PATH, encoding="utf-8", errors="replace") as f:
                for row in csv.DictReader(f):
                    oid = row.get("objectid", "")
                    cid = row.get("constituentid", "")
                    if oid and cid and cid in constituents:
                        c = constituents[cid]
                        if oid not in obj_to_artists:
                            obj_to_artists[oid] = []
                        obj_to_artists[oid].append(
                            {
                                "name": c.get("displayname", ""),
                                "nationality": c.get("nationality", ""),
                                "birth": c.get("beginyear", ""),
                                "death": c.get("endyear", ""),
                                "role": row.get("role", ""),
                            }
                        )

        logger.info(
            f"[NGA] Loading objects (since_year={since_year}, classification={classification})..."
        )
        artworks: list[dict[str, Any]] = []
        with open(NGA_OBJECTS_PATH, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if limit and len(artworks) >= limit:
                    break

                # Year filter
                begin_year = row.get("beginyear", "").strip()
                if since_year and begin_year:
                    try:
                        if int(begin_year) < since_year:
                            continue
                    except ValueError:
                        pass

                # Classification filter
                cls = row.get("classification", "").strip()
                if classification and classification.lower() not in cls.lower():
                    continue

                obj_id = row.get("objectid", "")
                title = row.get("title", "").strip()
                if not title:
                    continue

                # Attach artists
                artists = obj_to_artists.get(obj_id, [])
                primary_artist = artists[0] if artists else {}
                artist_name = primary_artist.get("name", "Unknown")
                nat = primary_artist.get("nationality", "")
                birth = primary_artist.get("birth", "")
                death = primary_artist.get("death", "")

                caption_parts = [artist_name]
                if nat:
                    caption_parts.append(nat)
                if birth or death:
                    caption_parts.append(f"{birth}–{death}".strip("–"))

                artworks.append(
                    {
                        "source": self.source,
                        "artist_name": artist_name,
                        "work_title": title,
                        "work_year": row.get("displaydate", begin_year),
                        "medium": row.get("medium", "").strip() or None,
                        "dimensions": row.get("dimensions", "").strip() or None,
                        "caption": ", ".join(caption_parts),
                        "classification": cls,
                        "url": f"https://www.nga.gov/collection/art-object-page.{obj_id}.html",
                        "all_artists": artists,
                    }
                )

        logger.info(f"[NGA] Loaded {len(artworks):,} artworks.")
        return artworks

    def clean_html(self, html: str) -> str:
        return html
