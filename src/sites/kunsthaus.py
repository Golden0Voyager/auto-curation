import json
import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.kunsthaus")


class KunsthausParser:
    """Kunsthaus Zürich.

    瑞士苏黎世顶级美术馆。展览页嵌入了 JSON-LD (schema.org/ExhibitionEvent)
    结构化数据，可直接解析，无需 LLM。
    """

    source = "Kunsthaus Zürich"
    city = "Zürich"
    strategy = ParserStrategy.HTML_LLM
    parser_key = "kunsthaus"
    institution_type = "museum"
    list_url = "https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/"
    link_patterns = [
        r"kunsthaus\.ch/en/besuch-planen/ausstellungen/[^/]+/$",
    ]

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        return [self.list_url]

    def get_exhibition_urls(self, client: httpx.Client, since_year: int | None = None) -> list[str]:
        urls = set()
        for url in self.get_list_urls(since_year):
            try:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"[Kunsthaus Zürich] Error fetching listing page {url}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = str(a["href"])
                if href.startswith("/"):
                    href = f"https://www.kunsthaus.ch{href}"
                for pattern in self.link_patterns:
                    if re.search(pattern, href):
                        urls.add(href)
                        break

        logger.info(f"[Kunsthaus Zürich] Total discovered: {len(urls)} exhibition URLs.")
        return sorted(urls)

    def parse_exhibition_page(self, client: httpx.Client, url: str) -> dict[str, Any] | None:
        """Fetch a single exhibition page and extract JSON-LD ExhibitionEvent data."""
        try:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[Kunsthaus Zürich] Failed to fetch {url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all JSON-LD scripts
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            # Handle both single object and list of objects
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "ExhibitionEvent":
                    return self._normalize_exhibition(item, url)

        logger.warning(f"[Kunsthaus Zürich] No JSON-LD ExhibitionEvent found at {url}")
        return None

    def _normalize_exhibition(self, data: dict[str, Any], url: str) -> dict[str, Any]:
        """Convert JSON-LD ExhibitionEvent to our schema."""
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        start_date = data.get("startDate")
        end_date = data.get("endDate")

        # Clean up dates to ISO 8601 YYYY-MM-DD
        if start_date and isinstance(start_date, str):
            start_date = start_date[:10]
        if end_date and isinstance(end_date, str):
            end_date = end_date[:10]

        return {
            "source": self.source,
            "title": name,
            "preface": description or None,
            "concept": None,
            "curators": [],
            "start_date": start_date,
            "end_date": end_date,
            "location": "Kunsthaus Zürich",
            "city": self.city,
            "url": url,
            "artworks": [],
        }

    def clean_html(self, html: str) -> str:
        return html
