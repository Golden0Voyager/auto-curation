from src.sites.base import BaseSiteParser

class SaoPauloBiennialParser(BaseSiteParser):
    """São Paulo Biennial.

    圣保罗双年展，拉丁美洲历史最悠久的国际当代艺术双年展。
    """
    source = "São Paulo Biennial"
    city = "São Paulo"
    parser_key = "saopaulo_biennial"
    institution_type = "biennial"
    list_url = "https://www.bienal.org.br"
    verify_ssl = False
    link_patterns = [
        r"bienal\.org\.br/[^/]+",
    ]
