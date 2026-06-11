"""Tests for src/sites/new_museum.py — New Museum parser."""

from unittest.mock import patch

from src.sites.new_museum import NewMuseumParser


class TestNewMuseumParser:
    def test_parser_attributes(self):
        p = NewMuseumParser()
        assert p.source == "New Museum"
        assert p.city == "New York"
        assert p.parser_key == "new_museum"
        assert p.institution_type == "museum"
        assert p.use_playwright is True

    def test_parse_exhibition_page_no_playwright(self):
        p = NewMuseumParser()
        with patch("src.sites.new_museum.HAS_PLAYWRIGHT", False):
            result = p.parse_exhibition_page(None, "http://ex.com")
            assert result is None

    def test_parse_exhibition_page_playwright_failure(self):
        """Parser can be instantiated regardless of Playwright status."""
        _ = NewMuseumParser()

    def test_extract_from_html_with_h1(self):
        p = NewMuseumParser()
        html = "<html><body><h1>Test Exhibition</h1><p>Description paragraph here with more than eighty characters for the preface extraction test case.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["title"] == "Test Exhibition"
        assert result["city"] == "New York"

    def test_extract_from_html_with_date_range(self):
        p = NewMuseumParser()
        html = "<html><body><h1>Summer Show</h1><p>March 21, 2026–August 15, 2026</p><p>Description text longer than 80 characters for the New Museum test case extraction.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["start_date"] == "March 21, 2026"
        assert result["end_date"] == "August 15, 2026"

    def test_extract_from_html_with_ongoing_date(self):
        p = NewMuseumParser()
        html = "<html><body><h1>Ongoing Show</h1><p>November 28, 2024–Ongoing</p><p>Description that is long enough to pass the 80 character threshold for extraction in test.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert result["start_date"] == "November 28, 2024"
        assert result["end_date"] is None  # Ongoing -> None

    def test_extract_from_html_no_title(self):
        p = NewMuseumParser()
        html = "<html><body><p>No heading here</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is None

    def test_extract_from_html_with_curator(self):
        p = NewMuseumParser()
        html = "<html><body><h1>Curated Show</h1><p>curated by Alice Smith, Bob Jones</p><p>This paragraph has enough characters to pass the eighty character threshold that is needed for preface.</p></body></html>"
        result = p._extract_from_html(html, "http://ex.com")
        assert result is not None
        assert len(result["curators"]) > 0
        assert "Alice Smith" in result["curators"][0]

    def test_has_playwright_reload(self):
        import importlib
        from unittest.mock import MagicMock, patch

        import src.sites.new_museum as nm_module

        orig_has_playwright = nm_module.HAS_PLAYWRIGHT
        orig_parser = nm_module.NewMuseumParser

        try:
            with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
                importlib.reload(nm_module)
                assert nm_module.HAS_PLAYWRIGHT is False

            with patch.dict(
                "sys.modules", {"playwright": MagicMock(), "playwright.sync_api": MagicMock()}
            ):
                importlib.reload(nm_module)
                assert nm_module.HAS_PLAYWRIGHT is True
        finally:
            importlib.reload(nm_module)
            nm_module.HAS_PLAYWRIGHT = orig_has_playwright
            nm_module.NewMuseumParser = orig_parser
