import logging
import re

from src.sites.base import BaseSiteParser

logger = logging.getLogger("auto_curation.sites.flv")

try:
    from scrapling import StealthyFetcher

    HAS_SCRAPLING = True
except Exception:
    HAS_SCRAPLING = False


class FLVParser(BaseSiteParser):
    """Fondation Louis Vuitton - Paris.

    路易威登基金会，巴黎布洛涅森林中的当代艺术地标。
    注意：网站为 SPA 且受 Akamai CDN 保护，原生 Playwright 会 Access Denied，
    必须使用 Scrapling StealthyFetcher 绕过。
    """

    source = "Fondation Louis Vuitton"
    city = "Paris"
    parser_key = "flv"
    institution_type = "museum"
    status = "BLOCKED_SPA"
    list_url = "https://www.fondationlouisvuitton.fr/en/fondation/the-exhibitions"
    link_patterns = [
        r"fondationlouisvuitton\.fr/en/events/[^/]+",
    ]

    def get_exhibition_urls(self, client, since_year: int | None = None) -> list[str]:
        """Use Scrapling StealthyFetcher to bypass Akamai and discover URLs."""
        if not HAS_SCRAPLING:
            logger.error(
                "[FLV] Scrapling is required but not installed. "
                "Install it with: uv pip install scrapling"
            )
            return []

        urls: set[str] = set()
        try:
            logger.info("[FLV] Fetching with Scrapling StealthyFetcher...")
            fetcher = StealthyFetcher()
            page = fetcher.fetch(self.list_url, timeout=60000)
            html = page.html_content

            for href in re.findall(r'href="([^"]*/en/events/[^"]+)"', html):
                if href.startswith("/"):
                    href = f"https://www.fondationlouisvuitton.fr{href}"
                urls.add(href)

        except Exception as e:
            logger.error(f"[FLV] Scrapling failed: {e}")
            return []

        logger.info(f"[FLV] Discovered {len(urls)} exhibition URLs.")
        return sorted(urls)
