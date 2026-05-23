from typing import List, Optional
from datetime import date
from src.sites.base import BaseSiteParser

class TateParser(BaseSiteParser):
    """Tate Modern - London.
    
    Supports historical exhibitions by generating year-based listing URLs.
    The Tate website supports filtering by year via the `date_from` and `date_to` query params.
    """
    source = "Tate Modern"
    city = "London"
    list_url = "https://www.tate.org.uk/whats-on?date_range=from_now&gallery_group=tate-modern&event_type=exhibition"
    
    # Current exhibitions - link patterns matching tate-modern exhibition paths
    link_patterns = [r"tate\.org\.uk/whats-on/tate-modern/[a-zA-Z0-9_-]+$"]
    
    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        """Generate year-based past exhibition listing URLs for Tate Modern.
        
        If since_year is provided, generates URLs from since_year to present.
        Otherwise uses only the current listing page.
        """
        urls = [self.list_url]
        
        current_year = date.today().year
        start_year = since_year if since_year else current_year
        
        # Tate's past exhibitions can be filtered by year using date_from/date_to
        for year in range(start_year, current_year + 1):
            past_url = (
                f"https://www.tate.org.uk/whats-on"
                f"?date_from={year}-01-01"
                f"&date_to={year}-12-31"
                f"&gallery_group=tate-modern"
                f"&event_type=exhibition"
                f"&date_range=custom"
            )
            if past_url not in urls:
                urls.append(past_url)
        
        return urls
