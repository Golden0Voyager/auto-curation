from src.sites.base import BaseSiteParser

class HamburgerBahnhofParser(BaseSiteParser):
    """Hamburger Bahnhof - Berlin.

    汉堡火车站现代艺术博物馆，柏林最重要的当代艺术馆之一。
    注意：SSL 证书 hostname 不匹配，需要 verify=False 或改走 http。
    """
    source = "Hamburger Bahnhof"
    city = "Berlin"
    parser_key = "hamburger_bahnhof"
    institution_type = "museum"
    list_url = "https://www.hamburgerbahnhof.de/en/exhibitions"
    link_patterns = [
        r"hamburgerbahnhof\.de/en/exhibitions/[^/]+",
    ]
