"""
Art Institute of Chicago (AIC) API Parser.

AIC 提供完全免费、无需 API Key 的 REST API，包含：
- 131,945 件馆藏作品（当代艺术重点）
- 6,253 个历史展览记录（含日期、艺术家、描述）

API 文档: https://api.artic.edu/docs/
展览端点: https://api.artic.edu/api/v1/exhibitions
"""

import logging
import time
from typing import Any

import httpx

from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.aic")

AIC_API_BASE = "https://api.artic.edu/api/v1"
AIC_EXHIBITIONS_URL = f"{AIC_API_BASE}/exhibitions"
AIC_ARTWORKS_URL = f"{AIC_API_BASE}/artworks"

HEADERS = {
    "User-Agent": "auto_curation/1.0 (research project; contact via GitHub)",
    "AIC-User-Agent": "auto_curation/1.0",
}

EXHIBITION_FIELDS = "id,title,description,short_description,aic_start_at,aic_end_at,artist_titles,artwork_titles,gallery_title,web_url,image_url,status"
ARTWORK_FIELDS = "id,title,artist_display,artist_id,date_display,date_start,date_end,medium_display,dimensions,department_title,artwork_type_title,place_of_origin,image_id,web_url"


class AICParser:
    """Art Institute of Chicago API Parser.

    抓取 AIC 的展览历史（6,253 个）及关联的当代艺术作品数据。
    无需 API Key，直接调用公开端点。
    """

    source = "Art Institute of Chicago"
    city = "Chicago"
    strategy = ParserStrategy.REST_API
    parser_key = "aic"
    institution_type = "museum"
    list_url = AIC_EXHIBITIONS_URL

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        return [AIC_EXHIBITIONS_URL]

    def get_exhibition_urls(self, client: httpx.Client, since_year: int | None = None) -> list[str]:
        """Compatibility stub — AIC uses get_api_exhibitions() directly."""
        return []

    def get_api_exhibitions(
        self,
        since_year: int | None = None,
        limit: int | None = None,
        department: str = "Contemporary Art",
    ) -> list[dict[str, Any]]:
        """Fetches exhibitions from AIC API with pagination.

        Args:
            since_year: Only return exhibitions from this year onwards.
            limit: Max number of exhibitions to fetch.
            department: Filter keyword (not enforced by API, applied post-fetch).

        Returns:
            List of structured exhibition dicts ready for DB insertion.
        """
        client = httpx.Client(timeout=30.0, follow_redirects=True, headers=HEADERS)
        exhibitions: list[dict[str, Any]] = []
        page = 1
        page_size = 100

        logger.info(f"[AIC] Fetching exhibitions from API (since_year={since_year}, limit={limit})")

        try:
            while True:
                if limit and len(exhibitions) >= limit:
                    break

                url = f"{AIC_EXHIBITIONS_URL}?limit={page_size}&page={page}&fields={EXHIBITION_FIELDS}"
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"[AIC] API request failed at page {page}: {e}")
                    break

                data = resp.json()
                items = data.get("data", [])
                total_pages = data.get("pagination", {}).get("total_pages", 1)

                if not items:
                    break

                for ex in items:
                    if limit and len(exhibitions) >= limit:
                        break

                    title = (ex.get("title") or "").strip()
                    start_date = ex.get("aic_start_at", "") or ""
                    end_date = ex.get("aic_end_at", "") or ""
                    if not title:
                        continue

                    # Apply year filter
                    if since_year and start_date:
                        try:
                            begin_year = int(start_date[:4])
                            if begin_year < since_year:
                                continue
                        except (ValueError, IndexError):
                            pass

                    # Build artist list as artworks entries
                    artist_titles = ex.get("artist_titles") or []
                    artwork_titles = ex.get("artwork_titles") or []

                    artworks = []
                    for i, artist in enumerate(artist_titles):
                        work_title = artwork_titles[i] if i < len(artwork_titles) else title
                        artworks.append(
                            {
                                "artist_name": artist,
                                "work_title": work_title,
                                "work_year": start_date[:4] if start_date else None,
                                "medium": None,
                                "dimensions": None,
                                "caption": artist,
                            }
                        )

                    ex_url = ex.get("web_url") or f"https://www.artic.edu/exhibitions/{ex['id']}"

                    exhibitions.append(
                        {
                            "source": self.source,
                            "title": title,
                            "preface": ex.get("description") or ex.get("short_description"),
                            "concept": None,
                            "curators": [],
                            "start_date": start_date[:10] if start_date else None,
                            "end_date": end_date[:10] if end_date else None,
                            "location": ex.get("gallery_title") or "Art Institute of Chicago",
                            "city": self.city,
                            "url": ex_url,
                            "artworks": artworks,
                        }
                    )

                logger.info(
                    f"[AIC] Page {page}/{total_pages}: fetched {len(items)} exhibitions, total so far: {len(exhibitions)}"
                )

                if page >= total_pages:
                    break
                page += 1
                time.sleep(0.2)  # Polite rate limiting

        finally:
            client.close()

        logger.info(f"[AIC] Done. Total exhibitions fetched: {len(exhibitions)}")
        return exhibitions

    def clean_html(self, html: str) -> str:
        return html
