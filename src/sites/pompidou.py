from src.sites.base import BaseSiteParser

class PompidouParser(BaseSiteParser):
    source = "Centre Pompidou"
    city = "Paris"
    list_url = "https://www.centrepompidou.fr/en/program/exhibitions"
    link_patterns = [
        r"/en/program/exhibitions/[a-zA-Z0-9_-]+",
        r"/en/expositions/[a-zA-Z0-9_-]+"
    ]
