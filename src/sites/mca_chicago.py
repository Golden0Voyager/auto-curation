from src.sites.base import BaseSiteParser

class MCAChicagoParser(BaseSiteParser):
    """Museum of Contemporary Art Chicago.

    芝加哥当代艺术博物馆，美国最重要的当代艺术机构之一。
    """
    source = "MCA Chicago"
    city = "Chicago"
    parser_key = "mca_chicago"
    institution_type = "museum"
    list_url = "https://mcachicago.org/exhibitions"
    link_patterns = [
        # Exclude archive listing page; only match individual exhibition slugs
        r"mcachicago\.org/exhibitions/(?!archive(?:/|$))[^/\s?]+",
    ]
