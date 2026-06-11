"""Comprehensive tests for src/scraper.py — ExhibitionScraper class."""

import os
from unittest.mock import patch

import httpx
import pytest

from src.scraper import (
    ExhibitionScraper,
    _is_retryable_http_error,
    extract_images_from_html,
)

TEST_DB = "tests/test_scraper.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# ---------------------------------------------------------------------------
# extract_images_from_html
# ---------------------------------------------------------------------------


class TestExtractImages:
    def test_extracts_jpg_images(self):
        html = '<html><body><img src="/images/photo.jpg" /></body></html>'
        result = extract_images_from_html(html, "http://example.com")
        assert len(result) == 1
        assert "photo.jpg" in result[0]

    def test_filters_logos(self):
        html = '<html><body><img src="/logo.png" /><img src="/photo.jpg" /></body></html>'
        result = extract_images_from_html(html, "http://example.com")
        assert len(result) == 1
        assert "photo.jpg" in result[0]

    def test_filters_icons(self):
        html = '<html><body><img src="/icon.svg" /><img src="/exhibit.webp" /></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1
        assert "exhibit.webp" in result[0]

    def test_deduplicates(self):
        html = '<html><body><img src="/a.jpg" /><img src="/a.jpg" /></body></html>'
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) == 1

    def test_respects_max_images(self):
        html = "<html><body>"
        for i in range(20):
            html += f'<img src="/img{i}.jpg" />'
        html += "</body></html>"
        result = extract_images_from_html(html, "http://ex.com")
        assert len(result) <= 8

    def test_handles_exception(self):
        # Invalid HTML should not crash
        result = extract_images_from_html(None, "http://ex.com")  # type: ignore
        assert result == []

    def test_resolves_relative_urls(self):
        html = '<html><body><img src="photo.jpg" /></body></html>'
        result = extract_images_from_html(html, "http://ex.com/sub/")
        assert "http://ex.com/sub/photo.jpg" in result[0]


# ---------------------------------------------------------------------------
# _is_retryable_http_error
# ---------------------------------------------------------------------------


class TestIsRetryableHttpError:
    def test_connect_error_is_retryable(self):
        assert _is_retryable_http_error(httpx.ConnectError("refused")) is True

    def test_timeout_is_retryable(self):
        assert _is_retryable_http_error(httpx.TimeoutException("timeout")) is True

    def test_429_is_retryable(self):
        try:
            resp = httpx.Response(429)
            resp._request = httpx.Request("GET", "http://ex.com")
            raise httpx.HTTPStatusError("too many", request=resp._request, response=resp)
        except httpx.HTTPStatusError as e:
            assert _is_retryable_http_error(e) is True

    def test_502_is_retryable(self):
        try:
            resp = httpx.Response(502)
            resp._request = httpx.Request("GET", "http://ex.com")
            raise httpx.HTTPStatusError("bad gateway", request=resp._request, response=resp)
        except httpx.HTTPStatusError as e:
            assert _is_retryable_http_error(e) is True

    def test_404_is_not_retryable(self):
        try:
            resp = httpx.Response(404)
            resp._request = httpx.Request("GET", "http://ex.com")
            raise httpx.HTTPStatusError("not found", request=resp._request, response=resp)
        except httpx.HTTPStatusError as e:
            assert _is_retryable_http_error(e) is False

    def test_value_error_is_not_retryable(self):
        assert _is_retryable_http_error(ValueError("nope")) is False


# ---------------------------------------------------------------------------
# ExhibitionScraper initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_initializes_clients(self):
        scraper = ExhibitionScraper(TEST_DB)
        assert scraper.db is not None
        assert scraper.parser is not None
        assert scraper.client is not None
        assert scraper.async_client is not None
        assert scraper.max_concurrency == 10

    def test_custom_concurrency(self):
        scraper = ExhibitionScraper(TEST_DB, max_concurrency=5)
        assert scraper.max_concurrency == 5

    def test_stat_handlers_defined(self):
        from src.sites.base import ParserStrategy

        scraper = ExhibitionScraper(TEST_DB)
        assert ParserStrategy.HTML_LLM in scraper.STRATEGY_HANDLERS
        assert ParserStrategy.CSV_LOCAL in scraper.STRATEGY_HANDLERS
        assert ParserStrategy.CSV_REMOTE in scraper.STRATEGY_HANDLERS
        assert ParserStrategy.REST_API in scraper.STRATEGY_HANDLERS
        assert ParserStrategy.SPARQL in scraper.STRATEGY_HANDLERS
        assert ParserStrategy.ARTWORK_ONLY in scraper.STRATEGY_HANDLERS


# ---------------------------------------------------------------------------
# scrape_site — error/edge cases
# ---------------------------------------------------------------------------


class TestScrapeSite:
    def test_unknown_site_key(self):
        scraper = ExhibitionScraper(TEST_DB)
        result = scraper.scrape_site("nonexistent")
        assert "error" in result

    def test_returns_stats(self):
        """scrape_site returns a dict with expected keys."""
        scraper = ExhibitionScraper(TEST_DB)
        # Use the first available site that has no network requirements
        site_key = "hirshhorn"  # hirshhorn returns empty without API calls
        result = scraper.scrape_site(site_key, dry_run=True)
        assert isinstance(result, dict)
        assert "site" in result
        assert "discovered" in result


