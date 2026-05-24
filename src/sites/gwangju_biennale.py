from src.sites.base import BaseSiteParser

class GwangjuBiennaleParser(BaseSiteParser):
    """Gwangju Biennale.

    韩国光州双年展，亚洲最重要的双年展之一。
    """
    source = "Gwangju Biennale"
    city = "Gwangju"
    parser_key = "gwangju_biennale"
    institution_type = "biennial"
    list_url = "https://gb.or.kr/en"
    link_patterns = [
        r"gb\.or\.kr/en/[^/]+",
    ]
