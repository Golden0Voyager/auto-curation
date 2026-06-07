import logging
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.whitney")

WHITNEY_API_BASE = "https://whitney.org/api/exhibitions"


class WhitneyParser:
    """Whitney Museum of American Art API Parser.

    Uses Whitney's public REST API to fetch exhibition history.
    No API key required. Paginated at 30 items per page.
    """

    source = "Whitney Museum of American Art"
    city = "New York"
    strategy = ParserStrategy.REST_API
    parser_key = "whitney"
    list_url = WHITNEY_API_BASE

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        return [WHITNEY_API_BASE]

    def get_exhibition_urls(self, client: httpx.Client, since_year: int | None = None) -> list[str]:
        return []

    def get_api_exhibitions(
        self, since_year: int | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetches exhibitions from Whitney API with pagination."""
        client = httpx.Client(timeout=30.0, follow_redirects=True)
        exhibitions = []
        page = 1

        logger.info(
            f"[Whitney] Fetching exhibitions from API (since_year={since_year}, limit={limit})"
        )

        try:
            while True:
                if limit and len(exhibitions) >= limit:
                    break

                url = f"{WHITNEY_API_BASE}?page={page}"
                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"[Whitney] API request failed at page {page}: {e}")
                    break

                data = resp.json()
                items = data.get("data", [])

                if not items:
                    break

                for ex in items:
                    if limit and len(exhibitions) >= limit:
                        break

                    attrs = ex.get("attributes", {})
                    title = (attrs.get("title") or "").strip()
                    start_time = attrs.get("start_time", "") or ""
                    end_time = attrs.get("end_time", "") or ""
                    if not title:
                        continue

                    # Apply year filter
                    if since_year and start_time:
                        try:
                            begin_year = int(start_time[:4])
                            if begin_year < since_year:
                                continue
                        except (ValueError, IndexError):
                            pass

                    # Clean HTML from primary_text
                    raw_text = attrs.get("primary_text", "") or ""
                    preface = None
                    if raw_text:
                        soup = BeautifulSoup(raw_text, "html.parser")
                        preface = soup.get_text(separator="\n").strip() or None

                    ex_url = attrs.get("url", "")
                    if ex_url and not ex_url.startswith("http"):
                        ex_url = f"https://whitney.org{ex_url}"
                    if not ex_url:
                        ex_url = f"https://whitney.org/exhibitions/{ex.get('id', '')}"

                    exhibitions.append(
                        {
                            "source": self.source,
                            "title": title,
                            "preface": preface,
                            "concept": None,
                            "curators": [],
                            "start_date": start_time[:10] if start_time else None,
                            "end_date": end_time[:10] if end_time else None,
                            "location": "Whitney Museum of American Art",
                            "city": self.city,
                            "url": ex_url,
                            "artworks": [],
                        }
                    )

                logger.info(
                    f"[Whitney] Page {page}: fetched {len(items)} exhibitions, total so far: {len(exhibitions)}"
                )
                page += 1
                time.sleep(0.3)

        finally:
            client.close()

        logger.info(f"[Whitney] Done. Total exhibitions fetched: {len(exhibitions)}")
        return exhibitions

    def clean_html(self, html: str) -> str:
        return html
