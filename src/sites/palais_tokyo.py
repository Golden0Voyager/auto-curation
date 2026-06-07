from src.sites.base import BaseSiteParser


class PalaisTokyoParser(BaseSiteParser):
    source = "Palais de Tokyo"
    city = "Paris"
    list_url = "https://palaisdetokyo.com/agenda-palais-de-tokyo/"
    # Palais de Tokyo exhibition pages are under /exposition/
    link_patterns = [r"/exposition/[a-zA-Z0-9_-]+"]
