"""Tests for src/sites/aic.py — Art Institute of Chicago parser."""

from unittest.mock import MagicMock, patch

from src.sites.aic import AICParser
from src.sites.base import ParserStrategy


class TestAICParser:
    def test_parser_attributes(self):
        p = AICParser()
        assert p.source == "Art Institute of Chicago"
        assert p.city == "Chicago"
        assert p.parser_key == "aic"
        assert p.institution_type == "museum"
        assert p.strategy == ParserStrategy.REST_API

    def test_get_list_urls(self):
        p = AICParser()
        urls = p.get_list_urls()
        assert len(urls) == 1
        assert "api.artic.edu" in urls[0]

    def test_get_exhibition_urls_returns_empty(self):
        p = AICParser()
        urls = p.get_exhibition_urls(client=None)
        assert urls == []

    def test_get_api_exhibitions_with_limit(self):
        """Test API fetching with limit actually makes an HTTP request."""
        # We mock the HTTP client to avoid real API calls
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [
                    {
                        "id": 1,
                        "title": "Test Exhibition",
                        "aic_start_at": "2024-01-01T00:00:00Z",
                        "aic_end_at": "2024-06-01T00:00:00Z",
                        "description": "A test exhibition",
                        "artist_titles": ["Artist A", "Artist B"],
                        "artwork_titles": ["Work 1", "Work 2"],
                        "gallery_title": "Gallery 100",
                        "web_url": "http://ex.com/1",
                    }
                ],
                "pagination": {"total_pages": 1},
            }
            p = AICParser()
            result = p.get_api_exhibitions(limit=5)
            assert len(result) == 1
            assert result[0]["title"] == "Test Exhibition"
            assert result[0]["city"] == "Chicago"
            assert len(result[0]["artworks"]) == 2

    def test_get_api_exhibitions_empty_response(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [],
                "pagination": {"total_pages": 0},
            }
            p = AICParser()
            result = p.get_api_exhibitions(limit=5)
            assert result == []

    def test_get_api_exhibitions_no_title_skipped(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [
                    {"id": 1, "title": "", "artist_titles": []},
                    {
                        "id": 2,
                        "title": "Real Show",
                        "aic_start_at": "2024-01-01T00:00:00Z",
                        "artist_titles": [],
                    },
                ],
                "pagination": {"total_pages": 1},
            }
            p = AICParser()
            result = p.get_api_exhibitions()
            assert len(result) == 1
            assert result[0]["title"] == "Real Show"

    def test_get_api_exhibitions_since_year_filter(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [
                    {
                        "id": 1,
                        "title": "Old Show",
                        "aic_start_at": "2010-01-01T00:00:00Z",
                        "artist_titles": [],
                    },
                    {
                        "id": 2,
                        "title": "New Show",
                        "aic_start_at": "2024-01-01T00:00:00Z",
                        "artist_titles": [],
                    },
                ],
                "pagination": {"total_pages": 1},
            }
            p = AICParser()
            result = p.get_api_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "New Show"

    def test_get_api_exhibitions_request_failure(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = Exception("Network error")
            p = AICParser()
            result = p.get_api_exhibitions()
            assert result == []

    def test_get_api_exhibitions_pagination_multiple_pages(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            # First page returns 1 item with total_pages=2, second page returns 1 item
            mock_instance.get.side_effect = [
                MagicMock(
                    json=lambda: {
                        "data": [
                            {
                                "id": 1,
                                "title": "Page1",
                                "aic_start_at": "2024-01-01T00:00:00Z",
                                "artist_titles": [],
                            }
                        ],
                        "pagination": {"total_pages": 2},
                    }
                ),
                MagicMock(
                    json=lambda: {
                        "data": [
                            {
                                "id": 2,
                                "title": "Page2",
                                "aic_start_at": "2024-06-01T00:00:00Z",
                                "artist_titles": [],
                            }
                        ],
                        "pagination": {"total_pages": 2},
                    }
                ),
            ]
            p = AICParser()
            result = p.get_api_exhibitions()
            assert len(result) == 2

    def test_clean_html_passthrough(self):
        p = AICParser()
        assert p.clean_html("<html/>") == "<html/>"

    def test_get_api_exhibitions_limit_breaks(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [
                    {"id": 1, "title": "Show 1", "aic_start_at": "2024-01-01T00:00:00Z"},
                    {"id": 2, "title": "Show 2", "aic_start_at": "2024-02-01T00:00:00Z"},
                ],
                "pagination": {"total_pages": 2},
            }
            p = AICParser()
            result = p.get_api_exhibitions(limit=1)
            assert len(result) == 1
            assert result[0]["title"] == "Show 1"

    def test_get_api_exhibitions_invalid_date_format(self):
        with patch("src.sites.aic.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value.json.return_value = {
                "data": [
                    {"id": 1, "title": "Show 1", "aic_start_at": "abcd-ef-gh"},
                ],
                "pagination": {"total_pages": 1},
            }
            p = AICParser()
            result = p.get_api_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "Show 1"

