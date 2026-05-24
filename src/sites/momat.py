from src.sites.base import BaseSiteParser

class MOMATParser(BaseSiteParser):
    """The National Museum of Modern Art, Tokyo.

    东京国立近代美术馆，日本最重要的现代艺术博物馆。
    注意：展览列表通过 JS 动态加载，静态 HTML 无详情链接，需要 Playwright 或 API 解析。
    """
    source = "MOMAT"
    city = "Tokyo"
    parser_key = "momat"
    institution_type = "museum"
    list_url = "https://www.momat.go.jp/exhibitions"
    link_patterns = [
        r"momat\.go\.jp/english/exhibitions/[^/]+",
    ]
