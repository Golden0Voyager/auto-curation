from src.sites.base import BaseSiteParser


class BalticParser(BaseSiteParser):
    """BALTIC Centre for Contemporary Art - Gateshead.

    波罗的海当代艺术中心，英国纽卡斯尔的重要当代艺术机构。
    """

    source = "BALTIC"
    city = "Gateshead"
    parser_key = "baltic"
    institution_type = "museum"
    list_url = "https://www.baltic.art/"
    link_patterns = [
        r"baltic\.art/whats-on/[^/]+",
    ]
