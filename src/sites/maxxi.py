from src.sites.base import BaseSiteParser

class MAXXIParser(BaseSiteParser):
    """MAXXI - National Museum of 21st Century Arts, Rome.

    罗马国立二十一世纪艺术博物馆，意大利最重要的当代艺术机构。
    """
    source = "MAXXI"
    city = "Rome"
    parser_key = "maxxi"
    institution_type = "museum"
    list_url = "https://www.maxxi.art/en/events/categories/mostre/"
    link_patterns = [
        r"maxxi\.art/en/events/[^/]+",
    ]
