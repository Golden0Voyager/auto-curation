"""Tests for src/sites/sharjah_biennale.py — Sharjah Biennial parser."""

from src.sites.sharjah_biennale import SharjahBiennaleParser


class TestSharjahBiennaleParser:
    def test_parser_attributes(self):
        p = SharjahBiennaleParser()
        assert p.source == "Sharjah Biennial"
        assert p.city == "Sharjah"
        assert p.parser_key == "sharjah_biennale"
        assert p.institution_type == "biennial"
        assert "sb-" in p.link_patterns[0]

    def test_get_exhibition_urls(self):
        p = SharjahBiennaleParser()
        urls = p.get_exhibition_urls(client=None)
        assert len(urls) == 17  # sb-1 to sb-17
        for i in range(1, 18):
            assert f"https://www.sharjahart.org/en/sharjah-biennial/sb-{i}/" in urls

    def test_get_exhibition_urls_with_since_year(self):
        p = SharjahBiennaleParser()
        urls = p.get_exhibition_urls(client=None, since_year=2020)
        assert len(urls) == 17  # same, since year doesn't filter
