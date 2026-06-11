"""
MoMA GitHub Open Dataset Parser.

MoMA 官方在 GitHub 上以 CC0 协议公开了其完整展览历史数据（1929-至今）。
我们直接从 GitHub raw CSV 下载并解析，不需要任何网页抓取，数据质量更高且无任何反爬风险。

数据集地址: https://github.com/MuseumofModernArt/exhibitions
"""

import csv
import io
import logging
from typing import Any

import httpx

from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.moma")

# MoMA 开放数据集 GitHub Raw URL（网络备用）
MOMA_EXHIBITIONS_CSV_URL = "https://raw.githubusercontent.com/MuseumofModernArt/exhibitions/master/MoMAExhibitions1929to1989.csv"

# 本地缓存路径（优先使用，避免网络依赖）
MOMA_LOCAL_CSV_PATH = "data/moma_github/MoMAExhibitions1929to1989.csv"

# MoMA 网站详情页 URL 模板（用于生成记录的 url 字段，实现数据库唯一性）
MOMA_EXHIBITION_BASE_URL = "https://www.moma.org/calendar/exhibitions/{id}"


class MoMAParser:
    """MoMA Open Dataset Parser.

    通过解析 MoMA 官方 GitHub 数据集获取结构化展览数据，
    而非网页爬取。数据涵盖 1929-1989 年的完整展览历史。
    """

    source = "MoMA"
    city = "New York"
    strategy = ParserStrategy.CSV_REMOTE
    parser_key = "moma"
    institution_type = "museum"
    # MoMA 使用 CSV 而非网页，此字段仅作标识
    list_url = MOMA_EXHIBITIONS_CSV_URL

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        return [MOMA_EXHIBITIONS_CSV_URL]

    def get_exhibition_urls(self, client: httpx.Client, since_year: int | None = None) -> list[str]:
        """Returns a placeholder list for compatibility. MoMA uses get_csv_exhibitions()."""
        logger.info(
            "[MoMA] Using GitHub open dataset (not web scraping). Use get_csv_exhibitions() directly."
        )
        return []

    def get_csv_exhibitions(self, since_year: int | None = None) -> list[dict[str, Any]]:
        """Reads and parses MoMA exhibition CSV dataset.

        Prefers local cached file (data/moma_github/) for speed and offline support.
        Falls back to HTTP download from GitHub if local file is not available.

        Args:
            since_year: If provided, only returns exhibitions from this year onwards.

        Returns:
            List of dicts, each representing a structured exhibition record ready for DB insertion.
        """
        import os

        try:
            # 优先使用本地缓存文件
            if os.path.exists(MOMA_LOCAL_CSV_PATH):
                logger.info(f"[MoMA] Reading from local cache: {MOMA_LOCAL_CSV_PATH}")
                with open(MOMA_LOCAL_CSV_PATH, encoding="latin-1") as f:
                    csv_text = f.read()
                logger.info(f"[MoMA] Local file loaded ({len(csv_text)} chars). Parsing...")
            else:
                # 本地文件不存在，从 GitHub 下载
                logger.info("[MoMA] Local cache not found. Downloading from GitHub...")
                client = httpx.Client(timeout=60.0, follow_redirects=True)
                response = client.get(
                    MOMA_EXHIBITIONS_CSV_URL,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; auto_curation bot)"},
                )
                response.raise_for_status()
                client.close()
                csv_text = response.content.decode("latin-1")
                logger.info(f"[MoMA] Downloaded ({len(csv_text)} chars). Parsing...")
                # 自动保存到本地以供下次使用
                os.makedirs(os.path.dirname(MOMA_LOCAL_CSV_PATH), exist_ok=True)
                with open(MOMA_LOCAL_CSV_PATH, "w", encoding="latin-1") as f:
                    f.write(csv_text)
                logger.info(f"[MoMA] Saved to local cache: {MOMA_LOCAL_CSV_PATH}")

            reader = csv.DictReader(io.StringIO(csv_text))

            # Two-pass: first group all rows by ExhibitionID, then build exhibition records
            # CSV has one row per artist per exhibition, so we must aggregate.
            from collections import OrderedDict

            groups: dict = OrderedDict()  # ExhibitionID -> exhibition dict

            for row in reader:
                ex_id = row.get("ExhibitionID", "").strip()
                title = row.get("ExhibitionTitle", "").strip()
                if not ex_id or not title:
                    continue

                # Get exhibition-level fields from the first row of each ExhibitionID group
                if ex_id not in groups:
                    begin_date = row.get("ExhibitionBeginDate", row.get("BeginDate", "")).strip()
                    end_date = row.get("ExhibitionEndDate", row.get("EndDate", "")).strip()
                    ex_url = row.get("ExhibitionURL", row.get("URL", "")).strip()

                    # Normalize URL
                    if ex_url and not ex_url.startswith("http"):
                        ex_url = "https://www." + ex_url
                    if not ex_url:
                        ex_url = MOMA_EXHIBITION_BASE_URL.format(id=ex_id)

                    # Apply year filter
                    if since_year and begin_date:
                        try:
                            begin_year = (
                                int(begin_date.split("/")[-1])
                                if "/" in begin_date
                                else int(begin_date[:4])
                            )
                            if begin_year < since_year:
                                continue
                        except (ValueError, IndexError):
                            pass

                    groups[ex_id] = {
                        "source": self.source,
                        "title": title,
                        "preface": None,
                        "concept": None,
                        "curators": [],
                        "start_date": begin_date,
                        "end_date": end_date,
                        "location": "MoMA",
                        "city": self.city,
                        "url": ex_url,
                        "artworks": [],
                    }

                # Skip if this exhibition was filtered by year
                if ex_id not in groups:
                    continue

                # Add artist/curator information from this row
                display_name = row.get("DisplayName", "").strip()
                role = row.get("ExhibitionRole", "").strip()
                nationality = row.get("Nationality", "").strip()
                birth_year = row.get("ConstituentBeginDate", "").strip()
                death_year = row.get("ConstituentEndDate", "").strip()

                if not display_name:
                    continue

                if "Curator" in role or "Director" in role or "Organiz" in role:
                    # Add as curator if not already present
                    if display_name not in groups[ex_id]["curators"]:
                        groups[ex_id]["curators"].append(display_name)
                elif "Artist" in role or not role:
                    # Add as artwork entry
                    caption_parts = [display_name]
                    if nationality:
                        caption_parts.append(nationality)
                    if birth_year or death_year:
                        life = f"{birth_year}–{death_year}".strip("–")
                        caption_parts.append(life)

                    groups[ex_id]["artworks"].append(
                        {
                            "artist_name": display_name,
                            "work_title": title,
                            "work_year": groups[ex_id]["start_date"][:4]
                            if groups[ex_id]["start_date"]
                            else None,
                            "medium": None,
                            "dimensions": None,
                            "caption": ", ".join(caption_parts) if caption_parts else None,
                        }
                    )

            exhibitions = list(groups.values())
            logger.info(
                f"[MoMA] Parsed {len(exhibitions)} exhibitions from dataset (since_year={since_year})."
            )
            return exhibitions

        except Exception as e:
            logger.error(f"[MoMA] Failed to download or parse GitHub dataset: {e}", exc_info=True)
            return []

    def clean_html(self, html: str) -> str:
        """Not used for MoMA CSV dataset mode."""
        return html
