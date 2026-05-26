from src.sites.base import BaseSiteParser

class FLVParser(BaseSiteParser):
    """Fondation Louis Vuitton - Paris.

    路易威登基金会，巴黎布洛涅森林中的当代艺术地标。
    注意：网站为 SPA，静态 HTML 无展览链接，需要 Playwright 渲染。
    """
    source = "Fondation Louis Vuitton"
    city = "Paris"
    parser_key = "flv"
    institution_type = "museum"
    status = "BLOCKED_SPA"
    list_url = "https://www.fondationlouisvuitton.fr/en.html"
    link_patterns = [
        r"fondationlouisvuitton\.fr/en/exhibitions/[^/]+",
    ]
