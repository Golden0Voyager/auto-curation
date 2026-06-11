"""Tests for src/sites/nga.py — NGA CSV parser."""

from unittest.mock import patch

from src.sites.base import ParserStrategy
from src.sites.nga import NGAParser


class TestNGAParser:
    def test_parser_attributes(self):
        p = NGAParser()
        assert p.source == "National Gallery of Art"
        assert p.city == "Washington D.C."
        assert p.parser_key == "nga"
        assert p.strategy == ParserStrategy.ARTWORK_ONLY

    def test_get_list_urls(self):
        p = NGAParser()
        urls = p.get_list_urls()
        assert "objects.csv" in urls[0]

    def test_get_exhibition_urls_empty(self):
        p = NGAParser()
        assert p.get_exhibition_urls(None) == []

    def test_get_csv_artworks_no_local_files(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=False):
            result = p.get_csv_artworks()
            assert result == []

    def test_ensure_local_files_returns_false(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=False):
            assert p._ensure_local_files() is False

    def test_ensure_local_files_returns_true(self):
        p = NGAParser()
        with patch("os.path.exists", return_value=True):
            assert p._ensure_local_files() is True

    def test_clean_html_passthrough(self):
        p = NGAParser()
        assert p.clean_html("test") == "test"
