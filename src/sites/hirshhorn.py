"""Hirshhorn Museum and Sculpture Garden.

华盛顿史密森尼学会旗下的现当代艺术博物馆。

当前状态：网站受 Cloudflare Bot Protection 保护（"Just a moment..."挑战页），
Playwright 和常规 HTTP 客户端均无法穿透。Smithsonian Open Access API
需要注册 API Key。

解决方案（未来）：
1. 申请 Smithsonian Open Access API Key（免费）：
   https://www.si.edu/openaccess
2. 实现 REST_API 策略调用 exhibitions 端点。
3. 或使用带 stealth 插件的 Playwright（如 playwright-stealth）尝试绕过 Cloudflare。
"""
import logging
from typing import List, Optional
from src.sites.base import ParserStrategy

logger = logging.getLogger("auto_curation.sites.hirshhorn")


class HirshhornParser:
    """Placeholder parser — blocked by Cloudflare protection."""
    source = "Hirshhorn Museum and Sculpture Garden"
    city = "Washington D.C."
    strategy = ParserStrategy.REST_API
    parser_key = "hirshhorn"
    list_url = "https://hirshhorn.si.edu/exhibitions/"

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        logger.warning(
            "[Hirshhorn] Scraping blocked: Cloudflare Bot Protection. "
            "Please apply for a Smithsonian Open Access API key to enable this parser."
        )
        return []

    def get_exhibition_urls(self, client, since_year: Optional[int] = None) -> List[str]:
        return []

    def get_api_exhibitions(self, since_year: Optional[int] = None, limit: Optional[int] = None):
        logger.warning(
            "[Hirshhorn] API key required. Register at https://www.si.edu/openaccess"
        )
        return []

    def clean_html(self, html: str) -> str:
        return html
