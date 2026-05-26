import os
import pytest
from unittest.mock import patch, MagicMock
from src.cache import LLMResponseCache
from src.llm_parser import LLMExhibitionParser

TEST_DB = "tests/test_llm_parser.db"


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_llm_parser_cache_hit_skips_api_call():
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    expected = {"title": "Cached Show", "city": "Tokyo", "artworks": []}
    from src.cache import make_cache_key
    key = make_cache_key("TestSource:", "some exhibition text")
    cache.set(key, "url", "TestSource", expected)

    with patch("httpx.Client.post") as mock_post:
        result = parser.parse_exhibition_text("some exhibition text", "TestSource")
        assert result == expected
        mock_post.assert_not_called()


def test_llm_parser_cache_miss_sets_cache(monkeypatch):
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": '{"title":"New Show","city":"Paris","start_date":"2026-01-01","artworks":[]}'}}]
    }
    fake_response.raise_for_status = MagicMock()

    with patch("httpx.Client.post", return_value=fake_response):
        result = parser.parse_exhibition_text("fresh text", "TestSource")
        assert result is not None
        assert result["title"] == "New Show"

    from src.cache import make_cache_key
    key = make_cache_key("TestSource:", "fresh text")
    cached = cache.get(key)
    assert cached is not None
    assert cached["title"] == "New Show"


@pytest.mark.asyncio
async def test_llm_parser_async_cache_hit():
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)
    expected = {"title": "Async Cached", "city": "Berlin", "artworks": []}
    from src.cache import make_cache_key
    key = make_cache_key("AsyncSource:", "async text")
    cache.set(key, "url", "AsyncSource", expected)

    with patch("httpx.AsyncClient.post") as mock_post:
        result = await parser.parse_exhibition_text_async("async text", "AsyncSource")
        assert result == expected
        mock_post.assert_not_called()
