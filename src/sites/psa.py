import logging
import re
from typing import List, Optional, Dict, Any

from src.sites.base import BaseSiteParser, ParserStrategy

logger = logging.getLogger("auto_curation.sites.psa")

# Playwright is an optional dependency for SPA scraping
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False


class PSAParser:
    """Power Station of Art (PSA) - Shanghai.

    上海当代艺术博物馆，中国大陆首家公立当代艺术馆。
    官网为 React SPA，必须使用 Playwright 渲染后才能提取内容。
    """
    source = "Power Station of Art"
    city = "Shanghai"
    strategy = ParserStrategy.HTML_LLM
    parser_key = "psa"
    use_playwright = True
    list_url = "https://www.powerstationofart.com/whats-on/exhibitions"
    link_patterns = [
        r"/whats-on/exhibitions/[^/]+$",
    ]

    # 上海双年展历届页面（1996-2023）+ 当前届
    _biennale_urls = [
        f"https://www.powerstationofart.com/whats-on/programs/shanghai-biennale-{y}"
        for y in [1996, 1998, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2023]
    ] + ["https://www.powerstationofart.com/whats-on/programs/shanghai-biennale"]

    # Wayback Machine 发现的历史展览（官网已下架但仍可访问）
    _wayback_urls = [
        "https://www.powerstationofart.com/whats-on/exhibitions/a-room-that-can-move-zhang-enli",
        "https://www.powerstationofart.com/whats-on/exhibitions/annette-messager",
        "https://www.powerstationofart.com/whats-on/exhibitions/art-of-craft",
        "https://www.powerstationofart.com/whats-on/exhibitions/biennale-wave",
        "https://www.powerstationofart.com/whats-on/exhibitions/boltanski-storage-memory",
        "https://www.powerstationofart.com/whats-on/exhibitions/chalayan-archipalego",
        "https://www.powerstationofart.com/whats-on/exhibitions/clark-passing-through-the-architecture",
        "https://www.powerstationofart.com/whats-on/exhibitions/decorum-carpets-and-tapestries-by-artists",
        "https://www.powerstationofart.com/whats-on/exhibitions/ding-ding-and-herge",
        "https://www.powerstationofart.com/whats-on/exhibitions/ding-li-ren-xia-yang",
        "https://www.powerstationofart.com/whats-on/exhibitions/ecp-2021-exhibition",
        "https://www.powerstationofart.com/whats-on/exhibitions/ecp-2022",
        "https://www.powerstationofart.com/whats-on/exhibitions/emerging-curator-project-2018-exhibition",
        "https://www.powerstationofart.com/whats-on/exhibitions/emerging-curator-project-2019-exhibitionnn",
        "https://www.powerstationofart.com/whats-on/exhibitions/emerging-curator-project-2020-exhibition",
        "https://www.powerstationofart.com/whats-on/exhibitions/helene-binet-2019",
        "https://www.powerstationofart.com/whats-on/exhibitions/henri-michaux-and-mu-xin",
        "https://www.powerstationofart.com/whats-on/exhibitions/henryk-tomaszewski",
        "https://www.powerstationofart.com/whats-on/exhibitions/jean-nouvel-in-my-head-in-my-eye-belonging",
        "https://www.powerstationofart.com/whats-on/exhibitions/john-hedjuk",
        "https://www.powerstationofart.com/whats-on/exhibitions/kazuhiro-yamanaka",
        "https://www.powerstationofart.com/whats-on/exhibitions/li-shan",
        "https://www.powerstationofart.com/whats-on/exhibitions/liang-shao-ji-thematic-exhibition",
        "https://www.powerstationofart.com/whats-on/exhibitions/lu-tai-ji-hua",
        "https://www.powerstationofart.com/whats-on/exhibitions/m-m-paris-shanghai",
        "https://www.powerstationofart.com/whats-on/exhibitions/taiwan-architectual",
        "https://www.powerstationofart.com/whats-on/exhibitions/the-challenging-souls",
        "https://www.powerstationofart.com/whats-on/exhibitions/the-return-of-the-guest",
        "https://www.powerstationofart.com/whats-on/exhibitions/tree-tree-cartier-art-foundation",
        "https://www.powerstationofart.com/whats-on/exhibitions/van-cleef-aprel",
        "https://www.powerstationofart.com/whats-on/exhibitions/wang-xing-wei-in-shanghai",
        "https://www.powerstationofart.com/whats-on/exhibitions/who-is-he",
        "https://www.powerstationofart.com/whats-on/exhibitions/xia-yang-collection",
    ]

    def get_list_urls(self, since_year: Optional[int] = None) -> List[str]:
        return [self.list_url]

    def get_exhibition_urls(self, client, since_year: Optional[int] = None) -> List[str]:
        """Use Playwright to render the SPA and discover exhibition URLs."""
        if not HAS_PLAYWRIGHT:
            logger.error(
                "[PSA] Playwright is required for PSA scraping but not installed. "
                "Install it with: uv pip install playwright && python -m playwright install chromium"
            )
            return []

        urls = set()
        # 1. 常规展览列表
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.list_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                html = page.content()
                browser.close()
        except Exception as e:
            logger.error(f"[PSA] Playwright failed to load listing page: {e}")
            return []

        for href in re.findall(r'href="(/whats-on/exhibitions/[^"]+)"', html):
            if href == "/whats-on/exhibitions":
                continue
            urls.add(f"https://www.powerstationofart.com{href}")

        # 2. 上海双年展（历届 + 当前届）
        for biennale_url in self._biennale_urls:
            urls.add(biennale_url)

        # 3. Wayback Machine 发现的历史展览（官网已下架）
        for wayback_url in self._wayback_urls:
            urls.add(wayback_url)

        logger.info(f"[PSA] Total discovered: {len(urls)} exhibition URLs (including {len(self._biennale_urls)} Shanghai Biennale editions, {len(self._wayback_urls)} from Wayback).")
        return sorted(urls)

    def parse_exhibition_page(self, client, url: str) -> Optional[Dict[str, Any]]:
        """Use Playwright to render the SPA exhibition page and extract structured data."""
        if not HAS_PLAYWRIGHT:
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                html = page.content()
                browser.close()
        except Exception as e:
            logger.error(f"[PSA] Playwright failed to load {url}: {e}")
            return None

        return self._extract_from_html(html, url)

    # 模板化的机构介绍文本片段（用于过滤 preface）
    _BOILERPLATE_FRAGMENTS = [
        "中国大陆第一家公立当代艺术博物馆",
        "坐落于黄浦江畔",
        "前身为",
        "Power Station of Art",
        "上海当代艺术博物馆（",
    ]

    def _is_boilerplate(self, text: str) -> bool:
        """判断文本是否为模板化的机构介绍。"""
        return any(frag in text for frag in self._BOILERPLATE_FRAGMENTS)

    # 已知上海双年展的届次与年份映射
    _biennale_editions = {
        1996: 1, 1998: 2, 2000: 3, 2002: 4, 2004: 5,
        2006: 6, 2008: 7, 2010: 8, 2012: 9, 2014: 10,
        2016: 11, 2018: 12, 2020: 13, 2023: 14,
    }

    def _extract_paragraphs(self, html: str) -> List[str]:
        """Extract text paragraphs from <p> tags (SPA-safe)."""
        # Extract content from <p> tags
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        result = []
        for p in paras:
            # Remove nested tags
            text = re.sub(r'<[^>]+>', ' ', p).strip()
            # Clean up whitespace
            text = ' '.join(text.split())
            if len(text) > 10:
                result.append(text)
        return result

    def _extract_from_html(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        text = re.sub(r'<[^>]+>', ' ', html)
        paragraphs = self._extract_paragraphs(html)

        # 1. Title: first <h1> or fallback to meta title / strong patterns
        title = ""
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if h1_match:
            title = re.sub(r'<[^>]+>', ' ', h1_match.group(1)).strip()

        if not title or len(title) < 5:
            meta_title = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if meta_title:
                title = meta_title.group(1).strip()

        # 如果标题是默认的博物馆名或为空，说明提取失败，返回 None 触发 LLM fallback
        if not title or title == "Power Station of Art" or len(title) < 2:
            logger.warning(f"[PSA] No valid title found for {url}, will fallback to LLM")
            return None

        # 2. Date range
        start_date = end_date = None
        date_match = re.search(
            r'(\d{4}[\./-]\d{1,2}[\./-]\d{1,2})\s*[-–—]\s*(\d{4}[\./-]\d{1,2}[\./-]\d{1,2})',
            text
        )
        if date_match:
            start_date = date_match.group(1).replace('/', '-').replace('.', '-')
            end_date = date_match.group(2).replace('/', '-').replace('.', '-')

        # 3. Location — 清理策展人/主办方污染
        location = "上海当代艺术博物馆"
        loc_match = re.search(r'地点\s+([^\n\r]{2,40})', text)
        if loc_match:
            raw_loc = loc_match.group(1).strip()
            for stop_word in ['策展人', '主办', '承办', '协办', '支持', '特别']:
                if stop_word in raw_loc:
                    raw_loc = raw_loc[:raw_loc.index(stop_word)].strip()
                    break
            if raw_loc and len(raw_loc) >= 2:
                location = raw_loc

        # 4. Curator — 清理主办方污染 + 过滤非人名
        curators = []
        curator_match = re.search(r'策展人\s*:?\s*([^\n\r]{2,60})', text)
        if curator_match:
            raw_curator = curator_match.group(1).strip()
            # 截断到第一个非策展人关键词
            for stop_word in ['主办', '承办', '协办', '支持', '特别支持', '展期', '地点', '赞助', '计划"', '自']:
                if stop_word in raw_curator:
                    raw_curator = raw_curator[:raw_curator.index(stop_word)].strip()
                    break
            # 分割多个策展人
            for sep in ['、', '，', ',', '  ']:
                if sep in raw_curator:
                    parts = [c.strip() for c in raw_curator.split(sep) if c.strip()]
                    # 过滤掉明显不是人名的（长度>15 或包含特定关键词）
                    curators = [c for c in parts if len(c) <= 15 and '策展' not in c and '计划' not in c and '自' not in c]
                    break
            if not curators and len(raw_curator) <= 15:
                curators = [raw_curator]

        # 5. Preface: from <p> tags, first substantial paragraph that is NOT boilerplate
        preface = None
        for para in paragraphs:
            if (len(para) > 40
                    and not self._is_boilerplate(para)
                    and not any(k in para for k in ['关于PSA', '参观购票', '沪ICP', '展览时间', '展览地点', '策展人'])):
                preface = para
                break

        # 6. Concept: for biennale, extract theme from title or text
        concept = None
        if 'biennale' in url or 'shanghai-biennale' in url:
            # Try to extract theme from title like "第十四届上海双年展：宇宙电影"
            theme_match = re.search(r'[:：]\s*["""]?(.*?)["""]?\s*$', title)
            if theme_match:
                concept = theme_match.group(1).strip()
            # Also try from page text: "主题" 或 "宇宙电影" 等
            if not concept:
                biennale_concept_match = re.search(r'"([^"]{2,30})"\s*[:：]?\s*第[\d一二三四五六七八九十]+届上海双年展', text)
                if biennale_concept_match:
                    concept = biennale_concept_match.group(1)

        return {
            "source": self.source,
            "title": title,
            "preface": preface,
            "concept": concept,
            "curators": curators,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "city": self.city,
            "url": url,
            "artworks": [],
        }

    def clean_html(self, html: str) -> str:
        return html
