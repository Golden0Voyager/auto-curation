from src.sites.base import BaseSiteParser

class WhitechapelParser(BaseSiteParser):
    """Whitechapel Gallery - London.

    白教堂美术馆，伦敦东区的标志性当代艺术机构。
    注意：受 Cloudflare 403 保护，需要 Playwright 或 stealth headers。
    """
    source = "Whitechapel Gallery"
    city = "London"
    parser_key = "whitechapel"
    institution_type = "museum"
    list_url = "https://www.whitechapelgallery.org/exhibitions/"
    link_patterns = [
        r"whitechapelgallery\.org/exhibitions/[^/]+",
    ]
