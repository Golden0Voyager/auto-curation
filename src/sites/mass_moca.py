from src.sites.base import BaseSiteParser

class MASSMocaParser(BaseSiteParser):
    """MASS MoCA.

    马萨诸塞州当代艺术博物馆，以大型装置和特定场域作品闻名。
    注意：受 Cloudflare 403 保护，需要 Playwright 或 stealth headers。
    """
    source = "MASS MoCA"
    city = "North Adams"
    parser_key = "mass_moca"
    institution_type = "museum"
    status = "BLOCKED_CLOUDFLARE"
    list_url = "https://massmoca.org/exhibitions/"
    link_patterns = [
        r"massmoca\.org/event/[^/]+",
        r"massmoca\.org/exhibitions/[^/]+",
    ]
    use_curl_cffi = True
