"""Additional tests for src/sites/__init__.py to improve coverage to 100%."""

import importlib
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.sites import SITES, _discover_parsers


class TestDiscoverParsersPrivateModule:
    def test_private_module_skipped(self, caplog):
        """Module starting with '_' should be skipped."""
        with patch("src.sites.pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [("", "_hidden_test", True)]
            with patch("importlib.import_module") as mock_import:
                result = _discover_parsers()
                mock_import.assert_not_called()
                assert isinstance(result, dict)


class TestDiscoverParsersGenericSource:
    def test_generic_source_skipped(self):
        """Class with source='' or 'Generic' should be skipped."""
        backup = _remove_real_sites_modules()

        try:
            mock_mod = MagicMock()
            mock_mod.GenericTestParser = type("GenericTestParser", (), {
                "source": "", "city": "Test", "parser_key": "generic_test"
            })
            sys.modules["src.sites.test_generic"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]):
                result = _discover_parsers()
                assert "generic_test" not in result
        finally:
            _restore_sites_modules(backup)

    def test_generic_string_source_skipped(self):
        """Class with source='Generic' should be skipped."""
        backup = _remove_real_sites_modules()

        try:
            mock_mod = MagicMock()
            mock_mod.GenericStrParser = type("GenericStrParser", (), {
                "source": "Generic", "city": "Test", "parser_key": "generic_str"
            })
            sys.modules["src.sites.test_generic_str"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]):
                result = _discover_parsers()
                assert "generic_str" not in result
        finally:
            _restore_sites_modules(backup)


class TestDiscoverParsersKeyCollision:
    def test_key_collision_logs_warning(self, caplog):
        """Duplicate parser key should log a warning and skip duplicate."""
        backup = _remove_real_sites_modules()

        try:
            mock_mod = MagicMock()
            mock_mod.FirstParser = type("FirstParser", (), {
                "source": "First", "city": "Test", "parser_key": "collision"
            })
            mock_mod.SecondParser = type("SecondParser", (), {
                "source": "Second", "city": "Test", "parser_key": "collision"
            })
            sys.modules["src.sites.test_collision"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]), \
                 caplog.at_level(logging.WARNING):
                result = _discover_parsers()
                assert result["collision"].source == "First"
                assert "collision" in caplog.text.lower()
        finally:
            _restore_sites_modules(backup)

    def test_key_collision_from_class_name(self, caplog):
        """Duplicate parser key derived from class name should log warning."""
        backup = _remove_real_sites_modules()

        try:
            mock_mod = MagicMock()
            mock_mod.TestParser = type("TestParser", (), {
                "source": "A", "city": "Test"
            })
            mock_mod.testParser = type("testParser", (), {
                "source": "B", "city": "Test"
            })
            sys.modules["src.sites.test_dup"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]), \
                 caplog.at_level(logging.WARNING):
                result = _discover_parsers()
                assert "test" in result
                assert result["test"].source == "A"
                assert "collision" in caplog.text.lower()
        finally:
            _restore_sites_modules(backup)


class TestDiscoverParsersInstantiationFailure:
    def test_instantiation_failure_logs_error(self, caplog):
        """Failed parser instantiation should log error and skip."""
        backup = _remove_real_sites_modules()

        try:
            class FailingParser:
                source = "Failing"
                city = "Test"
                parser_key = "failing"

                def __init__(self):
                    raise RuntimeError("Cannot instantiate")

            mock_mod = MagicMock()
            mock_mod.FailingParser = FailingParser
            sys.modules["src.sites.test_failing"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]), \
                 caplog.at_level(logging.ERROR):
                result = _discover_parsers()
                assert "failing" not in result
                assert "failed to instantiate" in caplog.text.lower()
        finally:
            _restore_sites_modules(backup)


class TestDiscoverParsersEmptySourceNotSkipped:
    def test_valid_source_registered(self):
        """Parser with valid source should be registered."""
        backup = _remove_real_sites_modules()

        try:
            mock_mod = MagicMock()
            mock_mod.ValidTestParser = type("ValidTestParser", (), {
                "source": "Valid Source", "city": "TestCity", "parser_key": "valid_test"
            })
            sys.modules["src.sites.test_valid"] = mock_mod

            with patch("src.sites.pkgutil.iter_modules", return_value=[]):
                result = _discover_parsers()
                assert "valid_test" in result
                assert result["valid_test"].source == "Valid Source"
        finally:
            _restore_sites_modules(backup)


def _remove_real_sites_modules():
    """Remove real src.sites.* modules from sys.modules and return backup."""
    backup = {}
    for name in list(sys.modules.keys()):
        if name.startswith("src.sites.") and name != "src.sites":
            backup[name] = sys.modules.pop(name)
    return backup


def _restore_sites_modules(backup):
    """Restore real src.sites.* modules."""
    for name in list(sys.modules.keys()):
        if name.startswith("src.sites.") and name != "src.sites":
            del sys.modules[name]
    sys.modules.update(backup)