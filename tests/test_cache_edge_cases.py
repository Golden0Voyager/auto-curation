"""Tests for src/cache.py edge cases — covers remaining uncovered lines.

Missing lines from coverage:
- 61-63: get() sqlite3.Error / JSONDecodeError exception handling
- 78-79: set() sqlite3.Error exception handling
- 90-92: clear() sqlite3.Error exception handling
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from src.cache import LLMResponseCache, make_cache_key

TEST_DB = "tests/test_cache_edges.db"


@pytest.fixture(autouse=True)
def clean_db():
    import os

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_get_handles_corrupted_json():
    """Line 61-63: corrupted JSON in cache should return None."""
    cache = LLMResponseCache(TEST_DB)
    # Insert a row with invalid JSON directly
    conn = cache._get_connection()
    conn.execute(
        "INSERT INTO llm_cache (cache_key, url, source, result_json) VALUES (?, ?, ?, ?)",
        ("bad_key", "url", "src", "{corrupted json"),
    )
    conn.commit()
    conn.close()

    result = cache.get("bad_key")
    assert result is None


def test_get_handles_database_error():
    """Line 61-63: sqlite3.Error during get should return None."""
    cache = LLMResponseCache(TEST_DB)
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("query failed")
    mock_conn.close.return_value = None
    with patch.object(cache, "_get_connection", return_value=mock_conn):
        result = cache.get("some_key")
        assert result is None


def test_set_handles_database_error():
    """Line 78-79: sqlite3.Error during set should not raise."""
    cache = LLMResponseCache(TEST_DB)
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("write failed")
    mock_conn.close.return_value = None
    with patch.object(cache, "_get_connection", return_value=mock_conn):
        cache.set("k", "url", "src", {"a": 1})


def test_clear_handles_database_error():
    """Line 90-92: sqlite3.Error during clear should return 0."""
    cache = LLMResponseCache(TEST_DB)
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = sqlite3.Error("locked")
    mock_conn.close.return_value = None
    with patch.object(cache, "_get_connection", return_value=mock_conn):
        result = cache.clear()
        assert result == 0


def test_make_cache_key_without_text():
    """make_cache_key with only url."""
    key = make_cache_key("https://example.com")
    assert len(key) == 64


def test_make_cache_key_with_text():
    """make_cache_key with url and text."""
    key = make_cache_key("https://example.com", "some text")
    assert len(key) == 64


def test_cache_roundtrip_with_full_metadata():
    """Full roundtrip with complex nested data."""
    cache = LLMResponseCache(TEST_DB)
    complex_data = {
        "title": "Art Exhibition",
        "city": "Paris",
        "curators": ["Alice", "Bob"],
        "artworks": [
            {"artist_name": "Picasso", "work_title": "Guernica"},
            {"artist_name": "Warhol", "work_title": "Marilyn"},
        ],
    }
    cache.set("complex", "http://url", "Source", complex_data)
    retrieved = cache.get("complex")
    assert retrieved == complex_data


def test_cache_overwrite_existing_key():
    """Overwriting an existing cache entry."""
    cache = LLMResponseCache(TEST_DB)
    cache.set("k1", "url1", "s1", {"v": 1})
    cache.set("k1", "url1", "s1", {"v": 2})
    retrieved = cache.get("k1")
    assert retrieved == {"v": 2}
