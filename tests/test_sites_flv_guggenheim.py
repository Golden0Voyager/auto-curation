"""Tests for src/sites/flv.py and guggenheim.py with mocked Scrapling."""

from unittest.mock import MagicMock, patch

from src.sites.flv import FLVParser
from src.sites.guggenheim import GuggenheimParser


class TestFLVParser:
    def test_parser_attributes(self):
        p = FLVParser()
        assert p.source == "Fondation Louis Vuitton"
        assert p.city == "Paris"
        assert p.parser_key == "flv"
        assert p.status == "BLOCKED_SPA"

    def test_get_exhibition_urls_no_scrapling(self):
        p = FLVParser()
        with patch("src.sites.flv.HAS_SCRAPLING", False):
            result = p.get_exhibition_urls(None)
            assert result == []

    def test_get_exhibition_urls_scrapling_success(self):
        p = FLVParser()
        mock_fetcher = MagicMock()
        mock_page = MagicMock()
        mock_page.html_content = '<a href="/en/events/test-exhibition">Link</a>'
        mock_fetcher.fetch.return_value = mock_page

        with (
            patch("src.sites.flv.HAS_SCRAPLING", True),
            patch("src.sites.flv.StealthyFetcher", return_value=mock_fetcher, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert len(result) == 1
            assert "fondationlouisvuitton.fr/en/events/test-exhibition" in result[0]

    def test_get_exhibition_urls_scrapling_failure(self):
        p = FLVParser()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("Scrapling error")

        with (
            patch("src.sites.flv.HAS_SCRAPLING", True),
            patch("src.sites.flv.StealthyFetcher", return_value=mock_fetcher, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert result == []


class TestGuggenheimParser:
    def test_parser_attributes(self):
        p = GuggenheimParser()
        assert p.source == "Guggenheim Museum"
        assert p.city == "New York"
        assert p.parser_key == "guggenheim"
        assert p.status == "BLOCKED_CLOUDFLARE"

    def test_get_exhibition_urls_no_scrapling(self):
        p = GuggenheimParser()
        with patch("src.sites.guggenheim.HAS_SCRAPLING", False):
            result = p.get_exhibition_urls(None)
            assert result == []

    def test_get_exhibition_urls_scrapling_success(self):
        p = GuggenheimParser()
        mock_fetcher = MagicMock()
        mock_page = MagicMock()
        mock_page.html_content = '<a href="/exhibition/test-show">Link</a>'
        mock_fetcher.fetch.return_value = mock_page

        with (
            patch("src.sites.guggenheim.HAS_SCRAPLING", True),
            patch("src.sites.guggenheim.StealthyFetcher", return_value=mock_fetcher, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert len(result) == 1
            assert "guggenheim.org/exhibition/test-show" in result[0]

    def test_get_exhibition_urls_skips_list_pages(self):
        p = GuggenheimParser()
        mock_fetcher = MagicMock()
        mock_page = MagicMock()
        mock_page.html_content = """
            <a href="/exhibition/real-show">Real</a>
            <a href="/exhibitions">List</a>
            <a href="/exhibitions#past">Past</a>
            <a href="#past-exhibitions">Anchor</a>
        """
        mock_fetcher.fetch.return_value = mock_page

        with (
            patch("src.sites.guggenheim.HAS_SCRAPLING", True),
            patch("src.sites.guggenheim.StealthyFetcher", return_value=mock_fetcher, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert len(result) == 1
            assert "real-show" in result[0]

    def test_get_exhibition_urls_scrapling_failure(self):
        p = GuggenheimParser()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("Scrapling error")

        with (
            patch("src.sites.guggenheim.HAS_SCRAPLING", True),
            patch("src.sites.guggenheim.StealthyFetcher", return_value=mock_fetcher, create=True),
        ):
            result = p.get_exhibition_urls(None)
            assert result == []
