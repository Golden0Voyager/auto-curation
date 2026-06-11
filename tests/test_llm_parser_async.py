"""Async and edge case tests for src/llm_parser.py — LLMExhibitionParser."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from src.llm_parser import LLMExhibitionParser

# ---------------------------------------------------------------------------
# Call provider edge cases
# ---------------------------------------------------------------------------


class TestCallProviderEdge:
    def test_parse_response_validates_via_model(self):
        """_parse_response should validate data through ExhibitionModel."""
        parser = LLMExhibitionParser()
        result = parser._parse_response(
            '{"title": "Valid Show", "city": "Paris", "artworks": []}',
            "test",
        )
        assert result is not None
        assert result["title"] == "Valid Show"


# ---------------------------------------------------------------------------
# _is_valid_result edge cases
# ---------------------------------------------------------------------------


class TestIsValidResultEdge:
    def test_null_title(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": None}) is False

    def test_na_title_variants(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": "n/a"}) is False
        assert parser._is_valid_result({"title": "null"}) is False

    def test_concept_too_short(self):
        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": "Too short"}
        assert parser._is_valid_result(data) is False

    def test_has_dates_no_text(self):
        """When dates exist but text is very short, should still be valid."""
        parser = LLMExhibitionParser()
        data = {
            "title": "Show",
            "start_date": "2024-01-01",
            "preface": "",
            "concept": "Adequate concept text here for exhibition.",
        }
        assert parser._is_valid_result(data) is True

    def test_empty_concept_valid(self):
        """Empty concept with dates should be fine."""
        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": None}
        assert parser._is_valid_result(data) is True


# ---------------------------------------------------------------------------
# _build_prompts edge cases
# ---------------------------------------------------------------------------


class TestBuildPromptsEdge:
    def test_empty_text(self):
        parser = LLMExhibitionParser()
        sys_prompt, user_prompt = parser._build_prompts("", "Source", "City")
        assert "=== TEXT ===" in user_prompt

    def test_source_in_prompt(self):
        parser = LLMExhibitionParser()
        _, user_prompt = parser._build_prompts("Sample text", "Specific Museum", "Specific City")
        assert "Specific Museum" in user_prompt
        assert "Specific City" in user_prompt


# ---------------------------------------------------------------------------
# _parse_response edge cases
# ---------------------------------------------------------------------------


class TestParseResponseEdge:
    def test_json_with_extra_fields(self):
        """Extra fields in JSON should be handled by Pydantic."""
        parser = LLMExhibitionParser()
        result = parser._parse_response(
            '{"title": "Show", "extra_field": "ignored", "city": "Berlin"}',
            "test",
        )
        assert result is not None
        assert result["title"] == "Show"

    def test_json_codeblock_with_newlines(self):
        parser = LLMExhibitionParser()
        content = '```json\n{\n  "title": "Multi Line",\n  "city": "London"\n}\n```'
        result = parser._parse_response(content, "test")
        assert result is not None
        assert result["title"] == "Multi Line"

    def test_plain_codeblock(self):
        parser = LLMExhibitionParser()
        content = '```\n{"title": "Plain Codeblock"}\n```'
        result = parser._parse_response(content, "test")
        assert result is not None
        assert result["title"] == "Plain Codeblock"


# ---------------------------------------------------------------------------
# Cache hit test — use temp file to avoid :memory: isolation issue
# ---------------------------------------------------------------------------


class TestParseWithCache:
    def test_cache_hit_returns_cached_value(self):
        """When cache has the key, parse_exhibition_text should return cached data."""
        from src.cache import LLMResponseCache, make_cache_key

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            db_path = f.name
            cache = LLMResponseCache(db_path)

            # Pre-populate cache with expected data
            text = "cached text"
            key = make_cache_key("TestSource:", text)
            expected = {"title": "Cached Show", "city": "Cache City", "artworks": []}
            cache.set(key, "TestSource:", "test", expected)

            cache2 = LLMResponseCache(db_path)
            # Set env vars so providers is non-empty, but mock _call_provider to prevent real API
            with patch.dict(
                os.environ,
                {
                    "XIAOMI_MIMO_API_KEY": "test-key",
                    "MIMO_BASE_URL": "https://test.example.com/v1",
                    "MIMO_MODEL": "test-model",
                },
            ):
                parser = LLMExhibitionParser(cache=cache2)
                with patch.object(parser, "_call_provider", return_value=None):
                    result = parser.parse_exhibition_text(text, "TestSource", "")
                    # Cache hit should return cached data before _call_provider is called
                    assert result == expected

    def test_cache_hit_async(self):
        """Async cache hit test."""
        import asyncio

        from src.cache import LLMResponseCache, make_cache_key

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            db_path = f.name
            cache = LLMResponseCache(db_path)

            text = "cached text"
            key = make_cache_key("TestSource:", text)
            expected = {"title": "Async Cached", "artworks": []}
            cache.set(key, "TestSource:", "test", expected)

            cache2 = LLMResponseCache(db_path)
            with patch.dict(
                os.environ,
                {
                    "XIAOMI_MIMO_API_KEY": "test-key",
                    "MIMO_BASE_URL": "https://test.example.com/v1",
                    "MIMO_MODEL": "test-model",
                },
            ):
                parser = LLMExhibitionParser(cache=cache2)
                with patch.object(parser, "_call_provider_async", return_value=None):
                    result = asyncio.run(parser.parse_exhibition_text_async(text, "TestSource", ""))
                    assert result == expected

    def test_cache_miss_no_providers(self):
        """When cache misses and no providers, return None."""
        with patch.dict(os.environ, {}, clear=True):
            parser = LLMExhibitionParser()
            result = parser.parse_exhibition_text("some text", "Source", "City")
            assert result is None


# ---------------------------------------------------------------------------
# Async: _call_provider_async returns None when no async client
# ---------------------------------------------------------------------------


class TestCallProviderAsync:
    @pytest.mark.asyncio
    async def test_call_provider_async_no_client(self):
        parser = LLMExhibitionParser()
        parser._hub_async_client = None
        result = await parser._call_provider_async("text", "src", "city")
        assert result is None

    @pytest.mark.asyncio
    async def test_call_provider_async_exception(self):
        """Test async provider error handling."""
        with patch.dict(
            os.environ,
            {
                "XIAOMI_MIMO_API_KEY": "test-key",
                "MIMO_BASE_URL": "https://test.example.com/v1",
                "MIMO_MODEL": "test-model",
            },
        ):
            parser = LLMExhibitionParser()
            parser._hub_async_client = AsyncMock()
            parser._hub_async_client.chat.side_effect = Exception("API error")
            result = await parser._call_provider_async("text", "src", "city")
            assert result is None


# ---------------------------------------------------------------------------
# Sync: parse_exhibition_text with cache
# ---------------------------------------------------------------------------


class TestParseExhibitionFull:
    def test_providers_empty_from_env(self):
        """When no API keys, parse_exhibition_text returns None."""
        with patch.dict(os.environ, {}, clear=True):
            parser = LLMExhibitionParser()
            assert parser.providers == []
            result = parser.parse_exhibition_text("text", "s")
            assert result is None
