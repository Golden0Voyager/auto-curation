from src.sites.base import BaseSiteParser

class NJPACParser(BaseSiteParser):
    """Nam June Paik Art Center - Seoul.

    白南准艺术中心，全球唯一专注于影像艺术之父的专题美术馆。
    """
    source = "Nam June Paik Art Center"
    city = "Yongin"
    parser_key = "njpac"
    institution_type = "museum"
    list_url = "https://njpart.ggcf.kr/exhibitions"
    link_patterns = [
        r"njpart\.ggcf\.kr/exhibitions/[^/]+",
    ]
