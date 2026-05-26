from src.sites.base import BaseSiteParser

class HamburgerBahnhofParser(BaseSiteParser):
    """Hamburger Bahnhof - Berlin.

    汉堡火车站现代艺术博物馆，柏林最重要的当代艺术馆之一。
    注意：原域名 hamburgerbahnhof.de SSL 证书 hostname 不匹配，
    展览信息实际托管在 smb.museum 主站下。
    """
    source = "Hamburger Bahnhof"
    city = "Berlin"
    parser_key = "hamburger_bahnhof"
    institution_type = "museum"
    list_url = "https://www.smb.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/"
    extra_list_urls = [
        "https://www.smb.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/archive/",
    ]
    link_patterns = [
        r"smb\.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/detail/[^/]+",
    ]
