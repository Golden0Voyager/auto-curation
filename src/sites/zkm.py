from src.sites.base import BaseSiteParser


class ZKMParser(BaseSiteParser):
    """ZKM | Center for Art and Media - Karlsruhe.

    卡尔斯鲁厄艺术与媒体中心，全球最重要的媒体艺术机构。
    """

    source = "ZKM"
    city = "Karlsruhe"
    parser_key = "zkm"
    institution_type = "museum"
    list_url = "https://zkm.de/en/exhibitions"
    extra_list_urls = ["https://zkm.de/en/exhibition-archive"]
    link_patterns = [
        r"zkm\.de/en/exhibition/\d{4}/\d{2}/[^/]+",
    ]
