"""Tests for src/sites/base.py — BaseSiteParser class."""

import httpx

from src.sites.base import HEADERS, BaseSiteParser, ParserStrategy

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class MinimalParser(BaseSiteParser):
    source = "Test Museum"
    city = "TestCity"
    parser_key = "test"
    list_url = "http://example.com/list"
    link_patterns = [r"/exhibition/\d+"]


class MultiPageParser(BaseSiteParser):
    source = "Multi Museum"
    city = "MultiCity"
    parser_key = "multipage"
    list_url = "http://example.com/exhibitions"
    extra_list_urls = ["http://example.com/past", "http://example.com/archive"]
    link_patterns = [r"/exhibition/\d+"]


class NoURLParser(BaseSiteParser):
    source = "Empty Museum"
    city = "Nowhere"
    parser_key = "empty"
    list_url = ""
    link_patterns = []


class SSLDisabledParser(BaseSiteParser):
    source = "SSL Issues"
    city = "Test"
    parser_key = "ssl_test"
    list_url = "https://bad-ssl.example.com"
    link_patterns = [r"/exhibition/"]
    verify_ssl = False


# ---------------------------------------------------------------------------
# ParserStrategy enum
# ---------------------------------------------------------------------------


class TestParserStrategy:
    def test_enum_values(self):
        assert ParserStrategy.HTML_LLM.value == "html_llm"
        assert ParserStrategy.CSV_LOCAL.value == "csv_local"
        assert ParserStrategy.CSV_REMOTE.value == "csv_remote"
        assert ParserStrategy.REST_API.value == "rest_api"
        assert ParserStrategy.SPARQL.value == "sparql"
        assert ParserStrategy.ARTWORK_ONLY.value == "artwork_only"

    def test_default_strategy_is_html_llm(self):
        parser = MinimalParser()
        assert parser.strategy == ParserStrategy.HTML_LLM


# ---------------------------------------------------------------------------
# HEADERS dict
# ---------------------------------------------------------------------------


class TestHeaders:
    def test_headers_contains_required_keys(self):
        assert "User-Agent" in HEADERS
        assert "Accept" in HEADERS
        assert "Accept-Language" in HEADERS

    def test_user_agent_looks_like_chrome(self):
        assert "Chrome" in HEADERS["User-Agent"]


# ---------------------------------------------------------------------------
# get_list_urls
# ---------------------------------------------------------------------------


class TestGetListUrls:
    def test_returns_list_url_and_extra(self):
        parser = MultiPageParser()
        urls = parser.get_list_urls()
        assert urls == [
            "http://example.com/exhibitions",
            "http://example.com/past",
            "http://example.com/archive",
        ]

    def test_returns_only_list_url_when_no_extra(self):
        parser = MinimalParser()
        urls = parser.get_list_urls()
        assert urls == ["http://example.com/list"]

    def test_returns_empty_when_no_list_url(self):
        parser = NoURLParser()
        urls = parser.get_list_urls()
        assert urls == []

    def test_since_year_passed_through(self):
        """since_year is passed but base implementation may not use it."""
        parser = MinimalParser()
        urls = parser.get_list_urls(since_year=2020)
        assert urls == ["http://example.com/list"]


# ---------------------------------------------------------------------------
# get_exhibition_urls
# ---------------------------------------------------------------------------


class TestGetExhibitionUrls:
    def test_returns_empty_on_no_list_urls(self):
        parser = NoURLParser()
        client = httpx.Client()
        urls = parser.get_exhibition_urls(client)
        assert urls == []

    def test_method_signature(self):
        """Verify method accepts optional since_year."""
        parser = MinimalParser()
        client = httpx.Client()
        urls = parser.get_exhibition_urls(client, since_year=2023)
        assert isinstance(urls, list)


# ---------------------------------------------------------------------------
# clean_html
# ---------------------------------------------------------------------------


