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
