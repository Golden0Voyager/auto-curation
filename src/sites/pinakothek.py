from src.sites.base import BaseSiteParser


class PinakothekParser(BaseSiteParser):
    """Pinakothek der Moderne - Munich.

    慕尼黑现代绘画陈列馆，德国最重要的现代艺术博物馆之一。
    注意：网站为 SPA，静态 HTML 几乎无展览链接，需要 Playwright 渲染。
    """

    source = "Pinakothek der Moderne"
    city = "Munich"
    parser_key = "pinakothek"
    institution_type = "museum"
    list_url = "https://www.pinakothek.de/en/exhibitions"
    extra_list_urls = ["https://www.pinakothek.de/en/exhibitions/archive"]
    use_playwright = True
    # NOTE: The archive page is a heavy SPA; only ~3 current exhibitions are
    # discoverable without interaction. Do not retry archive scraping.
    link_patterns = [
        r"pinakothek\.de/en/(?:exhibition|ausstellung)/[^/]+",
    ]
