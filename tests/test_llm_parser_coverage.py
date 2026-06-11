"""Additional tests for src/llm_parser.py to improve coverage to 100%."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.llm_parser import (
    ArtworkModel,
    ExhibitionModel,
    LLMExhibitionParser,
)


# ---------------------------------------------------------------------------
# LLMExhibitionParser initialization - multiple providers
# ---------------------------------------------------------------------------


class TestInitMultipleProviders:
    def test_with_gemini_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key"}):
            parser = LLMExhibitionParser()
            assert any(p["name"] == "gemini" for p in parser.providers)

    def test_with_siliconflow_key(self):
        with patch.dict(os.environ, {"SILICONFLOW_API_KEY": "test-sf-key"}):
            parser = LLMExhibitionParser()
            assert any(p["name"] == "siliconflow" for p in parser.providers)

    def test_with_all_providers(self):
        with patch.dict(os.environ, {
            "XIAOMI_MIMO_API_KEY": "test-mimo",
            "GEMINI_API_KEY": "test-gemini",
            "SILICONFLOW_API_KEY": "test-sf",
        }):
            parser = LLMExhibitionParser()
            assert len(parser.providers) == 3
            names = [p["name"] for p in parser.providers]
            assert "mimo" in names
            assert "gemini" in names
            assert "siliconflow" in names

    def test_provider_chain_setup(self):
        """Test _setup_auto_hub_chain sets up environment correctly."""
        with patch.dict(os.environ, {"XIAOMI_MIMO_API_KEY": "test-key"}):
            parser = LLMExhibitionParser()
            assert parser._hub_client is not None
            assert parser._hub_async_client is not None


# ---------------------------------------------------------------------------
# _is_valid_result - edge cases
# ---------------------------------------------------------------------------


class TestIsValidResultExtended:
    def test_invalid_n_a_lowercase(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": "n/a"}) is False

    def test_invalid_na_uppercase(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": "NA"}) is False

    def test_invalid_null_title(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": "null"}) is False

    def test_missing_title(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({}) is False

    def test_valid_with_only_end_date(self):
        parser = LLMExhibitionParser()
        data = {
            "title": "Show",
            "end_date": "2024-12-31",
            "concept": "A valid curatorial concept.",
        }
        assert parser._is_valid_result(data) is True

    def test_concept_too_short(self):
        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": "Short"}
        assert parser._is_valid_result(data) is False

    def test_concept_exactly_20_chars(self):
        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": "A" * 20}
        assert parser._is_valid_result(data) is True

    def test_concept_with_none_value(self):
        parser = LLMExhibitionParser()
        data = {"title": "Show", "start_date": "2024-01-01", "concept": None}
        assert parser._is_valid_result(data) is True

    def test_preface_only_long_enough(self):
        parser = LLMExhibitionParser()
        data = {
            "title": "Show",
            "start_date": None,
            "end_date": None,
            "preface": "X" * 50,
            "concept": "A valid curatorial concept.",
        }
        assert parser._is_valid_result(data) is True


# ---------------------------------------------------------------------------
# _parse_response - edge cases
# ---------------------------------------------------------------------------


class TestParseResponseExtended:
    def test_parse_with_extra_whitespace(self):
        parser = LLMExhibitionParser()
        json_str = '  {"title": "Show"}  '
        result = parser._parse_response(json_str, "test")
        assert result is not None
        assert result["title"] == "Show"

    def test_parse_invalid_json_returns_none(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response("not json at all", "test")
        assert result is None

    def test_parse_json_with_missing_required_field(self):
        """Missing required field raises ValidationError which is caught."""
        parser = LLMExhibitionParser()
        json_str = '{"city": "Paris"}'
        # This should raise ValidationError which is caught and returns None
        with pytest.raises(ValidationError):
            parser._parse_response(json_str, "test")

    def test_parse_json_with_artworks(self):
        parser = LLMExhibitionParser()
        json_str = '''
        {
            "title": "Show",
            "artworks": [
                {"artist_name": "A", "work_title": "W1"},
                {"artist_name": "B", "work_title": "W2"}
            ]
        }
        '''
        result = parser._parse_response(json_str, "test")
        assert result is not None
        assert len(result["artworks"]) == 2

    def test_parse_list_returns_first_dict(self):
        parser = LLMExhibitionParser()
        json_str = '[{"title": "First"}, {"title": "Second"}]'
        result = parser._parse_response(json_str, "test")
        assert result is not None
        assert result["title"] == "First"

    def test_parse_empty_list(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response("[]", "test")
        assert result is None

    def test_parse_list_with_non_dict_first(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response('["string", {"title": "At End"}]', "test")
        # The function takes first element if it's a dict, otherwise returns None
        assert result is None


# ---------------------------------------------------------------------------
# _build_prompts
# ---------------------------------------------------------------------------


class TestBuildPromptsExtended:
    def test_prompts_contain_schema(self):
        parser = LLMExhibitionParser()
        sys_prompt, user_prompt = parser._build_prompts("text", "source", "city")
        assert "title" in user_prompt
        assert "preface" in user_prompt
        assert "concept" in user_prompt
        assert "artworks" in user_prompt

    def test_prompts_contain_guidelines(self):
        parser = LLMExhibitionParser()
        sys_prompt, user_prompt = parser._build_prompts("text", "source", "city")
        assert "Strict Guidelines" in user_prompt or "guidelines" in user_prompt.lower()

    def test_prompts_contain_institution(self):
        parser = LLMExhibitionParser()
        sys_prompt, user_prompt = parser._build_prompts("text", "Test Museum", "Tokyo")
        assert "Test Museum" in user_prompt
        assert "Tokyo" in user_prompt


# ---------------------------------------------------------------------------
# parse_exhibition_text - cache hit path
# ---------------------------------------------------------------------------


class TestParseExhibitionTextCacheHit:
    def test_cache_disabled_calls_provider(self):
        """When cache is None, provider should be called."""
        parser = LLMExhibitionParser(cache=None)
        parser._hub_client = MagicMock()
        parser._hub_client.chat.return_value = '{"title": "New Show", "artworks": []}'

        result = parser.parse_exhibition_text("Some text", "TestSource")
        parser._hub_client.chat.assert_called_once()


# ---------------------------------------------------------------------------
# parse_exhibition_text - quality check failure
# ---------------------------------------------------------------------------


class TestParseExhibitionTextQualityCheck:
    def test_quality_check_failure_returns_none(self):
        """When result fails quality check, should return None."""
        parser = LLMExhibitionParser()
        parser._hub_client = MagicMock()
        parser._hub_client.chat.return_value = '{"title": "", "artworks": []}'

        result = parser.parse_exhibition_text("Some text", "TestSource")
        assert result is None

    def test_quality_check_pass_returns_result(self):
        """When result passes quality check, should return data."""
        parser = LLMExhibitionParser()
        parser._hub_client = MagicMock()
        parser._hub_client.chat.return_value = '''
        {
            "title": "Valid Show",
            "start_date": "2024-01-01",
            "concept": "A valid curatorial concept.",
            "artworks": []
        }
        '''

        result = parser.parse_exhibition_text("Some text", "TestSource")
        assert result is not None
        assert result["title"] == "Valid Show"


# ---------------------------------------------------------------------------
# parse_exhibition_text_async - various paths
# ---------------------------------------------------------------------------


class TestParseExhibitionTextAsync:
    @pytest.mark.asyncio
    async def test_async_provider_returns_none(self):
        """Async version: when provider returns None, result should be None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = None

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_provider_returns_invalid_json(self):
        """Async version: when provider returns invalid JSON, result should be None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = "not json"

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_provider_returns_empty_string(self):
        """Async version: when provider returns empty string, result should be None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = ""

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_quality_check_failure(self):
        """Async version: when result fails quality check, should log warning and return None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = '{"title": "", "artworks": []}'

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_cache_miss_writes_cache(self):
        """Async version: cache miss should write result to cache."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        parser = LLMExhibitionParser(cache=mock_cache)
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = '''
        {
            "title": "Valid Show",
            "start_date": "2024-01-01",
            "concept": "A valid curatorial concept.",
            "artworks": []
        }
        '''

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is not None
        assert result["title"] == "Valid Show"
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cache_hit_returns_cached(self):
        """Async version: cache hit should return cached data."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = {"title": "Cached Show", "start_date": "2023-01-01"}
        parser = LLMExhibitionParser(cache=mock_cache)
        parser._hub_async_client = AsyncMock()

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is not None
        assert result["title"] == "Cached Show"
        parser._hub_async_client.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_valid_result_without_cache(self):
        """Async version: valid result without cache should return data."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = '''
        {
            "title": "Valid Show",
            "start_date": "2024-01-01",
            "concept": "A valid curatorial concept.",
            "artworks": []
        }
        '''

        result = await parser.parse_exhibition_text_async("text", "source")
        assert result is not None
        assert result["title"] == "Valid Show"


# ---------------------------------------------------------------------------
# _call_provider - exception handling
# ---------------------------------------------------------------------------


class TestCallProviderException:
    def test_sync_provider_exception_returns_none(self):
        """When sync provider raises exception, should return None."""
        parser = LLMExhibitionParser()
        parser._hub_client = MagicMock()
        parser._hub_client.chat.side_effect = RuntimeError("API error")

        result = parser._call_provider("text", "source", "city")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_provider_exception_returns_none(self):
        """When async provider raises exception, should return None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.side_effect = RuntimeError("API error")

        result = await parser._call_provider_async("text", "source", "city")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_hub_client_is_none(self):
        """When _hub_async_client is None, should return None early."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = None

        result = await parser._call_provider_async("text", "source", "city")
        assert result is None

    def test_sync_hub_client_is_none(self):
        """When _hub_client is None, should return None early."""
        parser = LLMExhibitionParser()
        parser._hub_client = None

        result = parser._call_provider("text", "source", "city")
        assert result is None


# ---------------------------------------------------------------------------
# _call_provider - returns empty content
# ---------------------------------------------------------------------------


class TestCallProviderEmptyContent:
    def test_sync_provider_returns_empty_string(self):
        """When sync provider returns empty string, should return None."""
        parser = LLMExhibitionParser()
        parser._hub_client = MagicMock()
        parser._hub_client.chat.return_value = ""

        result = parser._call_provider("text", "source", "city")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_provider_returns_empty_string(self):
        """When async provider returns empty string, should return None."""
        parser = LLMExhibitionParser()
        parser._hub_async_client = AsyncMock()
        parser._hub_async_client.chat.return_value = ""

        result = await parser._call_provider_async("text", "source", "city")
        assert result is None


# ---------------------------------------------------------------------------
# Pydantic Models - serialization
# ---------------------------------------------------------------------------


class TestModelsSerialization:
    def test_artwork_model_to_dict(self):
        art = ArtworkModel(artist_name="A", work_title="W", work_year="2024")
        d = art.model_dump()
        assert d["artist_name"] == "A"
        assert d["work_year"] == "2024"

    def test_exhibition_model_to_dict(self):
        ex = ExhibitionModel(
            title="Show",
            curators=["C1"],
            artworks=[ArtworkModel(artist_name="A", work_title="W")],
        )
        d = ex.model_dump()
        assert d["title"] == "Show"
        assert len(d["artworks"]) == 1

    def test_artwork_model_from_dict(self):
        d = {"artist_name": "A", "work_title": "W", "medium": "Oil"}
        art = ArtworkModel(**d)
        assert art.medium == "Oil"

    def test_exhibition_model_from_dict(self):
        d = {
            "title": "Show",
            "start_date": "2024-01-01",
            "artworks": [{"artist_name": "A", "work_title": "W"}],
        }
        ex = ExhibitionModel(**d)
        assert len(ex.artworks) == 1
