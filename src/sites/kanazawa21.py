from src.sites.base import BaseSiteParser


class Kanazawa21Parser(BaseSiteParser):
    """21st Century Museum of Contemporary Art, Kanazawa.

    金泽21世纪美术馆，日本最具创新性的当代艺术博物馆之一。
    """

    source = "21st Century Museum"
    city = "Kanazawa"
    parser_key = "kanazawa21"
    institution_type = "museum"
    list_url = "https://www.kanazawa21.jp/en/exhibitions/"
    link_patterns = [
        r"kanazawa21\.jp/en/exhibitions/[^/]+",
    ]
