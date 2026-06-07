from src.sites.base import BaseSiteParser


class MetParser(BaseSiteParser):
    source = "The Met"
    city = "New York"
    list_url = "https://www.metmuseum.org/exhibitions"
    link_patterns = [r"/exhibitions/[^/]+$"]
