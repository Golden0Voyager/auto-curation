from src.sites.base import BaseSiteParser

class BiennaleParser(BaseSiteParser):
    source = "Venice Biennale"
    city = "Venice"
    list_url = "https://www.labiennale.org/en/art/2026"
    link_patterns = [
        r"/en/art/2026/[a-zA-Z0-9_-]+",
        r"/en/art/2024/[a-zA-Z0-9_-]+",
        r"/en/art/news/"
    ]
