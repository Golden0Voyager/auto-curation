from src.sites.base import BaseSiteParser

class WhitneyBiennialParser(BaseSiteParser):
    """Whitney Biennial.

    惠特尼双年展，美国当代艺术最具影响力的周期性展览。
    """
    source = "Whitney Biennial"
    city = "New York"
    parser_key = "whitney_biennial"
    institution_type = "biennial"
    list_url = "https://whitney.org/exhibitions"
    link_patterns = [
        r"whitney\.org/exhibitions/[^/]+",
    ]
