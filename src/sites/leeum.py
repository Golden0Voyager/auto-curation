from src.sites.base import BaseSiteParser

class LeeumParser(BaseSiteParser):
    """Leeum Samsung Museum of Art - Seoul.

    三星 Leeum 美术馆（现名 Leeum HOAM），首尔最重要的私立美术馆之一。
    注意：网站为 SPA，静态 HTML 无展览链接，需要 Playwright 渲染。
    """
    source = "Leeum Samsung Museum"
    city = "Seoul"
    parser_key = "leeum"
    institution_type = "museum"
    list_url = "https://www.leeumhoam.org/leeum/exhibition"
    use_playwright = True
    # NOTE: The SPA only renders ~4 current exhibitions on the list page.
    # No past/archive exhibition list is accessible without interaction.
    link_patterns = [
        r"leeumhoam\.org/leeum/exhibition/\d+",
    ]
