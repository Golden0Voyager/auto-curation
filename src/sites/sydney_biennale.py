from src.sites.base import BaseSiteParser

class SydneyBiennaleParser(BaseSiteParser):
    """Sydney Biennale.

    悉尼双年展，澳大利亚历史最悠久、规模最大的当代视觉艺术节。
    """
    source = "Sydney Biennale"
    city = "Sydney"
    parser_key = "sydney_biennale"
    institution_type = "biennial"
    list_url = "https://www.biennaleofsydney.art"
    link_patterns = [
        r"biennaleofsydney\.art/[^/]+",
    ]
