"""Tests for src/sites/tate.py — Tate Modern parser."""

from datetime import date

from src.sites.tate import TateParser


class TestTateParser:
    def test_parser_attributes(self):
        p = TateParser()
        assert p.source == "Tate Modern"
        assert p.city == "London"
        assert len(p.link_patterns) == 1
        assert "tate-modern" in p.link_patterns[0]

    def test_get_list_urls_default(self):
        p = TateParser()
        urls = p.get_list_urls()  # no since_year
        expected_urls = [p.list_url]
        # Default: includes current year
        current_year = date.today().year
        expected_past = (
            f"https://www.tate.org.uk/whats-on"
            f"?date_from={current_year}-01-01"
            f"&date_to={current_year}-12-31"
            f"&gallery_group=tate-modern"
            f"&event_type=exhibition"
            f"&date_range=custom"
        )
        expected_urls.append(expected_past)
        assert urls == expected_urls

    def test_get_list_urls_with_since_year(self):
        p = TateParser()
        current_year = date.today().year
        urls = p.get_list_urls(since_year=2022)
        # Should include current listing + years from 2022 to current
        assert len(urls) == (current_year - 2022 + 2)  # +2 for both default and first year

        first_past = urls[1]
        assert "date_from=2022-01-01" in first_past

        last_past = urls[-1]
        assert f"date_from={current_year}-01-01" in last_past

    def test_get_list_urls_with_since_year_in_future(self):
        p = TateParser()
        future_year = date.today().year + 5
        urls = p.get_list_urls(since_year=future_year)
        # Should still return at least 1 URL
        assert len(urls) >= 1
        assert urls[0] == p.list_url
