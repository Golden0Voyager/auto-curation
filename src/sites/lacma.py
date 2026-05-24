from src.sites.base import BaseSiteParser

class LACMAParser(BaseSiteParser):
    """Los Angeles County Museum of Art.

    洛杉矶郡艺术博物馆，美国西部最大的艺术博物馆。
    注意：受 Cloudflare 403 保护，需要 Playwright 或 stealth headers。
    """
    source = "LACMA"
    city = "Los Angeles"
    parser_key = "lacma"
    institution_type = "museum"
    list_url = "https://www.lacma.org/exhibitions"
    link_patterns = [
        r"lacma\.org/exhibitions/[^/]+",
    ]
