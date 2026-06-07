from datetime import date

from src.sites.base import BaseSiteParser


class MoriParser(BaseSiteParser):
    """Mori Art Museum - Tokyo.

    Historical exhibitions are available via the /exhibitions/past/ section.
    """

    source = "Mori Art Museum"
    city = "Tokyo"
    list_url = "https://www.mori.art.museum/en/exhibitions/"
    link_patterns = [r"mori\.art\.museum/en/exhibitions/[a-zA-Z0-9_-]+"]

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        """Generate current + past pagination URLs dynamically.

        Mori Art Museum has pagination past exhibitions under /exhibitions/past/?page=N.
        """
        urls = [self.list_url, "https://www.mori.art.museum/en/exhibitions/past/"]

        # Max pages to cover full history since 2003
        max_pages = 20
        if since_year:
            current_year = date.today().year
            years_back = max(1, current_year - since_year)
            # Roughly 5 exhibitions per year, ~8-10 per page
            max_pages = min(years_back + 1, 20)

        for page_num in range(2, max_pages + 1):
            urls.append(f"https://www.mori.art.museum/en/exhibitions/past/?page={page_num}")

        return urls
