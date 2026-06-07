from src.sites.base import BaseSiteParser


class LACMAParser(BaseSiteParser):
    """Los Angeles County Museum of Art.

    洛杉矶郡艺术博物馆，美国西部最大的艺术博物馆。
    注意：受 Cloudflare 403 保护。curl_cffi 已测试失败（2026-05-27）。勿再尝试。
    """

    source = "LACMA"
    city = "Los Angeles"
    parser_key = "lacma"
    institution_type = "museum"
    status = "BLOCKED_CLOUDFLARE"
    list_url = "https://www.lacma.org/exhibitions"
    link_patterns = [
        r"lacma\.org/art/exhibition/[^/]+",
    ]
    use_curl_cffi = True
