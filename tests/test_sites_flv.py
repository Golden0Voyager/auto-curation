"""Tests for src/sites/flv.py — Fondation Louis Vuitton parser."""

import unittest.mock

from src.sites import flv as flv_module
from src.sites.flv import FLVParser


class TestFLVParser:
    def test_parser_attributes(self):
        p = FLVParser()
        assert p.source == "Fondation Louis Vuitton"
        assert p.city == "Paris"
        assert p.parser_key == "flv"
        assert p.institution_type == "museum"
        assert p.status == "BLOCKED_SPA"
        assert "fondationlouisvuitton" in p.link_patterns[0]
        assert "events" in p.link_patterns[0]
        assert len(p.link_patterns) == 1

    def test_get_exhibition_urls_without_scrapling(self):
        """When scrapling is not installed, returns empty list."""
        with unittest.mock.patch.object(flv_module, "HAS_SCRAPLING", False):
            p = FLVParser()
            urls = p.get_exhibition_urls(client=None)
            assert urls == []

    def test_get_exhibition_urls_scrapling_mocked(self):
        """When scrapling is mocked as installed, returns URL list."""
        p = FLVParser()
        with (
            unittest.mock.patch.object(flv_module, "HAS_SCRAPLING", True),
            unittest.mock.patch("src.sites.flv.StealthyFetcher", create=True) as mock_fetcher_cls,
        ):
            mock_fetcher = unittest.mock.MagicMock()
            mock_page = unittest.mock.MagicMock()
            mock_page.html_content = '<a href="/en/events/test-exhibition">Link</a>'
            mock_fetcher.fetch.return_value = mock_page
            mock_fetcher_cls.return_value = mock_fetcher
            urls = p.get_exhibition_urls(client=None)
            assert urls == ["https://www.fondationlouisvuitton.fr/en/events/test-exhibition"]

    def test_has_scrapling_reload(self):
        import importlib
        from unittest.mock import MagicMock, patch

        orig_has_scrapling = flv_module.HAS_SCRAPLING
        orig_parser = flv_module.FLVParser

        try:
            with patch.dict(
                "sys.modules", {"scrapling": MagicMock(), "scrapling.StealthyFetcher": MagicMock()}
            ):
                importlib.reload(flv_module)
                assert flv_module.HAS_SCRAPLING is True

            with patch.dict("sys.modules", {"scrapling": None}):
                importlib.reload(flv_module)
                assert flv_module.HAS_SCRAPLING is False
        finally:
            importlib.reload(flv_module)
            flv_module.HAS_SCRAPLING = orig_has_scrapling
            flv_module.FLVParser = orig_parser
