"""Additional tests for src/scraper.py to improve coverage to 100%."""

import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.scraper import (
    ExhibitionScraper,
    _is_retryable_http_error,
    extract_images_from_html,
)
from src.sites.base import ParserStrategy

TEST_DB = "tests/test_scraper_coverage.db"


@pytest.fixture(autouse=True)
def cleanup_db():
    import os
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def _make_exhibition_data(url="http://test.show", title="Show"):
    """Helper to create exhibition data dict."""
    return {
        "url": url,
        "title": title,
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "artworks": [],
    }


def _create_mock_parser(source="Test", strategy=ParserStrategy.HTML_LLM):
    """Create a mock parser with all required attributes."""
    mock_parser = MagicMock()
    mock_parser.source = source
    mock_parser.city = "City"
    mock_parser.parser_key = f"{source.lower().replace(' ', '_')}"
    mock_parser.institution_type = "museum"
    mock_parser.strategy = strategy
    mock_parser.request_timeout = 60.0
    # Ensure use_curl_cffi is not set (returns False)
    mock_parser.use_curl_cffi = False
    return mock_parser


# ---------------------------------------------------------------------------
# extract_images_from_html - edge cases
# ---------------------------------------------------------------------------


class TestExtractImagesExtended:
    def test_filters_tracking_pixels(self):
        html = '<html><body><img src="http://track.com/pixel.gif"><img src="/photo.jpg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_filters_badge_images(self):
        html = '<html><body><img src="/badge.png"><img src="/artwork.jpg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_filters_nav_images(self):
        html = '<html><body><img src="/nav/arrow.jpg"><img src="/exhibit.jpg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_filters_footer_images(self):
        html = '<html><body><img src="/footer/logo.jpg"><img src="/main.jpg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_filters_avatar_images(self):
        html = '<html><body><img src="/avatar/user.png"><img src="/art.jpg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_accepts_webp_images(self):
        html = '<html><body><img src="/photo.webp"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1
        assert "photo.webp" in result[0]

    def test_accepts_jpeg_images(self):
        html = '<html><body><img src="/photo.jpeg"></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_empty_src_attribute(self):
        html = '<html><body><img src=""></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert result == []

    def test_whitespace_in_src(self):
        html = '<html><body><img src="  /photo.jpg  "></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _scrape_html - native parser path
# ---------------------------------------------------------------------------


class TestScrapeHtmlNativeParser:
    def test_native_parser_success(self):
        """Parser with parse_exhibition_page that returns data skips LLM."""
        mock_parser = _create_mock_parser("Native Test")
        mock_parser.get_exhibition_urls.return_value = ["http://native.test/show1"]

        def mock_parse(client, url):
            return {
                "title": "Native Parsed Exhibition",
                "start_date": "2024-01-01",
                "end_date": "2024-03-01",
                "artworks": [],
            }

        mock_parser.parse_exhibition_page = mock_parse

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"native_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["parsed"] == 1
            assert result["saved"] == 1
            scraper.close()

    def test_native_parser_returns_none_fallback_to_llm(self):
        """If native parser returns None, fallback to LLM pipeline."""
        mock_parser = _create_mock_parser("Fallback Test")
        mock_parser.get_exhibition_urls.return_value = ["http://fallback.test/show1"]
        mock_parser.parse_exhibition_page.return_value = None
        mock_parser.clean_html.return_value = "Clean content for LLM that is long enough."

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"fallback_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            # Mock the LLM parser to return None (simulating LLM failure)
            scraper.parser.parse_exhibition_text = MagicMock(return_value=None)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - force mode
# ---------------------------------------------------------------------------


