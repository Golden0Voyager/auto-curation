from typing import List, Optional
from src.sites.base import BaseSiteParser

class MPlusParser(BaseSiteParser):
    """M+ Museum - Hong Kong.
    
    Supports both current and historical exhibitions via the ?status=past endpoint.
    All past exhibitions are listed on a single page, no year-based pagination needed.
    """
    source = "M+ Museum"
    city = "Hong Kong"
    list_url = "https://www.mplus.org.hk/en/exhibitions/"
    
    # Historical exhibitions accessible via status=past query param
    extra_list_urls = [
        "https://www.mplus.org.hk/en/exhibitions/?status=past",
    ]
    
    link_patterns = [r"mplus\.org\.hk/en/exhibitions/[a-zA-Z0-9_-]+"]
