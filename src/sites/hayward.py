from src.sites.base import BaseSiteParser


class HaywardParser(BaseSiteParser):
    """Hayward Gallery - London.

    海沃德美术馆，位于南岸艺术中心，以雄心勃勃的当代艺术展览著称。
    注意：受 Cloudflare 403 保护。curl_cffi 已测试失败（2026-05-27）。勿再尝试。
    """

    source = "Hayward Gallery"
    city = "London"
    parser_key = "hayward"
    institution_type = "museum"
    status = "BLOCKED_CLOUDFLARE"
    list_url = "https://www.southbankcentre.co.uk/venues/hayward-gallery"
    link_patterns = [
        r"southbankcentre\.co\.uk/whats-on/[a-z0-9-]+",
    ]
    use_curl_cffi = True
