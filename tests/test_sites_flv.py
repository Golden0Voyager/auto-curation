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

    def test_get_exhibition_urls_with_scrapling(self):
        """When scrapling is installed, it attempts to fetch."""
        p = FLVParser()
        if flv_module.HAS_SCRAPLING:
            urls = p.get_exhibition_urls(client=None)
            assert isinstance(urls, list)

    def test_has_scrapling_reload(self):
        import importlib
        from unittest.mock import MagicMock, patch

        orig_has_scrapling = flv_module.HAS_SCRAPLING
        orig_parser = flv_module.FLVParser

        try:
            with patch.dict("sys.modules", {
                "scrapling": MagicMock(),
                "scrapling.StealthyFetcher": MagicMock()
            }):
                importlib.reload(flv_module)
                assert flv_module.HAS_SCRAPLING is True

            with patch.dict("sys.modules", {"scrapling": None}):
                importlib.reload(flv_module)
                assert flv_module.HAS_SCRAPLING is False
        finally:
            importlib.reload(flv_module)
            flv_module.HAS_SCRAPLING = orig_has_scrapling
            flv_module.FLVParser = orig_parser

