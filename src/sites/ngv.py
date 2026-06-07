from src.sites.base import BaseSiteParser


class NGVParser(BaseSiteParser):
    """National Gallery of Victoria - Melbourne.

    维多利亚州国立美术馆，澳大利亚历史最悠久、规模最大的美术馆。
    """

    source = "NGV"
    city = "Melbourne"
    parser_key = "ngv"
    institution_type = "museum"
    list_url = "https://www.ngv.vic.gov.au/whats-on/exhibitions/"
    link_patterns = [
        r"ngv\.vic\.gov\.au/exhibition/[^/]+",
    ]
