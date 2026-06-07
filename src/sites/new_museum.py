import logging
import re
from typing import Any

from src.sites.base import BaseSiteParser

logger = logging.getLogger("auto_curation.sites.new_museum")

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False


class NewMuseumParser(BaseSiteParser):
    """New Museum - New York.

    纽约新当代艺术博物馆，专注展示国际当代艺术新作。
    注意：网站基于 Next.js SPA，静态 HTML 几乎无内容，需要 Playwright 渲染。
    列表页和详情页均需 Playwright。
    """

    source = "New Museum"
    city = "New York"
    parser_key = "new_museum"
    institution_type = "museum"
    list_url = "https://www.newmuseum.org/exhibitions"
    use_playwright = True
    link_patterns = [
        r"newmuseum\.org/exhibition/[^/]+",
    ]

    def parse_exhibition_page(self, client, url: str) -> dict[str, Any] | None:
        """Use Playwright to render the SPA exhibition page and extract structured data."""
        if not HAS_PLAYWRIGHT:
            logger.error("[New Museum] Playwright is required but not installed.")
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                html = page.content()
                browser.close()
        except Exception as e:
            logger.error(f"[New Museum] Playwright failed to load {url}: {e}")
            return None

        return self._extract_from_html(html, url)

    def _extract_from_html(self, html: str, url: str) -> dict[str, Any] | None:
        text = re.sub(r"<[^>]+>", " ", html)
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Title: first <h1>
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        title = ""
        if h1_match:
            title = re.sub(r"<[^>]+>", " ", h1_match.group(1)).strip()

        if not title:
            logger.warning(f"[New Museum] No title found for {url}")
            return None

        # 2. Date range: patterns like "March 21, 2026–Ongoing" or "November 28, 2024–February 2, 2025"
        date_match = re.search(
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4})\s*[-–—]\s*(Ongoing|[A-Za-z]+\s+\d{1,2},\s+\d{4})", text
        )
        start_date = end_date = None
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
            if end_date.lower() == "ongoing":
                end_date = None

        # 3. Preface: find a paragraph > 80 chars near the title
        preface = None
        for line in lines:
            if len(line) > 80 and not any(
                k in line
                for k in [
                    "Skip To",
                    "Home Page",
                    "Visitor Guidelines",
                    "Accessibility",
                    "Tours",
                    "Restaurant",
                    "Exhibitions",
                    "Events",
                    "Learn",
                    "About",
                    "Support",
                    "Shop",
                    "SEARCH",
                    "TICKETS",
                    "New Museum Home Page",
                ]
            ):
                preface = line
                break

        # 4. Curator
        curators = []
        curator_match = re.search(r"curated by\s+([^,]+(?:,\s*[^,]+)*)", text, re.IGNORECASE)
        if curator_match:
            curators = [
                c.strip()
                for c in curator_match.group(1).split(",")
                if c.strip() and "Curator" not in c
            ]

        return {
            "source": self.source,
            "title": title,
            "preface": preface,
            "concept": None,
            "curators": curators,
            "start_date": start_date,
            "end_date": end_date,
            "location": "New Museum",
            "city": self.city,
            "url": url,
            "artworks": [],
        }
