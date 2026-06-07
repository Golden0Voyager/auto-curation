from src.sites.base import BaseSiteParser


class LenbachhausParser(BaseSiteParser):
    """Lenbachhaus - Munich.

    伦巴赫之家，慕尼黑著名的市立美术馆，以青骑士派收藏闻名。
    """

    source = "Lenbachhaus"
    city = "Munich"
    parser_key = "lenbachhaus"
    institution_type = "museum"
    list_url = "https://www.lenbachhaus.de/en/program/exhibitions"
    link_patterns = [
        r"lenbachhaus\.de/en/program/exhibitions/details/[^/]+",
    ]