# ---------------------------------------------------------------------------
# _scrape_html — edge cases
# ---------------------------------------------------------------------------


class TestScrapeHtml:
    def test_no_urls_discovered(self):
        from src.sites.base import BaseSiteParser

        class EmptyParser(BaseSiteParser):
            source = "Empty"
            city = "Nowhere"
            parser_key = "empty_test"
            list_url = "http://ex.com"
            link_patterns = []

            def get_exhibition_urls(self, client, since_year=None):
                return []

        scraper = ExhibitionScraper(TEST_DB)
        # Access the private handler directly
        result = scraper._scrape_html(EmptyParser(), dry_run=True)
        assert result["discovered"] == 0
        assert result["parsed"] == 0

    def test_site_not_registered(self):
        scraper = ExhibitionScraper(TEST_DB)
        result = scraper.scrape_site("__nonexistent__")
        assert "error" in result


# ---------------------------------------------------------------------------
# _scrape_csv
# ---------------------------------------------------------------------------


class TestScrapeCsv:
    def test_csv_pipeline_empty(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class CsvParser(BaseSiteParser):
            source = "CSV Test"
            city = "Test"
            parser_key = "csv_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.CSV_LOCAL

            def get_csv_exhibitions(self, since_year=None):
                return []

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_csv(CsvParser(), dry_run=True)
        assert result["discovered"] == 0
        assert result["parsed"] == 0

    def test_csv_pipeline_with_data(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class CsvParser(BaseSiteParser):
            source = "CSV Test"
            city = "Test"
            parser_key = "csv_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.CSV_LOCAL

            def get_csv_exhibitions(self, since_year=None):
                return [
                    {
                        "url": "http://csv.test/1",
                        "title": "CSV Exhibition",
                        "start_date": "2024-01-01",
                        "artworks": [],
                    }
                ]

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_csv(CsvParser(), dry_run=True)
        assert result["discovered"] == 1
        assert result["saved"] == 1


# ---------------------------------------------------------------------------
# _scrape_api
# ---------------------------------------------------------------------------


class TestScrapeApi:
    def test_api_pipeline_empty(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class ApiParser(BaseSiteParser):
            source = "API Test"
            city = "Test"
            parser_key = "api_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.REST_API

            def get_api_exhibitions(self, since_year=None, limit=None):
                return []

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_api(ApiParser(), dry_run=True)
        assert result["discovered"] == 0
        assert result["parsed"] == 0

    def test_api_pipeline_with_data(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class ApiParser(BaseSiteParser):
            source = "API Test"
            city = "Test"
            parser_key = "api_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.REST_API

            def get_api_exhibitions(self, since_year=None, limit=None):
                return [
                    {
                        "url": "http://api.test/1",
                        "title": "API Exhibition",
                        "start_date": "2024-06-01",
                        "artworks": [],
                    }
                ]

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_api(ApiParser(), dry_run=True)
        assert result["discovered"] == 1
        assert result["saved"] == 1


# ---------------------------------------------------------------------------
# _scrape_artwork_only
# ---------------------------------------------------------------------------


class TestScrapeArtworkOnly:
    def test_artwork_only_empty(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class ArtworkParser(BaseSiteParser):
            source = "Art Only"
            city = "Test"
            parser_key = "art_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.ARTWORK_ONLY

            def get_csv_artworks(self, since_year=None, limit=None):
                return []

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_artwork_only(ArtworkParser(), dry_run=True)
        assert result["discovered"] == 0

    def test_artwork_only_with_data(self):
        from src.sites.base import BaseSiteParser, ParserStrategy

        class ArtworkParser(BaseSiteParser):
            source = "Art Only"
            city = "Test"
            parser_key = "art_test"
            list_url = "http://ex.com"
            strategy = ParserStrategy.ARTWORK_ONLY

            def get_csv_artworks(self, since_year=None, limit=None):
                return [
                    {"artist_name": "A", "work_title": "W1", "caption": "Caption"},
                    {"artist_name": "B", "work_title": "W2", "caption": "Caption2"},
                ]

        scraper = ExhibitionScraper(TEST_DB)
        result = scraper._scrape_artwork_only(ArtworkParser(), dry_run=True)
        assert result["discovered"] == 2
        assert result["saved"] == 1  # one synthetic record


# ---------------------------------------------------------------------------
# scrape_all_sites
# ---------------------------------------------------------------------------


class TestScrapeAllSites:
    def test_scrape_all_returns_list(self):
        scraper = ExhibitionScraper(TEST_DB)
        # Mock scrape_site to avoid real network calls
        with patch.object(scraper, "scrape_site", return_value={"site": "test", "discovered": 0}):
            results = scraper.scrape_all_sites(dry_run=True)
            assert isinstance(results, list)
            from src.sites import SITES

            assert len(results) == len(SITES)


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    def test_close_sync(self):
        scraper = ExhibitionScraper(TEST_DB)
        scraper.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_aclose(self):
        scraper = ExhibitionScraper(TEST_DB)
        await scraper.aclose()  # Should not raise
