from src.sites.base import BaseSiteParser


class BrooklynMuseumParser(BaseSiteParser):
    """Brooklyn Museum.

    布鲁克林博物馆，纽约市藏品最丰富的博物馆之一。
    """

    source = "Brooklyn Museum"
    city = "New York"
    parser_key = "brooklyn_museum"
    institution_type = "museum"
    list_url = "https://www.brooklynmuseum.org/exhibitions"
    link_patterns = [
        r"brooklynmuseum\.org/exhibitions/[^/]+",
    ]
