import os
from unittest.mock import MagicMock, patch

import pytest

from src.cache import LLMResponseCache
from src.llm_parser import LLMExhibitionParser

TEST_DB = "tests/test_llm_parser.db"
_HUB_ENV_VARS = ["AI_PROVIDER_CHAIN", "MIMO_API_KEY", "MIMO_BASE_URL", "MIMO_MODEL"]


def _setup_minimal_provider(monkeypatch):
    """Set up minimal env vars so LLMExhibitionParser creates a hub client."""
    monkeypatch.setenv("XIAOMI_MIMO_API_KEY", "test-key")
    monkeypatch.setenv("MIMO_BASE_URL", "https://test.example.com/v1")
    monkeypatch.setenv("MIMO_MODEL", "test-model")


@pytest.fixture(autouse=True)
def clean_state():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    for var in _HUB_ENV_VARS:
        os.environ.pop(var, None)
    from auto_hub.llm.provider_chain import reset_provider_chain

    reset_provider_chain()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    for var in _HUB_ENV_VARS:
        os.environ.pop(var, None)
    reset_provider_chain()


def test_llm_parser_cache_hit_skips_api_call(monkeypatch):
    _setup_minimal_provider(monkeypatch)
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    expected = {"title": "Cached Show", "city": "Tokyo", "artworks": []}
    from src.cache import make_cache_key

    key = make_cache_key("TestSource:", "some exhibition text")
    cache.set(key, "url", "TestSource", expected)

    with patch("auto_hub.llm.client.OpenAI") as mock_openai:
        result = parser.parse_exhibition_text("some exhibition text", "TestSource")
        assert result == expected
        mock_openai.assert_not_called()


def test_llm_parser_cache_miss_sets_cache(monkeypatch):
    _setup_minimal_provider(monkeypatch)
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)

    json_content = '{"title":"New Show","city":"Paris","start_date":"2026-01-01","artworks":[]}'

    with patch("auto_hub.llm.client.OpenAI") as mock_openai:
        mock_instance = mock_openai.return_value
        mock_choice = MagicMock()
        mock_choice.message.content = json_content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_instance.chat.completions.create.return_value = mock_response

        result = parser.parse_exhibition_text("fresh text", "TestSource")
        assert result is not None
        assert result["title"] == "New Show"

    from src.cache import make_cache_key

    key = make_cache_key("TestSource:", "fresh text")
    cached = cache.get(key)
    assert cached is not None
    assert cached["title"] == "New Show"


@pytest.mark.asyncio
async def test_llm_parser_async_cache_hit(monkeypatch):
    _setup_minimal_provider(monkeypatch)
    cache = LLMResponseCache(TEST_DB)
    parser = LLMExhibitionParser(cache=cache)
    expected = {"title": "Async Cached", "city": "Berlin", "artworks": []}
    from src.cache import make_cache_key

    key = make_cache_key("AsyncSource:", "async text")
    cache.set(key, "url", "AsyncSource", expected)

    with patch("auto_hub.llm.client.AsyncOpenAI") as mock_async_openai:
        result = await parser.parse_exhibition_text_async("async text", "AsyncSource")
        assert result == expected
        mock_async_openai.assert_not_called()
