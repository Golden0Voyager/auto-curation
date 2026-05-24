from src.sites.base import BaseSiteParser

class PinakothekParser(BaseSiteParser):
    """Pinakothek der Moderne - Munich.

    慕尼黑现代绘画陈列馆，德国最重要的现代艺术博物馆之一。
    """
    source = "Pinakothek der Moderne"
    city = "Munich"
    parser_key = "pinakothek"
    institution_type = "museum"
    list_url = "https://www.pinakothek.de/en/exhibitions"
    link_patterns = [
        r"pinakothek\.de/en/exhibition/[^/]+",
    ]
