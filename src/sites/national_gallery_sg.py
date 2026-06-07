from src.sites.base import BaseSiteParser


class NationalGallerySGParser(BaseSiteParser):
    """National Gallery Singapore.

    新加坡国家美术馆，东南亚最大的现代艺术博物馆。
    """

    source = "National Gallery Singapore"
    city = "Singapore"
    parser_key = "national_gallery_sg"
    institution_type = "museum"
    list_url = "https://www.nationalgallery.sg/sg/en/whats-on.html"
    link_patterns = [
        r"nationalgallery\.sg/sg/en/exhibitions/[^/]+\.html",
    ]
