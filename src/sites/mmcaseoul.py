"""MMCA Seoul (National Museum of Modern and Contemporary Art, Korea).

韩国国立现代美术馆，首尔馆。

当前状态：官网从中国境外访问超时（ERR_TIMED_OUT），疑似地理屏蔽或
网络路由问题。英文官网 https://www.mmca.go.kr/eng/ 同样无法连接。

解决方案（未来）：
1. 使用韩国境内代理/VPS 测试连接。
2. 查找韩国政府开放数据门户 (data.go.kr) 中是否有该馆展览 API。
3. 尝试通过 Artsy、Artforum 等第三方平台抓取展览数据。
"""
import logging
from typing import List, Optional
from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.mmcaseoul")


class MMCASeoulParser:
    """Placeholder parser — site geo-blocked / unreachable."""
    source = "MMCA Seoul"
    city = "Seoul"
    strategy = ParserStrategy.HTML_LLM
    parser_key = "mmcaseoul"
    list_url = "https://www.mmca.go.kr/eng/exhibitions/exhibitionsList.do"

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        logger.warning(
            "[MMCA Seoul] Site unreachable (ERR_TIMED_OUT). Possibly geo-blocked. "
            "Please verify network connectivity or use an in-country proxy."
        )
        return []

    def get_exhibition_urls(self, client, since_year: Optional[int] = None) -> List[str]:
        return []

    def clean_html(self, html: str) -> str:
        return html
