from src.sites.base import BaseSiteParser

class BarbicanParser(BaseSiteParser):
    """Barbican Centre - London.

    巴比肯艺术中心，欧洲最大的多学科艺术中心之一。
    """
    source = "Barbican Centre"
    city = "London"
    parser_key = "barbican"
    institution_type = "museum"
    list_url = "https://www.barbican.org.uk/whats-on"
    link_patterns = [
        r"barbican\.org\.uk/whats-on/[^/]+",
    ]
