from src.sites.base import BaseSiteParser


class MuseumLudwigParser(BaseSiteParser):
    """Museum Ludwig - Cologne.

    路德维希博物馆，科隆最重要的现代艺术博物馆，以毕加索和波普艺术收藏闻名。
    """

    source = "Museum Ludwig"
    city = "Cologne"
    parser_key = "museum_ludwig"
    institution_type = "museum"
    list_url = "https://www.museum-ludwig.de/en/home/exhibitions"
    link_patterns = [
        r"museum-ludwig\.de/en/home/exhibitions/[^/]+",
    ]
