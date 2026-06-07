from src.sites.base import BaseSiteParser


class LiverpoolBiennialParser(BaseSiteParser):
    """Liverpool Biennial.

    英国利物浦双年展，英国最大的当代视觉艺术节。
    """

    source = "Liverpool Biennial"
    city = "Liverpool"
    parser_key = "liverpool_biennial"
    institution_type = "biennial"
    list_url = "https://www.biennial.com"
    link_patterns = [
        r"biennial\.com/[^/]+",
    ]
