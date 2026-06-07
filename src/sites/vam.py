"""V&A Museum (Victoria and Albert Museum) Parser.

伦敦维多利亚与阿尔伯特博物馆，世界最大的艺术与设计博物馆。
官网展览页面为服务端渲染，使用 HTML_LLM 策略。
"""

import logging

from src.sites.base import BaseSiteParser, ParserStrategy

logger = logging.getLogger("auto_curation.sites.vam")


class VAMParser(BaseSiteParser):
    """V&A Museum parser — HTML_LLM strategy."""

    source = "V&A Museum"
    city = "London"
    strategy = ParserStrategy.HTML_LLM
    parser_key = "vam"
    institution_type = "museum"
    list_url = "https://www.vam.ac.uk/whatson?type=exhibition"
    extra_list_urls = [
        "https://www.vam.ac.uk/whatson?type=exhibition&status=current",
        "https://www.vam.ac.uk/whatson?type=exhibition&status=upcoming",
    ]
    link_patterns = [
        r"/exhibitions/",
    ]

    def get_list_urls(self, since_year: int | None = None) -> list[str]:
        urls = [self.list_url]
        urls.extend(self.extra_list_urls)
        return urls
