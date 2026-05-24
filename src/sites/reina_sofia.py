from src.sites.base import BaseSiteParser

class ReinaSofiaParser(BaseSiteParser):
    """Museo Reina Sofía - Madrid.

    索菲亚王后国家艺术中心博物馆，西班牙最重要的现代艺术博物馆。
    """
    source = "Museo Reina Sofía"
    city = "Madrid"
    parser_key = "reina_sofia"
    institution_type = "museum"
    list_url = "https://www.museoreinasofia.es/en/exhibitions"
    link_patterns = [
        r"museoreinasofia\.es/en/exhibition/[^/]+",
    ]
