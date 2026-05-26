from src.sites.base import BaseSiteParser

class PompidouParser(BaseSiteParser):
    source = "Centre Pompidou"
    city = "Paris"
    list_url = "https://www.centrepompidou.fr/en/program/calendar"
    link_patterns = [
        r"/en/program/calendar/event/[a-zA-Z0-9]+",
    ]
