from src.sites.base import BaseSiteParser

class PalaisTokyoParser(BaseSiteParser):
    source = "Palais de Tokyo"
    city = "Paris"
    list_url = "https://palaisdetokyo.com/en/exhibitions/"
    # Palais de Tokyo uses /en/exposition/ or /en/exhibitions/ (excluding page links)
    link_patterns = [r"/en/exposition/[a-zA-Z0-9_-]+", r"/en/exhibitions/[a-zA-Z0-9_-]+"]
