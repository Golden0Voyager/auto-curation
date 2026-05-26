from src.sites.base import BaseSiteParser

class MCAAustraliaParser(BaseSiteParser):
    """Museum of Contemporary Art Australia - Sydney.

    澳大利亚当代艺术博物馆，悉尼环形码头的标志性艺术机构。
    注意：网站为 SPA，静态 HTML 无展览链接，需要 Playwright 渲染。
    """
    source = "MCA Australia"
    city = "Sydney"
    parser_key = "mca_australia"
    institution_type = "museum"
    status = "BLOCKED_SPA"
    list_url = "https://www.mca.com.au/exhibitions/"
    use_playwright = True
    link_patterns = [
        r"mca\.com\.au/exhibitions/[^/]+",
    ]
