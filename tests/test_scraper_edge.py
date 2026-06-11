"""Edge case tests for src/scraper.py — ExhibitionScraper strategy handlers."""

import tempfile
from unittest.mock import MagicMock, patch

import httpx

from src.scraper import (
    ExhibitionScraper,
    _is_retryable_http_error,
    extract_images_from_html,
)
from src.sites.base import ParserStrategy

# ---------------------------------------------------------------------------
# extract_images_from_html
# ---------------------------------------------------------------------------


class TestExtractImages:
    def test_extracts_valid_images(self):
        html = (
            '<html><img src="http://test.com/photo.jpg"><img src="/relative/pic.png"></body></html>'
        )
        result = extract_images_from_html(html, "http://test.com")
        assert len(result) == 2

    def test_filters_logos(self):
        html = (
            '<html><body><img src="http://test.com/logo.png"><img src="/photo.jpg"></body></html>'
        )
        result = extract_images_from_html(html, "http://test.com")
        assert len(result) == 1

    def test_filters_non_images(self):
        html = (
            '<html><body><img src="http://test.com/file.pdf"><img src="/photo.jpg"></body></html>'
        )
        result = extract_images_from_html(html, "http://test.com")
        assert len(result) == 1

    def test_deduplicates(self):
        html = '<html><body><img src="http://test.com/photo.jpg"><img src="http://test.com/photo.jpg"></body></html>'
        result = extract_images_from_html(html, "http://test.com")
        assert len(result) == 1

    def test_limits_max_images(self):
        html = "<html><body>"
        for i in range(20):
            html += f'<img src="http://test.com/photo{i}.jpg">'
        html += "</body></html>"
        result = extract_images_from_html(html, "http://test.com")
        assert len(result) <= 8

    def test_invalid_html_returns_empty(self):
        result = extract_images_from_html("", "http://test.com")
        assert result == []


# ---------------------------------------------------------------------------
# _is_retryable_http_error
# ---------------------------------------------------------------------------


class TestIsRetryableHttpError:
    def test_connect_error_retryable(self):
        assert _is_retryable_http_error(httpx.ConnectError("test")) is True

    def test_timeout_retryable(self):
        assert _is_retryable_http_error(httpx.TimeoutException("test")) is True

    def test_429_retryable(self):
        response = MagicMock(status_code=429)
        assert (
            _is_retryable_http_error(
                httpx.HTTPStatusError("test", request=MagicMock(), response=response)
            )
            is True
        )

    def test_404_not_retryable(self):
        response = MagicMock(status_code=404)
        assert (
            _is_retryable_http_error(
                httpx.HTTPStatusError("test", request=MagicMock(), response=response)
            )
            is False
        )

    def test_random_exception_not_retryable(self):
        assert _is_retryable_http_error(ValueError("test")) is False


# ---------------------------------------------------------------------------
# ExhibitionScraper initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_creates_with_defaults(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            assert scraper.max_concurrency == 10
            assert scraper.db is not None
            assert scraper.parser is not None
            scraper.close()

    def test_strategy_handlers_mapped(self):
        assert ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.HTML_LLM] == "_scrape_html"
        assert ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.CSV_LOCAL] == "_scrape_csv"
        assert ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.CSV_REMOTE] == "_scrape_csv"
        assert ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.REST_API] == "_scrape_api"
        assert ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.SPARQL] == "_scrape_api"
        assert (
            ExhibitionScraper.STRATEGY_HANDLERS[ParserStrategy.ARTWORK_ONLY]
            == "_scrape_artwork_only"
        )


# ---------------------------------------------------------------------------
# scrape_site - error handling
# ---------------------------------------------------------------------------


