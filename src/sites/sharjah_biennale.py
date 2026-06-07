from src.sites.base import BaseSiteParser


class SharjahBiennaleParser(BaseSiteParser):
    """Sharjah Biennial.

    沙迦双年展，中东和北非地区最具影响力的当代艺术双年展。
    官网列表页为纯导航菜单，无直接展览链接，需按届数构造 URL。
    """

    source = "Sharjah Biennial"
    city = "Sharjah"
    parser_key = "sharjah_biennale"
    institution_type = "biennial"
    list_url = "https://www.sharjahart.org/en/sharjah-biennial/"
    link_patterns = [
        r"sharjahart\.org/en/sharjah-biennial/sb-\d+",
    ]

    def get_exhibition_urls(self, client, since_year: int | None = None) -> list[str]:
        """Construct exhibition URLs directly (sb-1 to sb-17).

        The Sharjah Biennial website does not list exhibition detail links
        on its listing page; each edition follows a predictable URL pattern.
        """
        urls = []
        for i in range(1, 18):
            url = f"https://www.sharjahart.org/en/sharjah-biennial/sb-{i}/"
            urls.append(url)
        return urls
