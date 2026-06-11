"""Tests for src/sites/vam.py — V&A Museum parser."""

from src.sites.vam import VAMParser


class TestVAMParser:
    def test_parser_attributes(self):
        p = VAMParser()
        assert p.source == "V&A Museum"
        assert p.city == "London"
        assert p.parser_key == "vam"
        assert p.institution_type == "museum"
        assert p.list_url == "https://www.vam.ac.uk/whatson?type=exhibition"
        assert len(p.link_patterns) == 1
        assert r"/exhibitions/" in p.link_patterns[0]

    def test_get_list_urls(self):
        p = VAMParser()
        urls = p.get_list_urls()
        assert len(urls) == 3
        assert "type=exhibition" in urls[0]
        assert "status=current" in urls[1]
        assert "status=upcoming" in urls[2]

    def test_get_list_urls_with_since_year(self):
        p = VAMParser()
        urls = p.get_list_urls(since_year=2020)
        assert len(urls) == 3  # same as without year -- no year-based filtering
