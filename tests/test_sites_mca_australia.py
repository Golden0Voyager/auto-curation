"""Tests for src/sites/mca_australia.py — MCA Australia parser."""

import re
from unittest.mock import patch

from src.sites.mca_australia import MCAAustraliaParser


class TestMCAAustraliaParser:
    def test_parser_attributes(self):
        p = MCAAustraliaParser()
        assert p.source == "MCA Australia"
        assert p.city == "Sydney"
        assert p.parser_key == "mca_australia"
        assert p.use_playwright is True
        assert len(p.link_patterns) > 0
        assert (
            re.search(p.link_patterns[0], "https://www.mca.com.au/exhibitions/current") is not None
        )

    def test_get_exhibition_urls_no_playwright(self):
        p = MCAAustraliaParser()
        with patch("src.sites.mca_australia.HAS_PLAYWRIGHT", False):
            urls = p.get_exhibition_urls(client=None)
            assert urls == []

    def test_get_exhibition_urls_success(self):
        from unittest.mock import MagicMock
        p = MCAAustraliaParser()

        mock_playwright = MagicMock()
        mock_playwright.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.evaluate.return_value = ["https://www.mca.com.au/exhibitions/show1"]

        mock_button = MagicMock()
        mock_page.get_by_text.return_value.first = mock_button

        with patch("src.sites.mca_australia.sync_playwright", return_value=mock_playwright, create=True), \
             patch("src.sites.mca_australia.HAS_PLAYWRIGHT", True):
            urls = p.get_exhibition_urls(client=None)
            assert len(urls) == 1
            assert urls[0] == "https://www.mca.com.au/exhibitions/show1"
            mock_button.click.assert_called_once()

    def test_has_playwright_reload(self):
        import importlib
        from unittest.mock import MagicMock, patch

        import src.sites.mca_australia as mca_module

        orig_has_playwright = mca_module.HAS_PLAYWRIGHT
        orig_parser = mca_module.MCAAustraliaParser

        try:
            with patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
                importlib.reload(mca_module)
                assert mca_module.HAS_PLAYWRIGHT is False

            with patch.dict("sys.modules", {
                "playwright": MagicMock(),
                "playwright.sync_api": MagicMock()
            }):
                importlib.reload(mca_module)
                assert mca_module.HAS_PLAYWRIGHT is True
        finally:
            importlib.reload(mca_module)
            mca_module.HAS_PLAYWRIGHT = orig_has_playwright
            mca_module.MCAAustraliaParser = orig_parser

