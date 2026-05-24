from src.sites.base import BaseSiteParser

class KWInstituteParser(BaseSiteParser):
    """KW Institute for Contemporary Art - Berlin.

    KW 当代艺术研究所，柏林艺术圈的核心机构之一。
    """
    source = "KW Institute"
    city = "Berlin"
    parser_key = "kw_institute"
    institution_type = "museum"
    list_url = "https://www.kw-berlin.de/en/"
    link_patterns = [
        r"kw-berlin\.de/en/[^/]+",
    ]
