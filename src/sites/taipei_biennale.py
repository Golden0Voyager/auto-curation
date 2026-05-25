from src.sites.base import BaseSiteParser

class TaipeiBiennialParser(BaseSiteParser):
    """Taipei Biennial.

    台北双年展，由台北市立美术馆主办，亚洲重要的当代艺术双年展。
    """
    source = "Taipei Biennial"
    city = "Taipei"
    parser_key = "taipei_biennale"
    institution_type = "biennial"
    list_url = "https://www.tfam.museum/Exhibition/Exhibition.aspx?ddlLang=en"
    link_patterns = [
        r"tfam\.museum/Exhibition/ExhibitionTheme\.aspx\?[^\"]+",
    ]
