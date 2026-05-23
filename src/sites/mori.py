from typing import List, Optional
from datetime import date
from src.sites.base import BaseSiteParser

class MoriParser(BaseSiteParser):
    """Mori Art Museum - Tokyo.
    
    Historical exhibitions are available via the /exhibitions/past/ section.
    """
    source = "Mori Art Museum"
    city = "Tokyo"
    list_url = "https://www.mori.art.museum/en/exhibitions/"
    extra_list_urls = [
        "https://www.mori.art.museum/en/exhibitions/past/",
        "https://www.mori.art.museum/en/exhibitions/past/?page=2",
        "https://www.mori.art.museum/en/exhibitions/past/?page=3",
        "https://www.mori.art.museum/en/exhibitions/past/?page=4",
        "https://www.mori.art.museum/en/exhibitions/past/?page=5",
    ]
    link_patterns = [r"mori\.art\.museum/en/exhibitions/[a-zA-Z0-9_-]+"]
