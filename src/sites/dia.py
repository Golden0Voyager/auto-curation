from src.sites.base import BaseSiteParser

class DiaParser(BaseSiteParser):
    """Dia Art Foundation.

    Dia 艺术基金会，以大地艺术和极简主义长期装置闻名。
    注意：受 Cloudflare 403 保护，需要 Playwright 或 stealth headers。
    """
    source = "Dia Art Foundation"
    city = "New York"
    parser_key = "dia"
    institution_type = "museum"
    list_url = "https://www.diaart.org/exhibition"
    link_patterns = [
        r"diaart\.org/exhibition/[^/]+",
    ]
