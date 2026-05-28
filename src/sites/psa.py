import logging
import re
from typing import List, Optional, Dict, Any

from src.sites.base import BaseSiteParser, ParserStrategy

logger = logging.getLogger("auto_curation.sites.psa")

# Playwright is an optional dependency for SPA scraping
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False


class PSAParser:
    """Power Station of Art (PSA) - Shanghai.

    上海当代艺术博物馆，中国大陆首家公立当代艺术馆。
    官网为 React SPA，必须使用 Playwright 渲染后才能提取内容。
    """
    source = "Power Station of Art"
    city = "Shanghai"
    strategy = ParserStrategy.HTML_LLM
    parser_key = "psa"
    use_playwright = True
    list_url = "https://www.powerstationofart.com/whats-on/exhibitions"
    link_patterns = [
        r"/whats-on/exhibitions/[^/]+$",
    ]

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        return [self.list_url]

    def get_exhibition_urls(self, client, since_year: Optional[int] = None) -> List[str]:
        """Use Playwright to render the SPA and discover exhibition URLs."""
        if not HAS_PLAYWRIGHT:
            logger.error(
                "[PSA] Playwright is required for PSA scraping but not installed. "
                "Install it with: uv pip install playwright && python -m playwright install chromium"
            )
            return []

        urls = set()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.list_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                html = page.content()
                browser.close()
        except Exception as e:
            logger.error(f"[PSA] Playwright failed to load listing page: {e}")
            return []

        for href in re.findall(r'href="(/whats-on/exhibitions/[^"]+)"', html):
            if href == "/whats-on/exhibitions":
                continue
            urls.add(f"https://www.powerstationofart.com{href}")

        logger.info(f"[PSA] Total discovered: {len(urls)} exhibition URLs.")
        return sorted(urls)

    def parse_exhibition_page(self, client, url: str) -> Optional[Dict[str, Any]]:
        """Use Playwright to render the SPA exhibition page and extract structured data."""
        if not HAS_PLAYWRIGHT:
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
            logger.error(f"[PSA] Playwright failed to load {url}: {e}")
            return None

        return self._extract_from_html(html, url)

    def _extract_from_html(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        text = re.sub(r'<[^>]+>', ' ', html)
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # 1. Title: first <h1>
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        title = ""
        if h1_match:
            title = re.sub(r'<[^>]+>', ' ', h1_match.group(1)).strip()

        if not title:
            logger.warning(f"[PSA] No title found for {url}")
            return None

        # 2. Date range: patterns like 2025/11/25 — 2026/05/05
        date_match = re.search(
            r'(\d{4}[\./-]\d{1,2}[\./-]\d{1,2})\s*[-–—]\s*(\d{4}[\./-]\d{1,2}[\./-]\d{1,2})',
            text
        )
        start_date = end_date = None
        if date_match:
            start_date = date_match.group(1).replace('/', '-').replace('.', '-')
            end_date = date_match.group(2).replace('/', '-').replace('.', '-')

        # 3. Location
        location = "上海当代艺术博物馆"
        loc_match = re.search(r'地点\s+([^\n\r]{2,60})', text)
        if loc_match:
            location = loc_match.group(1).strip()

        # 4. Curator
        curators = []
        curator_match = re.search(r'策展人\s+([^\n\r]{2,30})', text)
        if curator_match:
            curators = [curator_match.group(1).strip()]

        # 5. Preface: first substantial paragraph after title
        # Find the first paragraph that is > 80 chars and doesn't contain navigation keywords
        preface = None
        for line in lines:
            if len(line) > 80 and '展览' in line and not any(k in line for k in ['关于PSA', '参观购票', '沪ICP', 'Power Station of Art']):
                preface = line
                break

        return {
            "source": self.source,
            "title": title,
            "preface": preface,
            "concept": None,
            "curators": curators,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "city": self.city,
            "url": url,
            "artworks": [],
        }

    def clean_html(self, html: str) -> str:
        return html
