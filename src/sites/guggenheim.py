from src.sites.base import BaseSiteParser

class GuggenheimParser(BaseSiteParser):
    source = "Guggenheim Museum"
    city = "New York"
    list_url = "https://www.guggenheim.org/exhibitions"
    link_patterns = [r"/exhibition/[a-zA-Z0-9_-]+"]
