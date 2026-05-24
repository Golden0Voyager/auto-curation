from src.sites.base import BaseSiteParser

class UCCAParser(BaseSiteParser):
    """UCCA Center for Contemporary Art - Beijing.

    尤伦斯当代艺术中心，中国当代艺术重要展览平台。
    """
    source = "UCCA Center for Contemporary Art"
    city = "Beijing"
    parser_key = "ucca"
    list_url = "https://ucca.org.cn/en/exhibitions/ucca-beijing/"
    extra_list_urls = [
        "https://ucca.org.cn/en/exhibitions/ucca-edge/past/",
        "https://ucca.org.cn/en/exhibitions/ucca-dune/",
        "https://ucca.org.cn/en/exhibitions/ucca-clay/",
        "https://ucca.org.cn/en/exhibitions/ucca-offsite/past/",
    ]
    link_patterns = [
        r"ucca\.org\.cn/en/exhibition/[^/]+/$",
    ]
