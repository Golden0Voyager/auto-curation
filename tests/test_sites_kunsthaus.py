"""Tests for src/sites/kunsthaus.py — Kunsthaus Zürich parser."""

import json
from unittest.mock import MagicMock

from src.sites.base import ParserStrategy
from src.sites.kunsthaus import KunsthausParser


class TestKunsthausParser:
    def test_parser_attributes(self):
        p = KunsthausParser()
        assert p.source == "Kunsthaus Zürich"
        assert p.city == "Zürich"
        assert p.parser_key == "kunsthaus"
        assert p.strategy == ParserStrategy.HTML_LLM

    def test_get_list_urls(self):
        p = KunsthausParser()
        urls = p.get_list_urls()
        assert "kunsthaus.ch" in urls[0]

    def test_get_list_urls_with_year(self):
        p = KunsthausParser()
        urls = p.get_list_urls(since_year=2020)
        assert len(urls) == 1

    def test_get_exhibition_urls_request_failure(self):
        """When the listing page request fails, returns empty list."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Network error")
        p = KunsthausParser()
        result = p.get_exhibition_urls(mock_client)
        assert result == []

    def test_normalize_exhibition(self):
        p = KunsthausParser()
        data = {
            "@type": "ExhibitionEvent",
            "name": "Test Exhibition",
            "description": "A description here",
            "startDate": "2024-01-15T00:00:00Z",
            "endDate": "2024-06-30T00:00:00Z",
        }
        result = p._normalize_exhibition(data, "http://ex.com/1")
        assert result["title"] == "Test Exhibition"
        assert result["start_date"] == "2024-01-15"
        assert result["end_date"] == "2024-06-30"
        assert result["source"] == "Kunsthaus Zürich"

    def test_normalize_exhibition_without_dates(self):
        p = KunsthausParser()
        data = {
            "@type": "ExhibitionEvent",
            "name": "No Dates Show",
        }
        result = p._normalize_exhibition(data, "http://ex.com/2")
        assert result["title"] == "No Dates Show"
        assert result["start_date"] is None

    def test_parse_exhibition_page_jsonld(self):
        """Test that JSON-LD is properly extracted from HTML."""
        jsonld = json.dumps(
            {
                "@type": "ExhibitionEvent",
                "name": "JSON-LD Exhibition",
                "description": "From structured data",
                "startDate": "2024-03-01T00:00:00Z",
            }
        )
        html = f'<html><body><script type="application/ld+json">{jsonld}</script></body></html>'
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        p = KunsthausParser()
        result = p.parse_exhibition_page(mock_client, "http://ex.com/3")
        assert result is not None
        assert result["title"] == "JSON-LD Exhibition"

    def test_parse_exhibition_page_no_jsonld(self):
        html = "<html><body><p>No structured data</p></body></html>"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        p = KunsthausParser()
        result = p.parse_exhibition_page(mock_client, "http://ex.com/4")
        assert result is None

    def test_parse_exhibition_page_request_failure(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Failed to fetch")
        p = KunsthausParser()
        result = p.parse_exhibition_page(mock_client, "http://ex.com/5")
        assert result is None

    def test_parse_exhibition_page_list_jsonld(self):
        """Handle list of JSON-LD objects."""
        jsonld = json.dumps(
            [
                {"@type": "WebSite", "name": "Website"},
                {
                    "@type": "ExhibitionEvent",
                    "name": "Exhibition from List",
                    "startDate": "2024-01-01",
                },
            ]
        )
        html = f'<html><body><script type="application/ld+json">{jsonld}</script></body></html>'
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = html
        mock_client.get.return_value = mock_response

        p = KunsthausParser()
        result = p.parse_exhibition_page(mock_client, "http://ex.com/6")
        assert result is not None
        assert result["title"] == "Exhibition from List"

    def test_clean_html_passthrough(self):
        p = KunsthausParser()
        assert p.clean_html("<html/>") == "<html/>"
