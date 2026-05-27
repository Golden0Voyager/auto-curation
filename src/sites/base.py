import logging
import re
from enum import Enum
from typing import List, Set, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger("auto_curation.sites.base")

# Playwright is an optional dependency for SPA scraping
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


class ParserStrategy(Enum):
    """Scraping strategy for a parser. Determines which pipeline the scraper uses."""
    HTML_LLM = "html_llm"        # Default: scrape HTML, send to LLM
    CSV_LOCAL = "csv_local"      # Parse local CSV file
    CSV_REMOTE = "csv_remote"    # Download and parse remote CSV
    REST_API = "rest_api"        # Call REST API endpoint
    SPARQL = "sparql"            # Wikidata-style SPARQL
    ARTWORK_ONLY = "artwork_only"  # No exhibitions, only artworks (e.g. NGA)


class BaseSiteParser:
    """Base class for all art institution site crawlers.

    Supports multi-page and historical archive crawling via the `list_urls` property.
    Subclasses can override `list_urls` to return a dynamic list of pages (e.g., by year).
    """

    source: str = "Generic"
    city: str = "Generic"
    list_url: str = ""
    strategy: ParserStrategy = ParserStrategy.HTML_LLM
    parser_key: str = ""  # Registration key; falls back to derived class name
    institution_type: str = "museum"  # museum, biennial, triennial, gallery

    # Additional archive/historical listing URLs (e.g., past exhibitions pages)
    extra_list_urls: List[str] = []

    # URL patterns or prefixes to match for detailed exhibition pages
    link_patterns: List[str] = []

    # SSL verification flag; set to False for sites with certificate hostname mismatches
    verify_ssl: bool = True

    # SPA flag; set to True for React/Vue/Next.js sites that require browser rendering
    use_playwright: bool = False

    # Use curl_cffi to impersonate browser TLS/JA3 fingerprint; set to True for Cloudflare-protected sites
    use_curl_cffi: bool = False

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        """Returns all listing URLs to crawl (current + historical).
        
        Subclasses can override this to generate year-based paginated URLs.
        The `since_year` filter applies when supported by the subclass.
        """
        urls = []
        if self.list_url:
            urls.append(self.list_url)
        urls.extend(self.extra_list_urls)
        return urls

    def get_exhibition_urls(self, client: httpx.Client, since_year: Optional[int] = None) -> List[str]:
        """Fetches all listing pages and extracts detail page URLs.

        Args:
            client: The HTTP client to use.
            since_year: If provided, only return URLs from listing pages for that year and later.
        """
        if self.use_playwright:
            return self._get_exhibition_urls_playwright(since_year=since_year)

        list_urls = self.get_list_urls(since_year=since_year)
        if not list_urls:
            logger.error(f"No list URLs configured for parser {self.source}")
            return []

        all_found: Set[str] = set()

        for list_url in list_urls:
            try:
                logger.info(f"[{self.source}] Fetching listing page: {list_url}")
                # Use curl_cffi for Cloudflare bypass, temporary httpx for SSL issues, or the shared client
                if self.use_curl_cffi:
                    from curl_cffi import requests as curl_requests

                    response = curl_requests.get(
                        list_url, headers=HEADERS, impersonate="chrome124", timeout=30
                    )
                    response.raise_for_status()
                    page_html = response.text
                elif not self.verify_ssl:
                    logger.warning(f"[{self.source}] SSL verification disabled for {list_url}")
                    with httpx.Client(verify=False, follow_redirects=True, max_redirects=5) as temp_client:
                        response = temp_client.get(list_url, headers=HEADERS)
                        response.raise_for_status()
                        page_html = response.text
                else:
                    response = client.get(list_url, headers=HEADERS, follow_redirects=True)
                    response.raise_for_status()
                    page_html = response.text

                soup = BeautifulSoup(page_html, "html.parser")

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    full_url = urljoin(list_url, href)

                    # Exclude exact list URL itself
                    if full_url.rstrip("/") in [u.rstrip("/") for u in list_urls]:
                        continue

                    # Check against link patterns
                    for pattern in self.link_patterns:
                        if re.search(pattern, full_url) or re.search(pattern, href):
                            all_found.add(full_url)
                            break

            except Exception as e:
                logger.error(f"[{self.source}] Error fetching listing page {list_url}: {e}", exc_info=True)
                continue

        urls = sorted(list(all_found))
        logger.info(f"[{self.source}] Total discovered: {len(urls)} exhibition URLs across {len(list_urls)} listing page(s).")
        return urls

    def _get_exhibition_urls_playwright(self, since_year: Optional[int] = None) -> List[str]:
        """SPA fallback: use Playwright to render the listing page and extract links."""
        if not HAS_PLAYWRIGHT:
            logger.error(
                f"[{self.source}] Playwright is required but not installed. "
                "Install it with: uv pip install playwright && python -m playwright install chromium"
            )
            return []

        list_urls = self.get_list_urls(since_year=since_year)
        if not list_urls:
            logger.error(f"No list URLs configured for parser {self.source}")
            return []

        all_found: Set[str] = set()

        for list_url in list_urls:
            try:
                logger.info(f"[{self.source}] Rendering listing page with Playwright: {list_url}")
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(10000)
                    html = page.content()
                    browser.close()
            except Exception as e:
                logger.error(f"[{self.source}] Playwright failed to load listing page {list_url}: {e}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                full_url = urljoin(list_url, href)

                if full_url.rstrip("/") in [u.rstrip("/") for u in list_urls]:
                    continue

                for pattern in self.link_patterns:
                    if re.search(pattern, full_url) or re.search(pattern, href):
                        all_found.add(full_url)
                        break

        urls = sorted(list(all_found))
        logger.info(f"[{self.source}] Total discovered (Playwright): {len(urls)} exhibition URLs.")
        return urls
            
    def clean_html(self, html: str) -> str:
        """Strips noise from the detailed exhibition HTML, returning clean high-density text."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove common noise tags
        for element in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript", "svg", "form"]):
            element.decompose()
            
        # Remove common noise classes/IDs
        for selector in [".nav", ".footer", ".header", ".menu", ".sidebar", "#menu", "#footer", "#header", ".cookie", ".breadcrumb"]:
            for element in soup.select(selector):
                element.decompose()
                
        # Get readable text
        text = soup.get_text(separator="\n")
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        return text
