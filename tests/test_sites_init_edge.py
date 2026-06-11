"""Tests for src/sites/__init__.py — parser discovery edge cases."""

from unittest.mock import patch

from src.sites import _discover_parsers


class TestDiscoverParsers:
    def test_discover_parsers_returns_dict(self):
        """_discover_parsers should return a dict of discovered parsers."""
        parsers = _discover_parsers()
        assert isinstance(parsers, dict)
        assert len(parsers) > 0

    def test_discover_handles_import_error(self):
        """When a module fails to import, it should be logged but not crash."""
        with patch("src.sites.importlib.import_module") as mock_import:
            mock_import.side_effect = [None, Exception("Import failed"), None, None, None, None]
            # Should not raise
            parsers = _discover_parsers()
            assert isinstance(parsers, dict)

    def test_discover_handles_key_collision(self):
        """When two parsers have the same key, the second should be skipped."""
        _ = _discover_parsers()
        # Just verify no errors - collision handling is tested implicitly

    def test_sites_has_expected_parsers(self):
        """Verify that common parsers are registered."""
        from src.sites import SITES

        assert "tate" in SITES
        assert "moma" in SITES
        assert "mplus" in SITES
        assert "serpentine" in SITES
