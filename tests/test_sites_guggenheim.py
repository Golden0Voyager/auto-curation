"""Tests for src/sites/guggenheim.py — Guggenheim Museum parser."""

import unittest.mock

from src.sites import guggenheim as guggenheim_module
from src.sites.guggenheim import GuggenheimParser


class TestGuggenheimParser:
    def test_parser_attributes(self):
        p = GuggenheimParser()
        assert p.source == "Guggenheim Museum"
        assert p.city == "New York"
        assert p.parser_key == "guggenheim"
        assert p.institution_type == "museum"
        assert p.status == "BLOCKED_CLOUDFLARE"
        assert "/exhibition/" in p.link_patterns[0]

    def test_get_exhibition_urls_without_scrapling(self):
        """When scrapling is not installed, returns empty list."""
        with unittest.mock.patch.object(guggenheim_module, "HAS_SCRAPLING", False):
            p = GuggenheimParser()
            urls = p.get_exhibition_urls(client=None)
            assert urls == []

    def test_get_exhibition_urls_scrapling_mocked(self):
        """When scrapling is mocked as installed, returns URL list."""
        p = GuggenheimParser()
        with (
            unittest.mock.patch.object(guggenheim_module, "HAS_SCRAPLING", True),
            unittest.mock.patch(
                "src.sites.guggenheim.StealthyFetcher", create=True
            ) as mock_fetcher_cls,
        ):
            mock_fetcher = unittest.mock.MagicMock()
            mock_page = unittest.mock.MagicMock()
            mock_page.html_content = '<a href="/exhibition/test">Link</a>'
            mock_fetcher.fetch.return_value = mock_page
            mock_fetcher_cls.return_value = mock_fetcher
            urls = p.get_exhibition_urls(client=None)
            assert isinstance(urls, list)
