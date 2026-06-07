from src.sites.base import BaseSiteParser


class MAIIAMParser(BaseSiteParser):
    """MAIIAM Contemporary Art Museum - Chiang Mai.

    MAIIAM 当代艺术博物馆，泰国清迈的重要私人当代艺术馆。
    """

    source = "MAIIAM"
    city = "Chiang Mai"
    parser_key = "maiiam"
    institution_type = "museum"
    list_url = "https://maiiam.com/en/exhibition"
    link_patterns = [
        r"maiiam\.com/en/exhibition/[^/]+",
    ]
