from src.sites.base import BaseSiteParser


class WhitechapelParser(BaseSiteParser):
    """Whitechapel Gallery - London.

    白教堂美术馆，伦敦东区的标志性当代艺术机构。
    注意：受 Cloudflare 403 保护。curl_cffi 已测试失败（2026-05-27）。勿再尝试。
    """

    source = "Whitechapel Gallery"
    city = "London"
    parser_key = "whitechapel"
    institution_type = "museum"
    status = "BLOCKED_CLOUDFLARE"
    list_url = "https://www.whitechapelgallery.org/exhibitions/"
    link_patterns = [
        r"whitechapelgallery\.org/exhibitions/[^/]+",
    ]
    use_curl_cffi = True
