from src.sites.base import BaseSiteParser

class BerlinBiennaleParser(BaseSiteParser):
    """Berlin Biennale.

    柏林双年展，由 KW Institute for Contemporary Art 主办。
    """
    source = "Berlin Biennale"
    city = "Berlin"
    parser_key = "berlin_biennale"
    institution_type = "biennial"
    list_url = "https://berlinbiennale.de"
    link_patterns = [
        r"berlinbiennale\.de/[^/]+",
    ]
