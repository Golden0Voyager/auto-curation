from src.sites.base import BaseSiteParser

class NewMuseumParser(BaseSiteParser):
    """New Museum - New York.

    纽约新当代艺术博物馆，专注展示国际当代艺术新作。
    注意：网站基于 Next.js SPA，静态 HTML 几乎无内容，需要 Playwright 渲染。
    """
    source = "New Museum"
    city = "New York"
    parser_key = "new_museum"
    institution_type = "museum"
    status = "BLOCKED_SPA"
    list_url = "https://www.newmuseum.org/exhibitions"
    use_playwright = True
    link_patterns = [
        r"newmuseum\.org/exhibition/[^/]+",
    ]
