from src.sites.base import BaseSiteParser


class KunsthalParser(BaseSiteParser):
    """Kunsthal Rotterdam.

    鹿特丹 Kunsthal，以多元化、高频率的当代艺术展览著称。
    """

    source = "Kunsthal Rotterdam"
    city = "Rotterdam"
    parser_key = "kunsthal"
    institution_type = "museum"
    list_url = "https://www.kunsthal.nl/en/plan-your-visit/exhibitions/"
    link_patterns = [
        r"kunsthal\.nl/en/plan-your-visit/exhibitions/[^/]+",
    ]