class TestCleanHtml:
    def test_removes_script_tags(self):
        parser = MinimalParser()
        html = "<html><body><script>alert('x')</script><p>Hello</p></body></html>"
        result = parser.clean_html(html)
        assert "alert" not in result
        assert "Hello" in result

    def test_removes_style_tags(self):
        parser = MinimalParser()
        html = (
            "<html><head><style>.foo{color:red;}</style></head><body><p>Content</p></body></html>"
        )
        result = parser.clean_html(html)
        assert "color" not in result
        assert "Content" in result

    def test_removes_nav_footer_header(self):
        parser = MinimalParser()
        html = (
            "<html><body>"
            "<nav>Nav</nav>"
            "<footer>Footer</footer>"
            "<header>Header</header>"
            "<main><p>Real content here.</p></main>"
            "</body></html>"
        )
        result = parser.clean_html(html)
        assert "Nav" not in result
        assert "Footer" not in result
        assert "Header" not in result
        assert "Real content" in result

    def test_semantic_selectors_first_pass(self):
        """If <main> tag has enough content, it's used as primary extraction."""
        parser = MinimalParser()
        long_text = "This is the main article content. " * 20
        html = f"<html><body><nav>Nav garbage</nav><main><p>{long_text}</p></main><footer>Footer garbage</footer></body></html>"
        result = parser.clean_html(html)
        assert "This is the main" in result
        assert "Nav garbage" not in result
        assert "Footer garbage" not in result

    def test_article_selector(self):
        """<article> tag should also work as semantic selector."""
        parser = MinimalParser()
        html = (
            "<html><body><article><p>" + "Article content. " * 40 + "</p></article></body></html>"
        )
        result = parser.clean_html(html)
        assert "Article content" in result

    def test_meta_description_included(self):
        """Meta description should be included in output."""
        parser = MinimalParser()
        html = (
            "<html><head>"
            '<meta name="description" content="Meta desc here.">'
            "</head><body><p>Short content.</p></body></html>"
        )
        result = parser.clean_html(html)
        assert "Meta desc here" in result

    def test_role_main_selector(self):
        """role='main' should be used as semantic selector."""
        parser = MinimalParser()
        html = (
            '<html><body><div role="main"><p>'
            + "Role main content area " * 40
            + "</p></div></body></html>"
        )
        result = parser.clean_html(html)
        assert "Role main content" in result

    def test_noise_selectors_removed(self):
        """Noise elements like .cookie, .sidebar, etc. should be removed."""
        parser = MinimalParser()
        long_content = "Real content here. " * 20
        html = f"<html><body><div class='cookie'>Cookie notice</div><div class='sidebar'>Sidebar</div><div class='comments'>Comments</div><div class='breadcrumb'>Breadcrumb</div><p>{long_content}</p></body></html>"
        result = parser.clean_html(html)
        assert "Cookie notice" not in result
        assert "Sidebar" not in result
        assert "Comments" not in result
        assert "Breadcrumb" not in result
        assert "Real content" in result


# ---------------------------------------------------------------------------
# _normalize_text (static method)
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_removes_excess_whitespace(self):
        result = BaseSiteParser._normalize_text("Hello    World\n\n\nTest")
        assert result == "Hello\nWorld\nTest"

    def test_removes_leading_trailing_spaces(self):
        result = BaseSiteParser._normalize_text("  A  \n  B  ")
        assert result == "A\nB"

    def test_handles_empty_string(self):
        result = BaseSiteParser._normalize_text("")
        assert result == ""


# ---------------------------------------------------------------------------
# Default attributes
# ---------------------------------------------------------------------------


class DefaultsOnlyParser(BaseSiteParser):
    """Parser with no overridden defaults for testing default attribute values."""

    source = "Defaults"
    city = "DefaultCity"
    parser_key = "defaults"


class TestDefaultAttributes:
    def test_default_playwright_false(self):
        parser = DefaultsOnlyParser()
        assert parser.use_playwright is False

    def test_default_curl_cffi_false(self):
        parser = DefaultsOnlyParser()
        assert parser.use_curl_cffi is False

    def test_default_verify_ssl_true(self):
        parser = DefaultsOnlyParser()
        assert parser.verify_ssl is True

    def test_default_institution_type_museum(self):
        parser = DefaultsOnlyParser()
        assert parser.institution_type == "museum"

    def test_default_extra_list_urls_empty(self):
        parser = DefaultsOnlyParser()
        assert parser.extra_list_urls == []

    def test_default_link_patterns_empty(self):
        parser = DefaultsOnlyParser()
        assert parser.link_patterns == []

    def test_default_timeouts(self):
        parser = DefaultsOnlyParser()
        assert parser.request_timeout == 60.0
        assert parser.playwright_timeout == 60000.0


# ---------------------------------------------------------------------------
# inheritability
# ---------------------------------------------------------------------------


class TestInheritability:
    def test_subclass_can_override_clean_html(self):
        class CustomClean(BaseSiteParser):
            source = "Custom"
            city = "CustomCity"
            parser_key = "custom"

            def clean_html(self, html):
                return "OVERRIDDEN"

        parser = CustomClean()
        assert parser.clean_html("<html></html>") == "OVERRIDDEN"

    def test_subclass_can_override_get_list_urls(self):
        class CustomList(BaseSiteParser):
            source = "Custom"
            city = "CustomCity"
            parser_key = "customlist"

            def get_list_urls(self, since_year=None):
                return [f"http://ex.com/{since_year}"]

        parser = CustomList()
        urls = parser.get_list_urls(since_year=2024)
        assert urls == ["http://ex.com/2024"]


def test_playwright_url_extraction():
    """Placeholder: Playwright-based URL extraction is tested in specific parsers."""
    pass
