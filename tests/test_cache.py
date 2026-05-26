import os
import pytest
from src.cache import LLMResponseCache, make_cache_key

TEST_DB = "tests/test_cache.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_make_cache_key_consistency():
    key1 = make_cache_key("https://example.com/ex1", "some text")
    key2 = make_cache_key("https://example.com/ex1", "some text")
    assert key1 == key2
    assert len(key1) == 64  # sha256 hex


def test_make_cache_key_differentiates_text():
    key1 = make_cache_key("https://example.com/ex1", "text a")
    key2 = make_cache_key("https://example.com/ex1", "text b")
    assert key1 != key2


def test_cache_set_and_get():
    cache = LLMResponseCache(TEST_DB)
    result = {"title": "Test Exhibition", "city": "Beijing"}
    cache.set("key1", "https://example.com/1", "test", result)

    cached = cache.get("key1")
    assert cached == result


def test_cache_miss_returns_none():
    cache = LLMResponseCache(TEST_DB)
    assert cache.get("nonexistent") is None


def test_cache_clear():
    cache = LLMResponseCache(TEST_DB)
    cache.set("k1", "url1", "s1", {"a": 1})
    cache.set("k2", "url2", "s2", {"b": 2})
    assert cache.clear() == 2
    assert cache.get("k1") is None