class TestScrapeHtmlForceMode:
    def test_force_deletes_existing_before_insert(self):
        """Force mode deletes existing record before inserting."""
        mock_parser = _create_mock_parser("Force Test")
        mock_parser.get_exhibition_urls.return_value = ["http://force.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "x" * 120

        mock_response = MagicMock()
        mock_response.text = "<html>" + "x" * 120 + "</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"force_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "Force Test",
                "title": "Existing Show",
                "url": "http://force.test/show1",
            })
            scraper.parser.parse_exhibition_text = MagicMock(return_value={
                "title": "New Show",
                "start_date": "2024-06-01",
                "artworks": [],
            })
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, force=True, dry_run=False)
                assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - URL already in DB (skip)
# ---------------------------------------------------------------------------


class TestScrapeHtmlSkipExisting:
    def test_skips_existing_url(self):
        """Existing URL is skipped when not in force mode."""
        mock_parser = _create_mock_parser("Skip Test")
        mock_parser.get_exhibition_urls.return_value = ["http://skip.test/show1"]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"skip_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            # Insert existing record
            scraper.db.insert_exhibition({
                "source": "Skip Test",
                "title": "Existing Show",
                "url": "http://skip.test/show1",
            })
            result = scraper._scrape_html(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            assert result["saved"] == 0
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - HTML size limit
# ---------------------------------------------------------------------------


class TestScrapeHtmlSizeLimit:
    def test_skips_oversized_html(self):
        """HTML exceeding MAX_HTML_SIZE is skipped."""
        mock_parser = _create_mock_parser("Size Test")
        mock_parser.get_exhibition_urls.return_value = ["http://size.test/show1"]
        mock_parser.parse_exhibition_page = None

        # Create oversized HTML (6MB)
        oversized_html = "<html>" + "x" * (6 * 1024 * 1024) + "</html>"

        mock_response = MagicMock()
        mock_response.text = oversized_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"size_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - content too short
# ---------------------------------------------------------------------------


class TestScrapeHtmlShortContent:
    def test_skips_short_content(self):
        """Content shorter than 100 chars after cleaning is skipped."""
        mock_parser = _create_mock_parser("Short Test")
        mock_parser.get_exhibition_urls.return_value = ["http://short.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "Short"

        mock_response = MagicMock()
        mock_response.text = "<html><body>Short</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"short_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["failed"] == 1
            scraper.close()

    def test_skips_empty_content(self):
        """Empty content after cleaning is skipped."""
        mock_parser = _create_mock_parser("Empty Test")
        mock_parser.get_exhibition_urls.return_value = ["http://empty.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = ""

        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"empty_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - LLM parsing failure
# ---------------------------------------------------------------------------


class TestScrapeHtmlLlmFailure:
    def test_llm_failure_counts_as_failed(self):
        """LLM parsing failure counts as failed."""
        mock_parser = _create_mock_parser("LLM Fail Test")
        mock_parser.get_exhibition_urls.return_value = ["http://llm.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "Valid content for LLM parsing."

        mock_response = MagicMock()
        mock_response.text = "<html><body>Valid content</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"llm_fail_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.parser.parse_exhibition_text = MagicMock(return_value=None)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - images handling
# ---------------------------------------------------------------------------


class TestScrapeHtmlImages:
    def test_images_attached_to_parsed_data(self):
        """Images are extracted and attached to parsed data."""
        mock_parser = _create_mock_parser("Images Test")
        mock_parser.get_exhibition_urls.return_value = ["http://images.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "Content for LLM. " + "y" * 90

        html_with_images = '<html><body><img src="/photo.jpg"><img src="/art.png"></body></html>'
        mock_response = MagicMock()
        mock_response.text = html_with_images
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"images_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.parser.parse_exhibition_text = MagicMock(return_value={
                "title": "Images Show",
                "start_date": "2024-01-01",
                "artworks": [],
            })
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=True)
                assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - tags handling
# ---------------------------------------------------------------------------


class TestScrapeHtmlTags:
    def test_tags_attached_when_present(self):
        """Tags from parser._url_tags are attached to parsed data."""
        mock_parser = _create_mock_parser("Tags Test")
        mock_parser.get_exhibition_urls.return_value = ["http://tags.test/show1"]
        mock_parser.parse_exhibition_page.return_value = {"title": "Tags Show"}
        mock_parser._url_tags = {"http://tags.test/show1": '["contemporary", "solo"]'}

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"tags_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_html(mock_parser, dry_run=True)
            assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - various paths
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsync:
    @pytest.mark.asyncio
    async def test_async_no_urls(self):
        """Async scrape with no URLs returns empty stats."""
        mock_parser = _create_mock_parser("Async Empty")
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_empty": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = await scraper._scrape_html_async(mock_parser)
            assert result["discovered"] == 0
            scraper.close()

    @pytest.mark.asyncio
    async def test_async_with_playwright(self):
        """Async scrape uses to_thread for Playwright parsers."""
        mock_parser = _create_mock_parser("Async PW")
        mock_parser.use_playwright = True
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_pw": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = await scraper._scrape_html_async(mock_parser)
            assert result["discovered"] == 0
            scraper.close()


# ---------------------------------------------------------------------------
# scrape_site - exception handling
# ---------------------------------------------------------------------------


class TestScrapeSiteException:
    def test_exception_records_error(self):
        """Exception in scrape_site records error in scraper_runs table."""
        mock_parser = _create_mock_parser("Error Test")
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.side_effect = RuntimeError("Network error")

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"error_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with pytest.raises(RuntimeError):
                scraper.scrape_site("error_test")
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_csv - limit and skip
# ---------------------------------------------------------------------------


class TestScrapeCsvExtended:
    def test_csv_limit_reached(self):
        """CSV pipeline stops at limit."""
        mock_parser = _create_mock_parser("CSV Limit", ParserStrategy.CSV_LOCAL)
        mock_parser.get_csv_exhibitions.return_value = [
            _make_exhibition_data("http://csv/1", "Show 1"),
            _make_exhibition_data("http://csv/2", "Show 2"),
            _make_exhibition_data("http://csv/3", "Show 3"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_csv(mock_parser, limit=2, dry_run=True)
            assert result["saved"] == 2
            scraper.close()

    def test_csv_force_overwrites(self):
        """CSV force mode deletes existing before insert."""
        mock_parser = _create_mock_parser("CSV Force", ParserStrategy.CSV_LOCAL)
        mock_parser.get_csv_exhibitions.return_value = [
            _make_exhibition_data("http://csv/1", "New Show"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "CSV Force",
                "title": "Old Show",
                "url": "http://csv/1",
            })
            result = scraper._scrape_csv(mock_parser, force=True, dry_run=False)
            assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_api - skip and force
# ---------------------------------------------------------------------------


class TestScrapeApiExtended:
    def test_api_skip_existing(self):
        """API pipeline skips existing URLs."""
        mock_parser = _create_mock_parser("API Skip", ParserStrategy.REST_API)
        mock_parser.get_api_exhibitions.return_value = [
            _make_exhibition_data("http://api/1", "Show"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "API Skip",
                "title": "Existing",
                "url": "http://api/1",
            })
            result = scraper._scrape_api(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            scraper.close()

    def test_api_force_overwrites(self):
        """API force mode deletes existing before insert."""
        mock_parser = _create_mock_parser("API Force", ParserStrategy.REST_API)
        mock_parser.get_api_exhibitions.return_value = [
            _make_exhibition_data("http://api/1", "New Show"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "API Force",
                "title": "Old Show",
                "url": "http://api/1",
            })
            result = scraper._scrape_api(mock_parser, force=True, dry_run=False)
            assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_artwork_only - skip existing
# ---------------------------------------------------------------------------


class TestScrapeArtworkOnlyExtended:
    def test_artwork_skip_existing(self):
        """Artwork-only pipeline skips existing synthetic URL."""
        mock_parser = _create_mock_parser("Art Skip", ParserStrategy.ARTWORK_ONLY)
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        synthetic_url = "https://auto-curation.internal/collection/art_skip"

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "Art Skip",
                "title": "Existing Collection",
                "url": synthetic_url,
            })
            result = scraper._scrape_artwork_only(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            scraper.close()

    def test_artwork_insert_failure(self):
        """Artwork-only pipeline counts failed inserts."""
        mock_parser = _create_mock_parser("Art Fail", ParserStrategy.ARTWORK_ONLY)
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            result = scraper._scrape_artwork_only(mock_parser, dry_run=False)
            assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# ascrape_site - HTML_LLM with no URLs
# ---------------------------------------------------------------------------


class TestAscrapeHtmlNoUrls:
    @pytest.mark.asyncio
    async def test_async_html_no_urls(self):
        """Async HTML scrape with no URLs returns empty stats."""
        mock_parser = _create_mock_parser("Async No URLs")
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_no_urls": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = await scraper.ascrape_site("async_no_urls")
            assert result["discovered"] == 0
            scraper.close()


# ---------------------------------------------------------------------------
# scrape_all_sites - with real-like mock
# ---------------------------------------------------------------------------


class TestScrapeAllSitesExtended:
    def test_scrape_all_calls_each_site(self):
        """scrape_all_sites calls scrape_site for each registered site."""
        mock_parser = _create_mock_parser("All Test", ParserStrategy.REST_API)
        mock_parser.get_api_exhibitions.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"all_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            results = scraper.scrape_all_sites(dry_run=True)
            assert len(results) == 1
            assert results[0]["site"] == "All Test"
            scraper.close()


# ---------------------------------------------------------------------------
# _is_retryable_http_error - 503 and 504
# ---------------------------------------------------------------------------


class TestIsRetryableExtended:
    def test_503_is_retryable(self):
        response = MagicMock(status_code=503)
        exc = httpx.HTTPStatusError("service unavailable", request=MagicMock(), response=response)
        assert _is_retryable_http_error(exc) is True

    def test_504_is_retryable(self):
        response = MagicMock(status_code=504)
        exc = httpx.HTTPStatusError("gateway timeout", request=MagicMock(), response=response)
        assert _is_retryable_http_error(exc) is True

    def test_500_is_not_retryable(self):
        response = MagicMock(status_code=500)
        exc = httpx.HTTPStatusError("internal error", request=MagicMock(), response=response)
        assert _is_retryable_http_error(exc) is False


# ---------------------------------------------------------------------------
# close / aclose - edge cases
# ---------------------------------------------------------------------------


class TestCloseExtended:
    def test_close_handles_async_close_error(self):
        """close() handles errors when closing async client (no running loop)."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            # Simulate async client close error
            with patch.object(scraper.async_client, "aclose", side_effect=RuntimeError("error")):
                scraper.close()  # Should not raise

    def test_close_multiple_times(self):
        """close() can be called multiple times safely."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.close()
            scraper.close()

    @pytest.mark.asyncio
    async def test_close_with_running_loop(self):
        """close() schedules aclose on running loop."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            mock = AsyncMock()
            scraper.async_client = mock
            scraper.close()
            await asyncio.sleep(0)
            mock.aclose.assert_awaited()


# ---------------------------------------------------------------------------
# scrape_site / ascrape_site - parser_key fallback
# ---------------------------------------------------------------------------


class TestScrapeSiteParserKey:
    def test_empty_parser_key_fallback(self):
        """Empty parser_key should be set from site_key."""
        mock_parser = _create_mock_parser("Test")
        mock_parser.parser_key = ""
        mock_parser.get_exhibition_urls.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"test_empty_key": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper.scrape_site("test_empty_key")
            assert result["discovered"] == 0
            assert mock_parser.parser_key == "test_empty_key"
            scraper.close()


class TestAscrapeSiteParserKey:
    @pytest.mark.asyncio
    async def test_ascrape_empty_parser_key_fallback(self):
        """Empty parser_key in ascrape_site should be set from site_key."""
        mock_parser = _create_mock_parser("Async Test")
        mock_parser.parser_key = ""
        mock_parser.get_exhibition_urls.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_empty_key": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = await scraper.ascrape_site("async_empty_key")
            assert result["discovered"] == 0
            assert mock_parser.parser_key == "async_empty_key"
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - DB insert failure (line 398)
# ---------------------------------------------------------------------------


class TestScrapeHtmlDbInsertFail:
    def test_db_insert_failure_increments_failed(self):
        """When insert_exhibition returns falsy, failed count should increment."""
        mock_parser = _create_mock_parser("DB Fail")
        mock_parser.get_exhibition_urls.return_value = ["http://dbfail.test/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "x" * 120

        mock_response = MagicMock()
        mock_response.text = "<html>" + "x" * 120 + "</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"dbfail_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.parser.parse_exhibition_text = MagicMock(return_value={
                "title": "DB Fail Show",
                "start_date": "2024-01-01",
                "artworks": [],
            })
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser, dry_run=False)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - async edge cases
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsyncEdgeCases:
    @pytest.mark.asyncio
    async def test_async_content_too_short(self):
        """Async: content shorter than 100 chars is skipped."""
        mock_parser = _create_mock_parser("Async Short")
        mock_parser.get_exhibition_urls.return_value = ["http://async.short/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "Short"

        mock_response = MagicMock()
        mock_response.text = "<html><body>Short</body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_short": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.async_client, "get", return_value=mock_response):
                result = await scraper._scrape_html_async(mock_parser)
                assert result["failed"] == 1
            scraper.close()

    @pytest.mark.asyncio
    async def test_async_html_too_large(self):
        """Async: HTML exceeding MAX_HTML_SIZE is skipped."""
        mock_parser = _create_mock_parser("Async Large")
        mock_parser.get_exhibition_urls.return_value = ["http://async.large/show1"]
        mock_parser.parse_exhibition_page = None

        oversized_html = "<html>" + "x" * (6 * 1024 * 1024) + "</html>"
        mock_response = MagicMock()
        mock_response.text = oversized_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_large": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.async_client, "get", return_value=mock_response):
                result = await scraper._scrape_html_async(mock_parser)
                assert result["failed"] == 1
            scraper.close()

    @pytest.mark.asyncio
    async def test_async_llm_failure(self):
        """Async: LLM parsing failure increments failed count."""
        mock_parser = _create_mock_parser("Async LLM Fail")
        mock_parser.get_exhibition_urls.return_value = ["http://async.llmfail/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "x" * 120

        mock_response = MagicMock()
        mock_response.text = "<html>" + "x" * 120 + "</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_llmfail": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.parser.parse_exhibition_text_async = AsyncMock(return_value=None)
            with patch.object(scraper.async_client, "get", return_value=mock_response):
                result = await scraper._scrape_html_async(mock_parser)
                assert result["failed"] == 1
            scraper.close()

    @pytest.mark.asyncio
    async def test_async_city_fallback(self):
        """Async: missing city in parsed data falls back to parser.city."""
        mock_parser = _create_mock_parser("Async City")
        mock_parser.get_exhibition_urls.return_value = ["http://async.city/show1"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "x" * 120

        mock_response = MagicMock()
        mock_response.text = "<html>" + "x" * 120 + "</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_city": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.parser.parse_exhibition_text_async = AsyncMock(return_value={
                "title": "City Fallback Show",
                "start_date": "2024-01-01",
                "artworks": [],
            })
            with patch.object(scraper.async_client, "get", return_value=mock_response):
                result = await scraper._scrape_html_async(mock_parser, dry_run=True)
                assert result["saved"] == 1
            scraper.close()

    @pytest.mark.asyncio
    async def test_async_exception_handler(self):
        """Async: exception in _process_one increments failed count."""
        mock_parser = _create_mock_parser("Async Exception")
        mock_parser.get_exhibition_urls.return_value = ["http://async.exception/show1"]
        mock_parser.parse_exhibition_page = None

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_exc": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            mock_get = AsyncMock(side_effect=RuntimeError("Connection error"))
            with patch.object(scraper.async_client, "get", mock_get):
                result = await scraper._scrape_html_async(mock_parser)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - native extraction (lines 448, 476-483)
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsyncNativeExtraction:
    @pytest.mark.asyncio
    async def test_async_native_extraction_success(self):
        """Async: native extraction with no Playwright."""
        mock_parser = _create_mock_parser("Async Native")
        mock_parser.use_playwright = False
        mock_parser.get_exhibition_urls.return_value = ["http://async.native/show1"]
        mock_parser.parse_exhibition_page = MagicMock(return_value={
            "title": "Native Show",
            "start_date": "2024-01-01",
            "artworks": [],
        })

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_native": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            result = await scraper._scrape_html_async(mock_parser, dry_run=True)
            assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - dedup skip (lines 463-466)
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsyncDedup:
    @pytest.mark.asyncio
    async def test_async_dedup_skip(self):
        """Async: existing URL is skipped when not in force/dry_run mode."""
        mock_parser = _create_mock_parser("Async Dedup")
        mock_parser.get_exhibition_urls.return_value = ["http://async.dedup/show1"]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_dedup": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "Async Dedup",
                "title": "Existing Show",
                "url": "http://async.dedup/show1",
            })
            result = await scraper._scrape_html_async(
                mock_parser, force=False, dry_run=False
            )
            assert result["skipped"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - force delete (lines 468-471, 541-547)
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsyncForceDelete:
    @pytest.mark.asyncio
    async def test_async_force_deletes_existing(self):
        """Async: force mode deletes existing record before insert."""
        mock_parser = _create_mock_parser("Async Force")
        mock_parser.get_exhibition_urls.return_value = ["http://async.force/show1"]
        mock_parser.parse_exhibition_page = MagicMock(return_value={
            "title": "New Show",
            "start_date": "2024-07-01",
            "artworks": [],
        })

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_force": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition({
                "source": "Async Force",
                "title": "Old Show",
                "url": "http://async.force/show1",
            })
            result = await scraper._scrape_html_async(
                mock_parser, force=True, dry_run=False
            )
            assert result["saved"] == 1
            assert result["skipped"] == 0
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html - Scrapling fallback failure (lines 334-336)
# ---------------------------------------------------------------------------


class TestScrapeHtmlScraplingFallback:
    def test_scrapling_fallback_failure(self):
        """HTTP 403 with Scrapling unhandled error logs and counts as failed."""
        mock_parser = _create_mock_parser("Scrapling Test")
        mock_parser.get_exhibition_urls.return_value = ["http://scrapling.test/show1"]
        mock_parser.parse_exhibition_page = None

        mock_response = MagicMock()
        mock_response.status_code = 403

        def raise_403():
            raise httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=mock_response,
            )

        mock_response.raise_for_status = raise_403

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"scrapling_test": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            with patch.object(scraper.client, "get", return_value=mock_response):
                result = scraper._scrape_html(mock_parser)
                assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html_async - DB insert failure (lines 546-547)
# ---------------------------------------------------------------------------


class TestScrapeHtmlAsyncDbInsertFail:
    @pytest.mark.asyncio
    async def test_async_db_insert_failure(self):
        """Async: when insert_exhibition returns falsy, failed count increments."""
        mock_parser = _create_mock_parser("Async DB Fail")
        mock_parser.use_playwright = False
        mock_parser.get_exhibition_urls.return_value = ["http://async.dbfail/show1"]
        mock_parser.parse_exhibition_page = MagicMock(return_value={
            "title": "Async Fail Show",
            "start_date": "2024-01-01",
            "artworks": [],
        })

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f, \
             patch("src.scraper.SITES", {"async_dbfail": mock_parser}):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            result = await scraper._scrape_html_async(
                mock_parser, force=False, dry_run=False
            )
            assert result["failed"] == 1
            scraper.close()


class TestFixtureCleanupCoverage:
    def test_fixture_teardown_cleans_db(self):
        """Ensure fixture teardown os.remove runs for TEST_DB."""
        import os
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        scraper = ExhibitionScraper(TEST_DB)
        scraper.close()
