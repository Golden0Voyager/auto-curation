"""Tests for src/sites/hirshhorn.py — Hirshhorn Museum parser."""

from src.sites.hirshhorn import HirshhornParser


class TestHirshhornParser:
    def test_parser_attributes(self):
        p = HirshhornParser()
        assert p.source == "Hirshhorn Museum and Sculpture Garden"
        assert p.city == "Washington D.C."
        assert p.parser_key == "hirshhorn"
        assert p.status == "BLOCKED_API_KEY"

    def test_get_list_urls_returns_empty(self):
        p = HirshhornParser()
        urls = p.get_list_urls()
        assert urls == []

    def test_get_list_urls_with_year(self):
        p = HirshhornParser()
        urls = p.get_list_urls(since_year=2020)
        assert urls == []

    def test_get_exhibition_urls_returns_empty(self):
        p = HirshhornParser()
        urls = p.get_exhibition_urls(client=None)
        assert urls == []

    def test_get_api_exhibitions_returns_empty(self):
        p = HirshhornParser()
        result = p.get_api_exhibitions()
        assert result == []

    def test_get_api_exhibitions_with_params(self):
        p = HirshhornParser()
        result = p.get_api_exhibitions(since_year=2020, limit=5)
        assert result == []

    def test_clean_html_passthrough(self):
        p = HirshhornParser()
        assert p.clean_html("<html></html>") == "<html></html>"

    def test_strategy_is_rest_api(self):
        from src.sites.base import ParserStrategy

        p = HirshhornParser()
        assert p.strategy == ParserStrategy.REST_API
