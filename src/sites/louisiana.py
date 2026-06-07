from src.sites.base import BaseSiteParser


class LouisianaParser(BaseSiteParser):
    """Louisiana Museum of Modern Art.

    路易斯安那现代艺术博物馆，丹麦最著名的当代艺术博物馆。
    """

    source = "Louisiana Museum"
    city = "Humlebæk"
    parser_key = "louisiana"
    institution_type = "museum"
    list_url = "https://louisiana.dk/en/exhibitions/current/"
    extra_list_urls = [
        "https://louisiana.dk/en/exhibitions/past/",
        "https://louisiana.dk/en/exhibitions/upcoming/",
    ]
    link_patterns = [
        r"louisiana\.dk/en/exhibition/[^/]+",
    ]
