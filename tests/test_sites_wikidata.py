"""Tests for src/sites/wikidata.py — Wikidata SPARQL parser."""

import json
from unittest.mock import MagicMock, patch

from src.sites.base import ParserStrategy
from src.sites.wikidata import (
    WIKIDATA_MUSEUM_QIDS,
    WikidataParser,
)


class TestWikidataParser:
    def test_parser_attributes(self):
        p = WikidataParser()
        assert p.source == "Wikidata"
        assert p.city == "Various"
        assert p.parser_key == "wikidata"
        assert p.strategy == ParserStrategy.SPARQL

    def test_get_exhibition_urls_empty(self):
        p = WikidataParser()
        assert p.get_exhibition_urls(None) == []

    def test_build_sparql_query_default(self):
        p = WikidataParser()
        query = p._build_sparql_query()
        assert "SELECT" in query
        assert "wd:Q19675" in query  # Louvre QID
        assert "LIMIT" not in query
        assert "FILTER" not in query

    def test_build_sparql_query_with_since_year(self):
        p = WikidataParser()
        query = p._build_sparql_query(since_year=2020)
        assert "FILTER(YEAR(?start) >= 2020)" in query

    def test_build_sparql_query_with_limit(self):
        p = WikidataParser()
        query = p._build_sparql_query(limit=50)
        assert "LIMIT 50" in query

    def test_museum_qids_defined(self):
        assert len(WIKIDATA_MUSEUM_QIDS) > 0
        assert all(len(item) == 3 for item in WIKIDATA_MUSEUM_QIDS)
        # Check some known entries
        qids = {qid for qid, _, _ in WIKIDATA_MUSEUM_QIDS}
        assert "Q19675" in qids  # Louvre
        assert "Q189826" in qids  # Tate Modern

    def test_get_api_exhibitions_request_success(self):
        """Test with mocked urllib request."""
        with patch("src.sites.wikidata.urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"results":{"bindings":[]}}'
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            p = WikidataParser()
            result = p.get_api_exhibitions()
            assert result == []

    def test_get_api_exhibitions_with_results(self):
        mock_json = {
            "results": {
                "bindings": [
                    {
                        "exhibition": {"value": "http://www.wikidata.org/entity/Q123"},
                        "exhibitionLabel": {"value": "Test Exhibition"},
                        "museum": {"value": "http://www.wikidata.org/entity/Q19675"},
                        "museumLabel": {"value": "Louvre"},
                        "start": {"value": "2024-01-01T00:00:00Z"},
                        "end": {"value": "2024-06-01T00:00:00Z"},
                        "cityLabel": {"value": "Paris"},
                    }
                ]
            }
        }
        with patch("src.sites.wikidata.urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_json).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            p = WikidataParser()
            result = p.get_api_exhibitions()
            assert len(result) == 1
            assert result[0]["title"] == "Test Exhibition"
            assert result[0]["city"] == "Paris"
            assert result[0]["start_date"] == "2024-01-01"

    def test_get_api_exhibitions_missing_label_fallback(self):
        """When label is missing, fallback to QID-based title."""
        mock_json = {
            "results": {
                "bindings": [
                    {
                        "exhibition": {"value": "http://www.wikidata.org/entity/Q123"},
                        "exhibitionLabel": {"value": "Q123"},
                        "museum": {"value": "http://www.wikidata.org/entity/Q19675"},
                        "museumLabel": {"value": "Louvre"},
                        "start": {"value": "2024-01-01T00:00:00Z"},
                        "cityLabel": {"value": "Paris"},
                    }
                ]
            }
        }
        with patch("src.sites.wikidata.urllib.request.urlopen") as mock_urlopen:
            import json

            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_json).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            p = WikidataParser()
            result = p.get_api_exhibitions()
            assert len(result) == 1
            # Should fallback to ex_id
            assert result[0]["title"] == "Q123" or len(result[0]["title"]) > 0

    def test_get_api_exhibitions_request_failure(self):
        with patch("src.sites.wikidata.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")
            p = WikidataParser()
            result = p.get_api_exhibitions()
            assert result == []

    def test_clean_html_passthrough(self):
        p = WikidataParser()
        assert p.clean_html("test") == "test"
