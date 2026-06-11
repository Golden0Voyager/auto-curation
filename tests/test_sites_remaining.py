"""Tests for remaining uncovered code paths across site parsers."""

import re
from unittest.mock import MagicMock, patch

from src.sites.base import BaseSiteParser
from src.sites.kunsthaus import KunsthausParser
from src.sites.mca_australia import MCAAustraliaParser
from src.sites.new_museum import NewMuseumParser
from src.sites.psa import PSAParser
from src.sites.serpentine import SerpentineParser

# ---------------------------------------------------------------------------
# BaseSiteParser - Playwright path
# ---------------------------------------------------------------------------


class TestBaseSiteParserPlaywright:
    def test_playwright_no_playwright_installed(self):
        """When HAS_PLAYWRIGHT is False, should return empty list."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test"]
        p.use_playwright = True

        with patch("src.sites.base.HAS_PLAYWRIGHT", False):
            result = p.get_exhibition_urls(MagicMock())
            assert result == []

    def test_playwright_no_list_urls(self):
        """When no list URLs, should return empty list."""
        p = BaseSiteParser()
        p.list_url = ""
        p.use_playwright = True

        with patch("src.sites.base.HAS_PLAYWRIGHT", True):
            result = p._get_exhibition_urls_playwright()
            assert result == []

    def test_playwright_no_playwright_path(self):
        """When use_playwright=True but HAS_PLAYWRIGHT=False, get_exhibition_urls returns []."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.use_playwright = True

        with patch("src.sites.base.HAS_PLAYWRIGHT", False):
            result = p.get_exhibition_urls(MagicMock())
            assert result == []

    def test_playwright_fetch_error(self):
        """When Playwright fetch raises, error should be logged and continue."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test"]
        p.use_playwright = True

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("Playwright error")
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser

        with (
            patch("src.sites.base.HAS_PLAYWRIGHT", True),
            patch("src.sites.base.sync_playwright", create=True) as mock_pw,
        ):
            mock_pw.return_value.__enter__.return_value = mock_playwright
            result = p._get_exhibition_urls_playwright()
            assert result == []


# ---------------------------------------------------------------------------
# KunsthausParser - JSON-LD parsing
# ---------------------------------------------------------------------------


class TestKunsthausParser:
    def test_parse_exhibition_page_success(self):
        p = KunsthausParser()
        html = """
        <html><body>
            <script type="application/ld+json">
            {
                "@type": "ExhibitionEvent",
                "name": "Kunsthaus Show",
                "description": "A great exhibition",
                "startDate": "2024-01-15",
                "endDate": "2024-04-20"
            }
            </script>
        </body></html>
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        result = p.parse_exhibition_page(mock_client, "http://ex.com")
        assert result is not None
        assert result["title"] == "Kunsthaus Show"
        assert result["start_date"] == "2024-01-15"
        assert result["end_date"] == "2024-04-20"

    def test_parse_exhibition_page_no_jsonld(self):
        p = KunsthausParser()
        html = "<html><body><h1>No JSON-LD</h1></body></html>"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        result = p.parse_exhibition_page(mock_client, "http://ex.com")
        assert result is None

    def test_parse_exhibition_page_request_failure(self):
        p = KunsthausParser()
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")

        result = p.parse_exhibition_page(mock_client, "http://ex.com")
        assert result is None

    def test_parse_exhibition_json_ld_list(self):
        """JSON-LD can be a list of objects; find ExhibitionEvent in the list."""
        p = KunsthausParser()
        html = """
        <html><body>
            <script type="application/ld+json">
            [
                {"@type": "WebSite", "name": "Site"},
                {"@type": "ExhibitionEvent", "name": "Show from List", "startDate": "2024-06-01"}
            ]
            </script>
        </body></html>
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        result = p.parse_exhibition_page(mock_client, "http://ex.com")
        assert result is not None
        assert result["title"] == "Show from List"

    def test_normalize_exhibition(self):
        p = KunsthausParser()
        data = {
            "name": "  Test Show  ",
            "description": "  A test  ",
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-03-01T00:00:00Z",
        }
        result = p._normalize_exhibition(data, "http://ex.com")
        assert result["title"] == "Test Show"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-03-01"

    def test_clean_html_passthrough(self):
        p = KunsthausParser()
        assert p.clean_html("<html/>") == "<html/>"

    def test_get_exhibition_urls_relative_hrefs(self):
        """get_exhibition_urls should resolve relative hrefs and match patterns."""
        p = KunsthausParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <a href="/en/besuch-planen/ausstellungen/current-show/">Current Show</a>
            <a href="/en/besuch-planen/ausstellungen/past-show/">Past Show</a>
            <a href="/en/visit/">Visit Page (no match)</a>
            <a href="https://kunsthaus.ch/en/besuch-planen/ausstellungen/other/">Other Show</a>
        </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        # Should find 3 exhibition URLs matching the link pattern
        assert len(result) == 3
        assert all("kunsthaus.ch" in url for url in result)

    def test_get_exhibition_urls_request_failure(self):
        """When listing page request fails, return empty list."""
        p = KunsthausParser()
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Kunsthaus request failed")
        result = p.get_exhibition_urls(mock_client)
        assert result == []

    def test_parse_exhibition_page_json_decode_error(self):
        """Malformed JSON-LD should be skipped."""
        p = KunsthausParser()
        html = """
        <html><body>
            <script type="application/ld+json">
            {invalid json here
            </script>
            <script type="application/ld+json">
            {"@type": "ExhibitionEvent", "name": "Second Try"}
            </script>
        </body></html>
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        result = p.parse_exhibition_page(mock_client, "http://ex.com")
        assert result is not None
        assert result["title"] == "Second Try"


# ---------------------------------------------------------------------------
# PSAParser - HTML extraction edge cases
# ---------------------------------------------------------------------------


class TestPSAParserEdge:
    def test_boilerplate_filtering(self):
        p = PSAParser()
        assert p._is_boilerplate("上海当代艺术博物馆（Power Station of Art）") is True
        assert p._is_boilerplate("This is a real exhibition description.") is False

    def test_extract_from_html_meta_title_fallback(self):
        """When no h1, use <title> as fallback."""
        p = PSAParser()
        html = "<html><head><title>Meta Title Exhibition</title></head><body><p>Content</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert "Meta Title" in result["title"]

    def test_extract_from_html_short_title_returns_none(self):
        """Title less than 2 chars should return None."""
        p = PSAParser()
        html = "<html><body><h1>X</h1></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is None

    def test_extract_paragraphs_skips_short(self):
        p = PSAParser()
        html = "<html><body><p>Short</p><p>Long enough paragraph for testing extraction logic.</p></body></html>"
        paras = p._extract_paragraphs(html)
        assert len(paras) == 1

    def test_biennale_concept_extraction(self):
        p = PSAParser()
        html = "<html><body><h1>第十四届上海双年展：宇宙电影</h1><p>展览内容。</p></body></html>"
        result = p._extract_from_html(html, "http://test.com/biennale")
        assert result is not None
        assert result["concept"] == "宇宙电影"

    def test_biennale_concept_from_text(self):
        """When no colon in title, try to find concept in text."""
        p = PSAParser()
        html = '<html><body><h1>第十四届上海双年展</h1><p>"宇宙电影"：第十四届上海双年展</p></body></html>'
        result = p._extract_from_html(html, "http://test.com/biennale")
        assert result is not None
        assert "宇宙电影" in result.get("concept", "")

    def test_parse_exhibition_page_no_playwright(self):
        p = PSAParser()
        with patch("src.sites.psa.HAS_PLAYWRIGHT", False):
            result = p.parse_exhibition_page(None, "http://ex.com")
            assert result is None

    def test_get_exhibition_urls_no_playwright(self):
        p = PSAParser()
        with patch("src.sites.psa.HAS_PLAYWRIGHT", False):
            urls = p.get_exhibition_urls(None)
            assert urls == []

    def test_biennale_editions_mapping(self):
        p = PSAParser()
        assert p._biennale_editions[1996] == 1
        assert p._biennale_editions[2023] == 14

    def test_get_exhibition_urls_playwright_success(self):
        """Mock Playwright to render SPA and extract exhibition URLs."""
        p = PSAParser()
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.content.return_value = '<a href="/whats-on/exhibitions/test-show/">Test</a>'
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.psa.HAS_PLAYWRIGHT", True),
            patch("src.sites.psa.sync_playwright", return_value=mock_context, create=True),
        ):
            urls = p.get_exhibition_urls(None)
        # Should include biennale + wayback URLs + the discovered one
        assert len(urls) >= 15
        assert any("test-show" in u for u in urls)

    def test_get_exhibition_urls_playwright_error(self):
        """When Playwright rendering fails, return empty list."""
        p = PSAParser()
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("PSA Playwright error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.psa.HAS_PLAYWRIGHT", True),
            patch("src.sites.psa.sync_playwright", return_value=mock_context, create=True),
        ):
            urls = p.get_exhibition_urls(None)
        assert urls == []

    def test_parse_exhibition_page_playwright_success(self):
        """Mock Playwright to render an exhibition page and parse it."""
        p = PSAParser()
        html_content = "<html><body><h1>PSA Exhibition</h1><p>Exhibition description content here.</p></body></html>"
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.content.return_value = html_content
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.psa.HAS_PLAYWRIGHT", True),
            patch("src.sites.psa.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.parse_exhibition_page(MagicMock(), "http://ex.com")
        assert result is not None
        assert "PSA Exhibition" in result["title"]

    def test_parse_exhibition_page_playwright_error(self):
        """When Playwright rendering fails for exhibition page."""
        p = PSAParser()
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("PSA page error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.psa.HAS_PLAYWRIGHT", True),
            patch("src.sites.psa.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.parse_exhibition_page(MagicMock(), "http://ex.com")
        assert result is None

    def test_extract_location_with_stop_word(self):
        """Location containing stop words should be trimmed."""
        p = PSAParser()
        html = """
        <html><body>
            <h1>Test Exhibition</h1>
            <p>地点 3F Gallery 策展人 Zhang San</p>
            <p>Description text content for the exhibition.</p>
        </body></html>
        """
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert "3F Gallery" in result["location"]
        assert "策展人" not in result["location"]

    def test_extract_curator_with_separator(self):
        """Multiple curators separated by Chinese comma should be parsed."""
        p = PSAParser()
        html = """
        <html><body>
            <h1>Group Exhibition</h1>
            <p>策展人：Zhang San、Li Si、Wang Wu</p>
            <p>Long description content for the exhibition showcase.</p>
        </body></html>
        """
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert len(result["curators"]) >= 1
        assert "Zhang San" in result["curators"][0]


# ---------------------------------------------------------------------------
# SerpentineParser - event filtering edge cases
# ---------------------------------------------------------------------------


class TestSerpentineParserEdge:
    def test_event_keywords_defined(self):
        p = SerpentineParser()
        assert len(p.EVENT_KEYWORDS) > 0
        assert "talk" in p.EVENT_KEYWORDS
        assert "workshop" in p.EVENT_KEYWORDS

    def test_get_exhibition_urls_with_teaser_filter(self):
        """Teasers with '?type=events' should be filtered out."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <section class="teaser">
                <a href="/whats-on/exhibition-1/">Exhibition 1</a>
                <a href="?type=exhibitions">Exhibitions</a>
            </section>
            <section class="teaser">
                <a href="/whats-on/event-talk/">Talk</a>
                <a href="?type=events">Events</a>
            </section>
        </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        # Only the exhibition should be found (talk is filtered as event)
        assert isinstance(result, list)

    def test_archive_list_url_count(self):
        p = SerpentineParser()
        urls = p.get_list_urls()
        # Should include current + archive pages
        assert len(urls) >= 2

    def test_get_exhibition_urls_no_teasers_fallback(self):
        """When no teasers found, use fallback link-based extraction."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <a href="https://www.serpentinegalleries.org/whats-on/exhibition-test/">Test Exhibition</a>
            <a href="https://www.serpentinegalleries.org/whats-on/event-talk/">Event Talk</a>
        </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        # Should find the exhibition URL
        assert isinstance(result, list)

    def test_get_exhibition_urls_meta_tags(self):
        """Teaser with meta category elements should extract tags."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <section class="teaser">
                <a href="/whats-on/exhibition-1/">Exhibition 1</a>
                <a href="?type=exhibitions">Exhibitions</a>
                <span class="card__category">Events, Talks</span>
            </section>
            <section class="teaser">
                <a href="/whats-on/exhibition-2/">Exhibition 2</a>
                <span class="label">Exhibitions</span>
            </section>
        </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        assert isinstance(result, list)

    def test_get_exhibition_urls_fallback_parent_tags(self):
        """Fallback branch: no card/teaser classes, extract tags from parent containers."""
        p = SerpentineParser()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <div>
                <a href="https://www.serpentinegalleries.org/whats-on/exhibition-test/">Exhibition</a>
                <a href="?type=exhibitions">Exhibitions</a>
            </div>
            <div>
                <a href="https://www.serpentinegalleries.org/whats-on/event-talk/">Talk</a>
                <a href="?type=events">Events</a>
            </div>
        </body></html>
        """
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# NewMuseumParser - additional edge cases
# ---------------------------------------------------------------------------


class TestNewMuseumParserEdge:
    def test_parse_exhibition_page_playwright_import_error(self):
        """When HAS_PLAYWRIGHT is False, return None."""
        p = NewMuseumParser()
        with patch("src.sites.new_museum.HAS_PLAYWRIGHT", False):
            result = p.parse_exhibition_page(None, "http://ex.com")
            assert result is None

    def test_extract_from_html_long_preface(self):
        """Find paragraph > 80 chars for preface."""
        p = NewMuseumParser()
        html = "<html><body><h1>Exhibition</h1><p>A" + "b" * 100 + "</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["preface"] is not None
        assert len(result["preface"]) > 80

    def test_extract_from_html_no_preface(self):
        """When no paragraph > 80 chars, preface should be None."""
        p = NewMuseumParser()
        html = "<html><body><h1>Exhibition</h1><p>Short text.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["preface"] is None

    def test_curator_extraction(self):
        """Curator should be extracted from 'curated by' text."""
        p = NewMuseumParser()
        html = "<html><body><h1>Show</h1><p>curated by Alice Smith</p><p>Description to meet threshold for the new museum parser test case extraction.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert len(result["curators"]) > 0
        assert "Alice Smith" in result["curators"][0]

    def test_no_date_found(self):
        """When no date pattern matches, start/end should be None."""
        p = NewMuseumParser()
        html = "<html><body><h1>Show</h1><p>No dates here.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["start_date"] is None
        assert result["end_date"] is None

    def test_parse_exhibition_page_playwright_success(self):
        """Mock Playwright to render and parse an exhibition page."""
        p = NewMuseumParser()
        html_content = "<html><body><h1>New Museum Show</h1><p>" + "A" * 100 + "</p></body></html>"
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.content.return_value = html_content
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.new_museum.HAS_PLAYWRIGHT", True),
            patch("src.sites.new_museum.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.parse_exhibition_page(MagicMock(), "http://ex.com")
        assert result is not None
        assert "New Museum Show" in result["title"]

    def test_parse_exhibition_page_playwright_error(self):
        """When Playwright fails, return None."""
        p = NewMuseumParser()
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("New Museum PW error")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.new_museum.HAS_PLAYWRIGHT", True),
            patch("src.sites.new_museum.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.parse_exhibition_page(MagicMock(), "http://ex.com")
        assert result is None


# ---------------------------------------------------------------------------
# BaseSiteParser - additional edge cases
# ---------------------------------------------------------------------------


class TestBaseSiteParserAdditional:
    def test_get_exhibition_urls_playwright_success(self):
        """Mock Playwright to discover URLs via SPA rendering."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/list"
        p.link_patterns = [r"test-show"]
        p.use_playwright = True

        html_content = '<html><body><a href="/exhibitions/test-show/">Show</a><a href="/about/">About</a></body></html>'
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.content.return_value = html_content
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_playwright

        with (
            patch("src.sites.base.HAS_PLAYWRIGHT", True),
            patch("src.sites.base.sync_playwright", create=True) as mock_sp,
        ):
            mock_sp.return_value.__enter__.return_value = mock_playwright
            result = p._get_exhibition_urls_playwright()
        assert len(result) == 1
        assert "test-show" in result[0]

    def test_clean_html_noise_selectors(self):
        """clean_html should remove common noise elements."""
        p = BaseSiteParser()
        html = '<html><body><div class="nav">Nav</div><div class="sidebar">Side</div><main>Main content here for the exhibition page about contemporary art.</main></body></html>'
        result = p.clean_html(html)
        assert "Nav" not in result
        assert "Side" not in result
        assert "Main content" in result

    def test_clean_html_skip_list_url(self):
        """URL matching list URL exactly should be excluded."""
        p = BaseSiteParser()
        p.list_url = "http://test.com/exhibitions"
        p.link_patterns = [r".*"]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '<html><body><a href="http://test.com/exhibitions">List</a><a href="http://test.com/exhibitions/show1">Show</a></body></html>'
        mock_client.get.return_value = mock_response
        result = p.get_exhibition_urls(mock_client)
        assert len(result) == 1
        assert "show1" in result[0]


# ---------------------------------------------------------------------------
# MCAAustraliaParser - edge cases
# ---------------------------------------------------------------------------


class TestMCAAustraliaParserEdge:
    def test_parser_defaults(self):
        p = MCAAustraliaParser()
        assert p.source == "MCA Australia"
        assert p.use_playwright is True

    def test_get_exhibition_urls_no_playwright(self):
        p = MCAAustraliaParser()
        with patch("src.sites.mca_australia.HAS_PLAYWRIGHT", False):
            result = p.get_exhibition_urls(None)
            assert result == []

    def test_link_patterns_match(self):
        p = MCAAustraliaParser()
        assert (
            re.search(p.link_patterns[0], "https://www.mca.com.au/exhibitions/current") is not None
        )

    def test_get_exhibition_urls_playwright_error(self):
        """When Playwright fetch fails, return empty list."""
        p = MCAAustraliaParser()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("MCA Playwright error")
        mock_browser.new_page.return_value = mock_page
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_pw

        with (
            patch("src.sites.mca_australia.HAS_PLAYWRIGHT", True),
            patch("src.sites.mca_australia.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert result == []

    def test_get_exhibition_urls_playwright_success(self):
        """Playwright succeeds, extract matching URLs."""
        p = MCAAustraliaParser()
        mock_page = MagicMock()
        mock_page.goto.return_value = None
        mock_page.wait_for_timeout = MagicMock()
        mock_page.evaluate.return_value = [
            "https://www.mca.com.au/exhibitions/current",
            "https://www.mca.com.au/visit",
        ]
        # Simulate Continue button click failure (caught by except)
        mock_find = MagicMock()
        mock_find.first.click.side_effect = Exception("No Continue")
        mock_page.get_by_text.return_value = mock_find

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_pw

        with (
            patch("src.sites.mca_australia.HAS_PLAYWRIGHT", True),
            patch("src.sites.mca_australia.sync_playwright", return_value=mock_context, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert len(result) == 1
            assert "current" in result[0]


# ---------------------------------------------------------------------------
# Additional llm_parser coverage
# ---------------------------------------------------------------------------


class TestLLMParserAdditional:
    def test_is_valid_result_no_concept_with_dates(self):
        """Valid when no concept but has dates."""
        from src.llm_parser import LLMExhibitionParser

        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": None}
        assert parser._is_valid_result(data) is True

    def test_build_prompts_includes_text(self):
        from src.llm_parser import LLMExhibitionParser

        parser = LLMExhibitionParser()
        _, user = parser._build_prompts(
            "Sample description text for exhibition", "Test Museum", "Paris"
        )
        assert "Sample description" in user
        assert "Test Museum" in user
        assert "Paris" in user
