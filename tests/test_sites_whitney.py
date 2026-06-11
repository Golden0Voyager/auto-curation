"""Tests for src/sites/whitney.py — Whitney Museum parser."""

from unittest.mock import MagicMock, patch

from src.sites.base import ParserStrategy
from src.sites.whitney import WhitneyParser


def _make_response(data_list: list):
    """Helper to create a mock HTTP response with given data."""
    resp = MagicMock()
    resp.json.return_value = {"data": data_list}
    return resp


class TestWhitneyParser:
    def test_parser_attributes(self):
        p = WhitneyParser()
        assert p.source == "Whitney Museum of American Art"
        assert p.city == "New York"
        assert p.parser_key == "whitney"
        assert p.strategy == ParserStrategy.REST_API

    def test_get_list_urls(self):
        p = WhitneyParser()
        urls = p.get_list_urls()
        assert "whitney.org/api/exhibitions" in urls[0]

    def test_get_exhibition_urls_empty(self):
        p = WhitneyParser()
        assert p.get_exhibition_urls(None) == []

    def test_get_api_exhibitions_with_limit(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            # Return data on first call, empty on subsequent calls to break pagination
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {
                                "title": "Whitney Show",
                                "start_time": "2024-01-01T00:00:00Z",
                                "end_time": "2024-06-01T00:00:00Z",
                                "primary_text": "<p>Exhibition description here</p>",
                                "url": "/exhibitions/1",
                            },
                        }
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions(limit=10)
            assert len(result) == 1
            assert result[0]["title"] == "Whitney Show"
            assert "description" in result[0]["preface"]

    def test_get_api_exhibitions_empty(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.return_value = _make_response([])
            p = WhitneyParser()
            result = p.get_api_exhibitions()
            assert result == []

    def test_get_api_exhibitions_no_title_skipped(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {"id": 1, "attributes": {"title": ""}},
                        {
                            "id": 2,
                            "attributes": {
                                "title": "Real Show",
                                "start_time": "2024-01-01T00:00:00Z",
                            },
                        },
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions()
            assert len(result) == 1

    def test_get_api_exhibitions_since_year_filter(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {"title": "Old", "start_time": "2010-01-01T00:00:00Z"},
                        },
                        {
                            "id": 2,
                            "attributes": {"title": "New", "start_time": "2024-01-01T00:00:00Z"},
                        },
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "New"

    def test_get_api_exhibitions_request_failure(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = Exception("Network error")
            p = WhitneyParser()
            result = p.get_api_exhibitions()
            assert result == []

    def test_get_api_exhibitions_full_url(self):
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {
                                "title": "Show",
                                "start_time": "2024-01-01T00:00:00Z",
                                "url": "https://whitney.org/exhibitions/1",
                            },
                        }
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions()
            assert result[0]["url"].startswith("https://")

    def test_clean_html_passthrough(self):
        p = WhitneyParser()
        assert p.clean_html("test") == "test"

    def test_limit_breaks_before_next_page(self):
        """Covers L50: outer while-loop limit check triggers break before fetching next page."""
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            # Page 1 returns exactly 1 item; limit=1 means outer check fires before page 2
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {
                                "title": "Show A",
                                "start_time": "2024-01-01T00:00:00Z",
                                "end_time": "2024-06-01T00:00:00Z",
                                "url": "/exhibitions/1",
                            },
                        }
                    ]
                ),
                # This page should never be reached
                _make_response([{"id": 2, "attributes": {"title": "Should Not Appear"}}]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions(limit=1)
            assert len(result) == 1
            assert result[0]["title"] == "Show A"
            # Confirm page 2 was never fetched
            assert mock_instance.get.call_count == 1

    def test_limit_breaks_mid_page(self):
        """Covers L68: inner for-loop limit check stops processing items mid-page."""
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {
                                "title": "First",
                                "start_time": "2024-01-01T00:00:00Z",
                                "url": "/exhibitions/1",
                            },
                        },
                        {
                            "id": 2,
                            "attributes": {
                                "title": "Second",
                                "start_time": "2024-02-01T00:00:00Z",
                                "url": "/exhibitions/2",
                            },
                        },
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            result = p.get_api_exhibitions(limit=1)
            assert len(result) == 1
            assert result[0]["title"] == "First"

    def test_invalid_start_time_does_not_raise(self):
        """Covers L83-84: malformed start_time triggers ValueError/IndexError → pass."""
        with patch("src.sites.whitney.httpx.Client") as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            mock_instance.get.side_effect = [
                _make_response(
                    [
                        {
                            "id": 1,
                            "attributes": {
                                "title": "Garbled Date Show",
                                # Non-numeric prefix causes int() to raise ValueError
                                "start_time": "INVALID-DATE",
                                "url": "/exhibitions/1",
                            },
                        }
                    ]
                ),
                _make_response([]),
            ]
            p = WhitneyParser()
            # since_year triggers the date-parsing branch; malformed value must not crash
            result = p.get_api_exhibitions(since_year=2020)
            assert len(result) == 1
            assert result[0]["title"] == "Garbled Date Show"
