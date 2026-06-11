import logging
import re

from src.sites.base import BaseSiteParser

logger = logging.getLogger("auto_curation.sites.guggenheim")

try:
    from scrapling import StealthyFetcher

    HAS_SCRAPLING = True
except Exception:
    HAS_SCRAPLING = False


class GuggenheimParser(BaseSiteParser):
    """Guggenheim Museum - New York.

    古根海姆美术馆，纽约标志性螺旋建筑内的现当代艺术馆。
    注意：网站受 Cloudflare 保护，原生 Playwright 会 403，
    必须使用 Scrapling StealthyFetcher 绕过。
    """

    source = "Guggenheim Museum"
    city = "New York"
    parser_key = "guggenheim"
    institution_type = "museum"
    status = "BLOCKED_CLOUDFLARE"
    list_url = "https://www.guggenheim.org/exhibitions"
    link_patterns = [
        r"/exhibition/[a-zA-Z0-9_-]+",
    ]

    def get_exhibition_urls(self, client, since_year: int | None = None) -> list[str]:
        """Use Scrapling StealthyFetcher to bypass Cloudflare and discover URLs."""
        if not HAS_SCRAPLING:
            logger.error(
                "[Guggenheim] Scrapling is required but not installed. "
                "Install it with: uv pip install scrapling"
            )
            return []

        urls: set[str] = set()
        try:
            logger.info("[Guggenheim] Fetching with Scrapling StealthyFetcher...")
            fetcher = StealthyFetcher()
            page = fetcher.fetch(self.list_url, timeout=60000)
            html = page.html_content

            for href in re.findall(r'href="(/exhibition/[^"]+)"', html):
                if href in (
                    "/exhibitions",
                    "/exhibitions#past",
                    "/exhibitions#upcoming",
                    "#past-exhibitions",
                    "#exhibitions-on-view",
                    "/exhibition/exhibitions",
                ):
                    continue
                urls.add(f"https://www.guggenheim.org{href}")

        except Exception as e:
            logger.error(f"[Guggenheim] Scrapling failed: {e}")
            return []

        logger.info(f"[Guggenheim] Discovered {len(urls)} exhibition URLs.")
        return sorted(urls)
