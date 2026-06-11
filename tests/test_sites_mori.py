"""Tests for src/sites/mori.py — Mori Art Museum parser."""

from datetime import date

from src.sites.mori import MoriParser


class TestMoriParser:
    def test_parser_attributes(self):
        p = MoriParser()
        assert p.source == "Mori Art Museum"
        assert p.city == "Tokyo"
        assert len(p.link_patterns) == 1
        assert "mori" in p.link_patterns[0]
        assert "exhibitions" in p.link_patterns[0]

    def test_get_list_urls_default(self):
        p = MoriParser()
        urls = p.get_list_urls()  # no since_year
        assert urls[0] == "https://www.mori.art.museum/en/exhibitions/"
        assert urls[1] == "https://www.mori.art.museum/en/exhibitions/past/"
        # Default: pages 2 to 20 = 19 additional URLs
        assert len(urls) == 21  # 2 base + 19 pagination pages

    def test_get_list_urls_with_since_year_recent(self):
        p = MoriParser()
        current_year = date.today().year
        urls = p.get_list_urls(since_year=current_year)
        assert len(urls) >= 2

    def test_get_list_urls_with_since_year_far(self):
        p = MoriParser()
        urls = p.get_list_urls(since_year=2003)
        assert len(urls) == 21

    def test_get_list_urls_since_year_negative(self):
        p = MoriParser()
        urls = p.get_list_urls(since_year=1800)
        assert len(urls) == 21
