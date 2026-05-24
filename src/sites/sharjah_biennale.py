from src.sites.base import BaseSiteParser

class SharjahBiennaleParser(BaseSiteParser):
    """Sharjah Biennial.

    沙迦双年展，中东和北非地区最具影响力的当代艺术双年展。
    """
    source = "Sharjah Biennial"
    city = "Sharjah"
    parser_key = "sharjah_biennale"
    institution_type = "biennial"
    list_url = "https://sharjahart.org/sharjah-biennial"
    link_patterns = [
        r"sharjahart\.org/sharjah-biennial/[^/]+",
    ]
