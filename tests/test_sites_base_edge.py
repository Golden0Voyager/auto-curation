"""Edge case tests for src/sites/base.py — BaseSiteParser."""

from unittest.mock import MagicMock, patch

from src.sites.base import BaseSiteParser, ParserStrategy


class TestGetListUrls:
    def test_list_url_and_extra(self):
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.extra_list_urls = ["http://test.com/archive"]
        urls = p.get_list_urls()
        assert len(urls) == 2
        assert urls[0] == "http://test.com/list"
        assert urls[1] == "http://test.com/archive"

    def test_no_list_url(self):
        p = BaseSiteParser()
        p.list_url = ""
        assert p.get_list_urls() == []


class TestGetExhibitionUrls:
    def test_no_list_urls_returns_empty(self):
        p = BaseSiteParser()
        p.list_url = ""
        p.link_patterns = [r"test"]
        result = p.get_exhibition_urls(MagicMock())
        assert result == []

    def test_finds_urls_matching_pattern(self):
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test\.com/exhibitions/[^/]+"]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
            <html><body>
                <a href="/exhibitions/show1/">Show 1</a>
                <a href="/exhibitions/show2/">Show 2</a>
                <a href="/about/">About</a>
            </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        assert len(result) == 2

    def test_request_failure_returns_urls_from_other_pages(self):
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.extra_list_urls = ["http://test.com/backup"]
        p.link_patterns = [r"test\.com/exhibitions/[^/]+"]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
            <html><body>
                <a href="/exhibitions/backup-show/">Backup Show</a>
            </body></html>
        """
        mock_client.get.side_effect = [
            Exception("Network error"),
            mock_response,
        ]
        result = p.get_exhibition_urls(mock_client)
        assert len(result) == 1
        assert "backup-show" in result[0]

    def test_curl_cffi_path(self):
        """Test the curl_cffi path for Cloudflare bypass."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test\.com/exhibitions/[^/]+"]
        p.use_curl_cffi = True

        mock_response = MagicMock()
        mock_response.text = '<a href="/exhibitions/test/">Test</a>'

        # curl_cffi is not installed, so mock it via sys.modules
        mock_curl = MagicMock()
        mock_curl.requests.get.return_value = mock_response
        with patch.dict(
            "sys.modules", {"curl_cffi": mock_curl, "curl_cffi.requests": mock_curl.requests}
        ):
            result = p.get_exhibition_urls(MagicMock())
            assert len(result) == 1
            assert "test" in result[0]

    def test_verify_ssl_false_path(self):
        """Test the SSL verification disabled path."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test\.com/exhibitions/[^/]+"]
        p.verify_ssl = False

        mock_response = MagicMock()
        mock_response.text = '<a href="/exhibitions/ssl-show/">SSL Show</a>'

        with patch("httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response

            result = p.get_exhibition_urls(MagicMock())
            assert len(result) == 1
            assert "ssl-show" in result[0]


class TestCleanHtml:
    def test_semantic_extraction_with_main(self):
        p = BaseSiteParser()
        html = """
        <html><head><meta name="description" content="Meta desc for test"></head>
        <body>
            <main>
                <h1>Exhibition Title</h1>
                <p>This is a long paragraph about the exhibition with enough text to pass the 300 character threshold for semantic extraction test purposes. Additional content that provides more context about the curatorial vision and the artworks displayed in this exhibition. The goal is to have enough text so the clean_html method picks the semantic extraction path rather than falling through to the full-page noise removal pass.</p>
            </main>
        </body></html>
        """
        result = p.clean_html(html)
        assert "Exhibition Title" in result
        assert "Meta desc" in result

    def test_semantic_extraction_with_article(self):
        p = BaseSiteParser()
        html = """
        <html><body>
            <article>
                <h1>Article Exhibition</h1>
                <p>Long paragraph with enough content to meet the minimum 300 character threshold required for the semantic extraction pass to work correctly in this test scenario. More text about the exhibition and the artists involved in creating the works displayed throughout the gallery space.</p>
            </article>
        </body></html>
        """
        result = p.clean_html(html)
        assert "Article Exhibition" in result

    def test_meta_description_fallback(self):
        """When cleaned text < 200 chars, meta description should be prepended."""
        p = BaseSiteParser()
        html = """
        <html><head><meta name="description" content="Short desc fallback"></head>
        <body>
            <p>Short text.</p>
            <script>var x = 1;</script>
            <nav>Navigation</nav>
            <footer>Footer</footer>
        </body></html>
        """
        result = p.clean_html(html)
        assert "Short desc" in result

    def test_noise_tags_removed(self):
        p = BaseSiteParser()
        html = """
        <html><body>
            <main>
                <p>Exhibition content here with enough text to pass the 300 character threshold for the semantic extraction pass to work in the test environment. Additional content about the exhibition to reach the threshold for the test to pass.</p>
                <nav>Should be removed</nav>
                <footer>Should be removed</footer>
                <script>alert('x')</script>
            </main>
        </body></html>
        """
        result = p.clean_html(html)
        assert "Exhibition content" in result
        assert "removed" not in result

    def test_normalize_text_handles_whitespace(self):
        result = BaseSiteParser._normalize_text("Hello   World\n\nLine 2")
        lines = result.split("\n")
        assert "Hello" in lines[0]
        assert "World" in lines
        assert "Line 2" in result


class TestParserStrategy:
    def test_strategy_values(self):
        assert ParserStrategy.HTML_LLM.value == "html_llm"
        assert ParserStrategy.CSV_LOCAL.value == "csv_local"
        assert ParserStrategy.CSV_REMOTE.value == "csv_remote"
        assert ParserStrategy.REST_API.value == "rest_api"
        assert ParserStrategy.SPARQL.value == "sparql"
        assert ParserStrategy.ARTWORK_ONLY.value == "artwork_only"

    def test_strategy_is_enum(self):
        assert isinstance(ParserStrategy.HTML_LLM, ParserStrategy)


class TestBaseSiteParserCoverageGaps:
    def test_has_playwright_import_error(self):
        import importlib
        import sys
        import src.sites.base

        orig_strategy = src.sites.base.ParserStrategy
        orig_parser = src.sites.base.BaseSiteParser

        with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
            importlib.reload(src.sites.base)
            assert src.sites.base.HAS_PLAYWRIGHT is False

        importlib.reload(src.sites.base)
        assert src.sites.base.HAS_PLAYWRIGHT is True

        src.sites.base.ParserStrategy = orig_strategy
        src.sites.base.BaseSiteParser = orig_parser

    def test_playwright_list_urls_dedup(self):
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test\.com/exhibitions/[^/]+"]
        p.use_playwright = True

        mock_playwright = MagicMock()
        mock_playwright.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = """
            <html><body>
                <a href="http://test.com/list">List URL itself</a>
                <a href="http://test.com/exhibitions/show1">Real Show</a>
            </body></html>
        """

        with patch("src.sites.base.sync_playwright", return_value=mock_playwright), \
             patch("src.sites.base.HAS_PLAYWRIGHT", True):
            urls = p._get_exhibition_urls_playwright()
            assert len(urls) == 1
            assert urls[0] == "http://test.com/exhibitions/show1"

    def test_clean_html_body_noise_selector_skip(self):
        p = BaseSiteParser()
        html = '<body class="widget"><p>Exhibition content here with enough text to pass the 300 character threshold for the semantic extraction pass to work in the test environment. Additional content about the exhibition to reach the threshold for the test to pass.</p></body>'
        result = p.clean_html(html)
        assert "Exhibition content" in result

