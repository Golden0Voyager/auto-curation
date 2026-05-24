from src.sites.base import BaseSiteParser

class LyonBiennaleParser(BaseSiteParser):
    """Lyon Biennale.

    法国里昂双年展，欧洲重要的当代艺术双年展。
    """
    source = "Lyon Biennale"
    city = "Lyon"
    parser_key = "lyon_biennale"
    institution_type = "biennial"
    list_url = "https://www.biennalede-lyon.com"
    link_patterns = [
        r"biennalede-lyon\.com/[^/]+",
    ]
