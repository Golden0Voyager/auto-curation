import logging
import re

from src.sites.base import BaseSiteParser

logger = logging.getLogger("auto_curation.sites.mca_australia")

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False


class MCAAustraliaParser(BaseSiteParser):
    """Museum of Contemporary Art Australia - Sydney.

    澳大利亚当代艺术博物馆，悉尼环形码头的标志性艺术机构。
    注意：网站为 SPA，静态 HTML 无展览链接，需要 Playwright 渲染。
    入口页有 "Continue" 按钮，必须先点击才能看到展览列表。
    """

    source = "MCA Australia"
    city = "Sydney"
    parser_key = "mca_australia"
    institution_type = "museum"
    list_url = "https://www.mca.com.au/exhibitions/"
    use_playwright = True
    link_patterns = [
        r"mca\.com\.au/exhibitions/[^/]+",
    ]

    def get_exhibition_urls(self, client, since_year: int | None = None) -> list[str]:
        """Custom Playwright flow: click Continue button then extract links."""
        if not HAS_PLAYWRIGHT:
            logger.error(
                "[MCA Australia] Playwright is required but not installed. "
                "Install it with: uv pip install playwright && python -m playwright install chromium"
            )
            return []

        all_found: set[str] = set()
        list_urls = self.get_list_urls(since_year=since_year)

        for list_url in list_urls:
            try:
                logger.info(f"[MCA Australia] Rendering listing page with Playwright: {list_url}")
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(list_url, wait_until="networkidle", timeout=90000)
                    page.wait_for_timeout(3000)

                    # Click the Continue button on the landing/splash page
                    try:
                        page.get_by_text("Continue", exact=False).first.click()
                        logger.info("[MCA Australia] Clicked Continue button.")
                        page.wait_for_timeout(5000)
                    except Exception:
                        logger.info(
                            "[MCA Australia] No Continue button found (may already be on content page)."
                        )

                    links = page.evaluate(
                        """() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"""
                    )
                    browser.close()

                for link in links:
                    for pattern in self.link_patterns:
                        if re.search(pattern, link):
                            all_found.add(link)
                            break

            except Exception as e:
                logger.error(
                    f"[MCA Australia] Playwright failed to load listing page {list_url}: {e}"
                )
                continue

        urls = sorted(list(all_found))
        logger.info(f"[MCA Australia] Total discovered (Playwright): {len(urls)} exhibition URLs.")
        return urls
