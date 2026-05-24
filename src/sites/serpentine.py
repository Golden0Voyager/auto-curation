import logging
import re
from typing import List, Optional, Set
from datetime import date
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.sites.base import BaseSiteParser, HEADERS

logger = logging.getLogger("auto_curation.sites.serpentine")

class SerpentineParser(BaseSiteParser):
    """Serpentine Galleries - London.
    
    The archive section is paginated (/whats-on/archive/page/N/).
    We generate archive page URLs up to a defined limit and extract
    real exhibition links from each page.
    """
    source = "Serpentine Galleries"
    city = "London"
    list_url = "https://www.serpentinegalleries.org/whats-on/"
    
    # Max archive pages to crawl per run (each page ~10 exhibitions)
    # Default 150 pages to cover full history; use --since to limit
    MAX_ARCHIVE_PAGES = 150
    
    link_patterns = [r"serpentinegalleries\.org/whats-on/[a-zA-Z0-9][a-zA-Z0-9_-]+/?$"]

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        """Generate current + archive pagination URLs.
        
        If since_year is provided and is recent, reduce the number of archive pages.
        Each archive page covers roughly one year, so we limit pages accordingly.
        """
        urls = [self.list_url]
        
        current_year = date.today().year
        if since_year:
            years_back = max(1, current_year - since_year)
            # Roughly 10 exhibitions/page, ~15 per year for Serpentine
            max_pages = min(years_back * 2, self.MAX_ARCHIVE_PAGES)
        else:
            max_pages = self.MAX_ARCHIVE_PAGES
        
        # Add archive pagination
        urls.append("https://www.serpentinegalleries.org/whats-on/archive/")
        for page_num in range(2, max_pages + 1):
            urls.append(f"https://www.serpentinegalleries.org/whats-on/archive/page/{page_num}/")
        
        logger.info(f"[Serpentine] Will crawl {len(urls)} pages (including {max_pages} archive pages).")
        return urls

    def get_exhibition_urls(self, client: httpx.Client, since_year: Optional[int] = None) -> List[str]:
        """Fetch all pages and extract real exhibition detail URLs.
        
        Filters out pagination links (archive/page/N/) and category filter URLs.
        """
        list_urls = self.get_list_urls(since_year=since_year)
        all_found: Set[str] = set()

        for list_url in list_urls:
            try:
                response = client.get(list_url, headers=HEADERS, follow_redirects=True)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    full_url = urljoin(list_url, href)
                    
                    # Must match exhibition pattern
                    if not re.search(r"serpentinegalleries\.org/whats-on/[a-zA-Z0-9][a-zA-Z0-9_-]+", full_url):
                        continue
                    
                    # Exclude: archive/, archive/page/N/, ?type=... filter URLs
                    path = full_url.replace("https://www.serpentinegalleries.org", "")
                    if re.search(r"^/whats-on/archive(/page/\d+)?/?$", path):
                        continue
                    if "?" in full_url:
                        continue
                    if re.search(r"/whats-on/$", full_url):
                        continue
                    
                    all_found.add(full_url.rstrip("/") + "/")
                    
            except Exception as e:
                logger.error(f"[Serpentine] Error fetching {list_url}: {e}")
                continue

        urls = sorted(list(all_found))
        logger.info(f"[Serpentine] Discovered {len(urls)} real exhibition URLs.")
        return urls
