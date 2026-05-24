from src.sites.base import BaseSiteParser

class IstanbulBiennaleParser(BaseSiteParser):
    """Istanbul Biennial.

    伊斯坦布尔双年展，连接欧亚艺术场景的重要平台。
    """
    source = "Istanbul Biennial"
    city = "Istanbul"
    parser_key = "istanbul_biennale"
    institution_type = "biennial"
    list_url = "https://bienal.iksv.org/en"
    link_patterns = [
        r"bienal\.iksv\.org/en/[^/]+",
    ]
