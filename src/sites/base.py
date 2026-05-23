import logging
import re
from typing import List, Set, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger("auto_curation.sites.base")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

class BaseSiteParser:
    """Base class for all art institution site crawlers.
    
    Supports multi-page and historical archive crawling via the `list_urls` property.
    Subclasses can override `list_urls` to return a dynamic list of pages (e.g., by year).
    """
    
    source: str = "Generic"
    city: str = "Generic"
    list_url: str = ""
    
    # Additional archive/historical listing URLs (e.g., past exhibitions pages)
    extra_list_urls: List[str] = []
    
    # URL patterns or prefixes to match for detailed exhibition pages
    link_patterns: List[str] = []

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
        list_urls = self.get_list_urls(since_year=since_year)
        if not list_urls:
            logger.error(f"No list URLs configured for parser {self.source}")
            return []
            
        all_found: Set[str] = set()

        for list_url in list_urls:
            try:
                logger.info(f"[{self.source}] Fetching listing page: {list_url}")
                response = client.get(list_url, headers=HEADERS, follow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
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
