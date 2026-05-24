from src.sites.base import BaseSiteParser

class YokohamaTriennaleParser(BaseSiteParser):
    """Yokohama Triennale.

    横滨三年展，日本最具影响力的国际当代艺术展之一。
    """
    source = "Yokohama Triennale"
    city = "Yokohama"
    parser_key = "yokohama_triennale"
    institution_type = "triennial"
    list_url = "https://yokohamatriennale.jp/english"
    link_patterns = [
        r"yokohamatriennale\.jp/english/[^/]+",
    ]
