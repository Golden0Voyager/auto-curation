from src.sites.base import BaseSiteParser


class DocumentaParser(BaseSiteParser):
    """Documenta - Kassel.

    德国卡塞尔文献展，当代艺术的顶级风向标，五年一届。
    """

    source = "Documenta"
    city = "Kassel"
    parser_key = "documenta"
    institution_type = "quintennial"
    list_url = "https://documenta.de/en"
    link_patterns = [
        r"documenta\.de/en/(retrospective|programme)/[^/]+",
    ]