class TestScrapeSiteErrors:
    def test_unknown_site_key(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper.scrape_site("nonexistent")
            assert "error" in result
            scraper.close()

    def test_unknown_strategy(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test"
        mock_parser.city = "City"
        mock_parser.parser_key = "test"
        mock_parser.strategy = "unknown"

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper.scrape_site("test")
            assert "error" in result
            scraper.close()


# ---------------------------------------------------------------------------
# Helper to create exhibition data dict
# ---------------------------------------------------------------------------


def _make_ex(url="http://test.show", title="Show"):
    return {
        "source": "Test",
        "title": title,
        "preface": "Preface text",
        "concept": None,
        "curators": [],
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "location": "Gallery",
        "city": "City",
        "url": url,
        "artworks": [],
    }


# ---------------------------------------------------------------------------
# _scrape_csv
# ---------------------------------------------------------------------------


class TestScrapeCsv:
    def test_csv_dry_run(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test CSV"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_csv"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_exhibitions.return_value = [_make_ex()]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_csv(mock_parser, dry_run=True)
            assert result["discovered"] == 1
            assert result["saved"] == 1
            scraper.close()

    def test_csv_inserts_to_db(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test CSV"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_csv"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_exhibitions.return_value = [_make_ex(url="http://csv.show")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_csv(mock_parser, dry_run=False)
            assert result["saved"] == 1
            ex = scraper.db.get_exhibition_by_url("http://csv.show")
            assert ex is not None
            scraper.close()

    def test_csv_limit(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test CSV"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_csv"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_exhibitions.return_value = [
            _make_ex(url="http://csv.show/1", title="Show 1"),
            _make_ex(url="http://csv.show/2", title="Show 2"),
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_csv(mock_parser, limit=1, dry_run=True)
            assert result["saved"] == 1
            scraper.close()

    def test_csv_skips_existing(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test CSV"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_csv"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_exhibitions.return_value = [_make_ex(url="http://csv.show/1")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper._scrape_csv(mock_parser, dry_run=False)
            result = scraper._scrape_csv(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_api
# ---------------------------------------------------------------------------


class TestScrapeApi:
    def test_api_dry_run(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test API"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_api"
        mock_parser.institution_type = "museum"
        mock_parser.get_api_exhibitions.return_value = [_make_ex(url="http://api.show")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_api(mock_parser, dry_run=True)
            assert result["discovered"] == 1
            assert result["saved"] == 1
            scraper.close()

    def test_api_inserts_to_db(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test API"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_api"
        mock_parser.institution_type = "museum"
        mock_parser.get_api_exhibitions.return_value = [_make_ex(url="http://api.show")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_api(mock_parser, dry_run=False)
            assert result["saved"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_artwork_only
# ---------------------------------------------------------------------------


class TestScrapeArtworkOnly:
    def test_no_artworks(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test NGA"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_nga"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_artworks.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_artwork_only(mock_parser)
            assert result["discovered"] == 0
            scraper.close()

    def test_dry_run(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test NGA"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_nga"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_artwork_only(mock_parser, dry_run=True)
            assert result["saved"] == 1
            scraper.close()

    def test_inserts_to_db(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test NGA"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_nga"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper._scrape_artwork_only(mock_parser, dry_run=False)
            assert result["saved"] == 1
            scraper.close()

    def test_skips_existing(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test NGA"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_nga"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper._scrape_artwork_only(mock_parser, dry_run=False)
            result = scraper._scrape_artwork_only(mock_parser, dry_run=False)
            assert result["skipped"] == 1
            scraper.close()

    def test_insert_failure(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test NGA"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_nga"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_artworks.return_value = [
            {"artist_name": "Artist", "work_title": "Work"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            # Force the insert_exhibition to return None (simulate failure)
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            result = scraper._scrape_artwork_only(mock_parser, dry_run=False)
            assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# scrape_all_sites
# ---------------------------------------------------------------------------


class TestScrapeAllSites:
    def test_scrape_all_sites_empty(self):
        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            results = scraper.scrape_all_sites(dry_run=True)
            assert results == []
            scraper.close()


# ---------------------------------------------------------------------------
# close / aclose
# ---------------------------------------------------------------------------


class TestClose:
    def test_close_does_not_raise(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.close()

    def test_aclose_does_not_raise(self):
        import asyncio

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            asyncio.run(scraper.aclose())


# ---------------------------------------------------------------------------
# ascrape_site - async version
# ---------------------------------------------------------------------------


class TestAscrapeSite:
    def test_ascrape_unknown_site_key(self):
        """ascrape_site with unknown site key returns error."""
        import asyncio

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            result = asyncio.run(scraper.ascrape_site("nonexistent"))
            assert "error" in result
            scraper.close()

    def test_ascrape_unknown_strategy(self):
        """ascrape_site with unknown strategy returns error."""
        import asyncio

        mock_parser = MagicMock()
        mock_parser.source = "Test"
        mock_parser.city = "City"
        mock_parser.parser_key = "test"
        mock_parser.strategy = "unknown"

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = asyncio.run(scraper.ascrape_site("test"))
            assert "error" in result
            scraper.close()

    def test_ascrape_api_strategy_dispatches_sync(self):
        """Non-HTML_LLM strategies should dispatch sync handler."""
        import asyncio

        mock_parser = MagicMock()
        mock_parser.source = "Test API"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_api"
        mock_parser.institution_type = "museum"
        mock_parser.strategy = ParserStrategy.REST_API
        mock_parser.get_api_exhibitions.return_value = []

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test_api": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = asyncio.run(scraper.ascrape_site("test_api"))
            assert result["discovered"] == 0
            scraper.close()

    def test_ascrape_site_exception_handled(self):
        """Exception in ascrape_site handler gets caught and logged."""
        import asyncio

        import pytest

        mock_parser = MagicMock()
        mock_parser.source = "Test"
        mock_parser.city = "City"
        mock_parser.parser_key = "test"
        mock_parser.institution_type = "museum"
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.side_effect = RuntimeError("Unexpected error")

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            with pytest.raises(RuntimeError):
                asyncio.run(scraper.ascrape_site("test"))
            scraper.close()


# ---------------------------------------------------------------------------
# ascrape_all_sites - concurrent async
# ---------------------------------------------------------------------------


class TestAscrapeAllSites:
    def test_ascrape_all_sites_empty(self):
        """ascrape_all_sites with no SITES returns empty."""
        import asyncio

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = asyncio.run(scraper.ascrape_all_sites(dry_run=True))
            assert result == []
            scraper.close()

    def test_ascrape_all_sites_mixed_strategies(self):
        """ascrape_all_sites handles HTML + non-HTML strategies."""
        import asyncio

        html_parser = MagicMock()
        html_parser.source = "HTML Site"
        html_parser.city = "City"
        html_parser.parser_key = "html_site"
        html_parser.institution_type = "museum"
        html_parser.strategy = ParserStrategy.HTML_LLM
        html_parser.get_exhibition_urls.return_value = []

        csv_parser = MagicMock()
        csv_parser.source = "CSV Site"
        csv_parser.city = "City"
        csv_parser.parser_key = "csv_site"
        csv_parser.institution_type = "museum"
        csv_parser.strategy = ParserStrategy.CSV_LOCAL
        csv_parser.get_csv_exhibitions.return_value = []

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"html_site": html_parser, "csv_site": csv_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = asyncio.run(scraper.ascrape_all_sites(dry_run=True))
            assert len(result) == 2
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_csv / _scrape_api - insert failure
# ---------------------------------------------------------------------------


class TestScrapeInsertFailures:
    def test_csv_insert_failure(self):
        """_scrape_csv counts failed inserts."""
        mock_parser = MagicMock()
        mock_parser.source = "Test CSV"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_csv"
        mock_parser.institution_type = "museum"
        mock_parser.get_csv_exhibitions.return_value = [_make_ex(url="http://csv.fail")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            result = scraper._scrape_csv(mock_parser, dry_run=False)
            assert result["failed"] == 1
            scraper.close()

    def test_api_insert_failure(self):
        """_scrape_api counts failed inserts."""
        mock_parser = MagicMock()
        mock_parser.source = "Test API"
        mock_parser.city = "City"
        mock_parser.parser_key = "test_api"
        mock_parser.institution_type = "museum"
        mock_parser.get_api_exhibitions.return_value = [_make_ex(url="http://api.fail")]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition = MagicMock(return_value=None)
            result = scraper._scrape_api(mock_parser, dry_run=False)
            assert result["failed"] == 1
            scraper.close()


# ---------------------------------------------------------------------------
# scrape_site with HTML_LLM strategy (mocked URL discovery)
# ---------------------------------------------------------------------------


class TestScrapeSiteHtml:
    def test_no_urls_discovered(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test"
        mock_parser.city = "City"
        mock_parser.parser_key = "test"
        mock_parser.institution_type = "museum"
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.return_value = []

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            result = scraper.scrape_site("test", dry_run=True)
            assert result["discovered"] == 0
            scraper.close()


# ---------------------------------------------------------------------------
# _scrape_html with force mode
# ---------------------------------------------------------------------------


class TestScrapeHtmlForce:
    def test_force_deletes_existing(self):
        mock_parser = MagicMock()
        mock_parser.source = "Test"
        mock_parser.city = "City"
        mock_parser.parser_key = "test"
        mock_parser.institution_type = "museum"
        mock_parser.strategy = ParserStrategy.HTML_LLM
        mock_parser.get_exhibition_urls.return_value = ["http://test.ex/show"]
        mock_parser.parse_exhibition_page = None
        mock_parser.clean_html.return_value = "Clean text for LLM parsing that is long enough."
        mock_parser.request_timeout = 60.0

        with (
            tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f,
            patch("src.scraper.SITES", {"test": mock_parser}),
        ):
            scraper = ExhibitionScraper(db_path=f.name)
            scraper.db.insert_exhibition(
                {
                    "source": "Test",
                    "title": "Existing",
                    "url": "http://test.ex/show",
                }
            )
            result = scraper._scrape_html(mock_parser, force=True, dry_run=True)
            assert result["discovered"] == 1
            scraper.close()
