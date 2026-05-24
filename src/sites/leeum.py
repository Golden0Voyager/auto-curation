from src.sites.base import BaseSiteParser

class LeeumParser(BaseSiteParser):
    """Leeum Samsung Museum of Art - Seoul.

    三星 Leeum 美术馆，首尔最重要的私立美术馆之一。
    注意：网站为 SPA，静态 HTML 无展览链接，需要 Playwright 渲染。
    """
    source = "Leeum Samsung Museum"
    city = "Seoul"
    parser_key = "leeum"
    institution_type = "museum"
    list_url = "https://www.leeum.org/en/exhibitions"
    link_patterns = [
        r"leeum\.org/en/exhibitions/[^/]+",
    ]
