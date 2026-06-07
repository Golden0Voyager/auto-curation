from src.sites.base import BaseSiteParser


class AstrupFearnleyParser(BaseSiteParser):
    """Astrup Fearnley Museet - Oslo.

    奥斯陆 Astrup Fearnley 现代艺术博物馆，以国际当代艺术收藏闻名。
    """

    source = "Astrup Fearnley Museet"
    city = "Oslo"
    parser_key = "astrup_fearnley"
    institution_type = "museum"
    list_url = "https://afmuseet.no/en/exhibitions/"
    link_patterns = [
        r"afmuseet\.no/en/exhibitions/[^/]+",
    ]
