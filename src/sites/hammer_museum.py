from src.sites.base import BaseSiteParser


class HammerMuseumParser(BaseSiteParser):
    """Hammer Museum - UCLA.

    UCLA 哈默博物馆，以当代艺术展览和公共项目著称。
    """

    source = "Hammer Museum"
    city = "Los Angeles"
    parser_key = "hammer_museum"
    institution_type = "museum"
    list_url = "https://hammer.ucla.edu/exhibitions"
    link_patterns = [
        r"hammer\.ucla\.edu/exhibitions/[^/]+",
    ]
