"""Tests for src/sites/psa.py — Power Station of Art parser."""

from unittest.mock import patch

from src.sites.psa import PSAParser


class TestPSAParser:
    def test_parser_attributes(self):
        p = PSAParser()
        assert p.source == "Power Station of Art"
        assert p.city == "Shanghai"
        assert p.parser_key == "psa"
        assert p.use_playwright is True
        assert len(p._biennale_urls) > 0
        assert len(p._wayback_urls) > 0

    def test_get_list_urls(self):
        p = PSAParser()
        urls = p.get_list_urls()
        assert "whats-on/exhibitions" in urls[0]

    def test_get_list_urls_with_year(self):
        p = PSAParser()
        urls = p.get_list_urls(since_year=2020)
        assert len(urls) == 1

    def test_get_exhibition_urls_no_playwright(self):
        p = PSAParser()
        with patch("src.sites.psa.HAS_PLAYWRIGHT", False):
            urls = p.get_exhibition_urls(client=None)
            assert urls == []

    def test_parse_exhibition_page_no_playwright(self):
        p = PSAParser()
        with patch("src.sites.psa.HAS_PLAYWRIGHT", False):
            result = p.parse_exhibition_page(None, "http://ex.com")
            assert result is None

    def test_is_boilerplate_matches(self):
        p = PSAParser()
        assert p._is_boilerplate("上海当代艺术博物馆（Power Station of Art）") is True
        assert p._is_boilerplate("真实展览描述内容") is False

    def test_extract_paragraphs(self):
        p = PSAParser()
        html = "<html><body><p>First paragraph content here.</p><p>Second longer paragraph content for testing extraction.</p></body></html>"
        paras = p._extract_paragraphs(html)
        assert len(paras) >= 2
        assert "First paragraph" in paras[0]

    def test_extract_paragraphs_short_skipped(self):
        p = PSAParser()
        html = "<html><body><p>Short</p><p>Long enough paragraph content for the test to verify extraction logic works correctly.</p></body></html>"
        paras = p._extract_paragraphs(html)
        assert len(paras) == 1  # short one skipped

    def test_extract_from_html_basic(self):
        p = PSAParser()
        html = "<html><body><h1>Test Exhibition 展</h1><p>展览描述内容，这是真实展览的文字描述。</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["title"] == "Test Exhibition 展"
        assert result["city"] == "Shanghai"
        assert result["location"] == "上海当代艺术博物馆"

    def test_extract_from_html_with_date(self):
        p = PSAParser()
        html = "<html><body><h1>PSA Exhibition</h1><p>2024-01-15–2024-06-30</p><p>展览内容描述文字。</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["start_date"] == "2024-01-15"

    def test_extract_from_html_with_curator(self):
        p = PSAParser()
        html = "<html><body><h1>Curated Exhibition</h1><p>策展人：王小明</p><p>展览描述文字内容用于测试。测试策展人提取功能。</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert len(result["curators"]) > 0

    def test_extract_from_html_no_title(self):
        p = PSAParser()
        html = "<html><body><p>No title here.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is None

    def test_extract_from_html_power_station_title(self):
        """Title matching 'Power Station of Art' should return None to trigger LLM fallback."""
        p = PSAParser()
        html = "<html><body><h1>Power Station of Art</h1></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is None

    def test_extract_from_html_biennale_concept(self):
        p = PSAParser()
        html = "<html><body><h1>第十四届上海双年展：宇宙电影</h1></body></html>"
        result = p._extract_from_html(html, "http://ex.com/biennale")
        assert result is not None
        assert result["concept"] == "宇宙电影"

    def test_biennale_editions_mapping(self):
        p = PSAParser()
        assert p._biennale_editions[1996] == 1
        assert p._biennale_editions[2023] == 14

    def test_clean_html_passthrough(self):
        p = PSAParser()
        assert p.clean_html("<html/>") == "<html/>"

    def test_get_exhibition_urls_success(self):
        from unittest.mock import MagicMock
        p = PSAParser()

        mock_playwright = MagicMock()
        mock_playwright.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = """
            <html><body>
                <a href="/whats-on/exhibitions">List page itself (skip)</a>
                <a href="/whats-on/exhibitions/real-show">Real Show</a>
            </body></html>
        """

        with patch("src.sites.psa.sync_playwright", return_value=mock_playwright, create=True), \
             patch("src.sites.psa.HAS_PLAYWRIGHT", True):
            urls = p.get_exhibition_urls(client=None)
            assert "https://www.powerstationofart.com/whats-on/exhibitions/real-show" in urls
            assert "https://www.powerstationofart.com/whats-on/exhibitions" not in urls

    def test_extract_from_html_curator_stop_words(self):
        p = PSAParser()
        html = "<html><body><h1>Curated Exhibition</h1><p>策展人: 王小明 主办方：上海博物馆</p><p>展览描述文字内容用于测试。测试策展人提取功能。</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert "王小明" in result["curators"]

    def test_has_playwright_reload(self):
        import importlib
        from unittest.mock import MagicMock, patch

        import src.sites.psa as psa_module

        orig_has_playwright = psa_module.HAS_PLAYWRIGHT
        orig_parser = psa_module.PSAParser

        try:
            with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
                importlib.reload(psa_module)
                assert psa_module.HAS_PLAYWRIGHT is False

            with patch.dict("sys.modules", {
                "playwright": MagicMock(),
                "playwright.sync_api": MagicMock()
            }):
                importlib.reload(psa_module)
                assert psa_module.HAS_PLAYWRIGHT is True
        finally:
            importlib.reload(psa_module)
            psa_module.HAS_PLAYWRIGHT = orig_has_playwright
            psa_module.PSAParser = orig_parser

