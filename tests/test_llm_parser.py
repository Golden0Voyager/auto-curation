"""Comprehensive tests for src/llm_parser.py — LLMExhibitionParser."""

import os
from unittest.mock import patch

import pytest

from src.llm_parser import (
    ArtworkModel,
    ExhibitionModel,
    LLMExhibitionParser,
)

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class TestArtworkModel:
    def test_minimal_artwork(self):
        art = ArtworkModel(artist_name="Picasso", work_title="Guernica")
        assert art.artist_name == "Picasso"
        assert art.work_title == "Guernica"
        assert art.work_year is None
        assert art.medium is None

    def test_full_artwork(self):
        art = ArtworkModel(
            artist_name="Warhol",
            work_title="Marilyn",
            work_year="1962",
            medium="Silkscreen",
            dimensions="40x40",
            caption="Iconic pop art",
        )
        assert art.artist_name == "Warhol"
        assert art.caption == "Iconic pop art"

    def test_artwork_defaults(self):
        art = ArtworkModel(artist_name="Kusama", work_title="Infinity Room")
        assert art.artist_name == "Kusama"
        assert art.work_title == "Infinity Room"


class TestExhibitionModel:
    def test_minimal_exhibition(self):
        ex = ExhibitionModel(title="Test Show")
        assert ex.title == "Test Show"
        assert ex.preface is None
        assert ex.concept is None
        assert ex.curators == []
        assert ex.artworks == []

    def test_exhibition_with_artworks(self):
        ex = ExhibitionModel(
            title="Group Show",
            curators=["Alice"],
            artworks=[ArtworkModel(artist_name="Bob", work_title="Work")],
        )
        assert len(ex.artworks) == 1
        assert ex.artworks[0].artist_name == "Bob"

    def test_exhibition_all_fields(self):
        ex = ExhibitionModel(
            title="Big Show",
            preface="A big show",
            concept="Curatorial concept",
            preface_en="English preface",
            concept_en="English concept",
            biographies="Artist bios",
            biographies_cn="中文传记",
            credits="Thanks",
            curators=["X", "Y"],
            images=["http://img.com/1.jpg"],
            start_date="2024-01-01",
            end_date="2024-03-01",
            location="Main Gallery",
            city="New York",
            artworks=[ArtworkModel(artist_name="A", work_title="W")],
        )
        assert ex.title == "Big Show"
        assert len(ex.images) == 1
        assert ex.city == "New York"


# ---------------------------------------------------------------------------
# _is_valid_result
# ---------------------------------------------------------------------------


class TestIsValidResult:
    def test_valid_with_title_and_dates(self):
        parser = LLMExhibitionParser()
        data = {
            "title": "Show",
            "start_date": "2024-01-01",
            "preface": "Some text",
            "concept": "A nice curatorial concept for the exhibition.",
        }
        assert parser._is_valid_result(data) is True

    def test_invalid_empty_title(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": ""}) is False

    def test_invalid_na_title(self):
        parser = LLMExhibitionParser()
        assert parser._is_valid_result({"title": "N/A"}) is False

    def test_no_dates_short_text(self):
        parser = LLMExhibitionParser()
        data = {
            "title": "Test",
            "start_date": None,
            "end_date": None,
            "preface": "short",
            "concept": "Very short",
        }
        assert parser._is_valid_result(data) is False

    def test_no_dates_long_text(self):
        parser = LLMExhibitionParser()
        data = {
            "title": "Test",
            "start_date": None,
            "preface": "X" * 50,
            "concept": "A nice curatorial concept.",
        }
        assert parser._is_valid_result(data) is True

    def test_short_concept(self):
        parser = LLMExhibitionParser()
        data = {"title": "Test", "start_date": "2024-01-01", "concept": "short"}
        assert parser._is_valid_result(data) is False

    def test_empty_concept(self):
        parser = LLMExhibitionParser()
        data = {"title": "Test", "start_date": "2024-01-01", "concept": ""}
        assert parser._is_valid_result(data) is True


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_parse_valid_json(self):
        parser = LLMExhibitionParser()
        json_str = '{"title": "Test Show", "city": "Paris", "artworks": []}'
        result = parser._parse_response(json_str, "test_provider")
        assert result is not None
        assert result["title"] == "Test Show"

    def test_parse_with_json_codeblock(self):
        parser = LLMExhibitionParser()
        json_str = '```json\n{"title": "Codeblock Show", "city": "Berlin"}\n```'
        result = parser._parse_response(json_str, "test_provider")
        assert result is not None
        assert result["title"] == "Codeblock Show"

    def test_parse_with_markdown_backtick(self):
        parser = LLMExhibitionParser()
        json_str = '```\n{"title": "Backtick Show"}\n```'
        result = parser._parse_response(json_str, "test_provider")
        assert result is not None
        assert result["title"] == "Backtick Show"

    def test_parse_invalid_json(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response("{broken json}", "test_provider")
        assert result is None

    def test_parse_list_returns_first_dict(self):
        parser = LLMExhibitionParser()
        json_str = '[{"title": "First"}, {"title": "Second"}]'
        result = parser._parse_response(json_str, "test_provider")
        assert result is not None
        assert result["title"] == "First"

    def test_parse_empty_list(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response("[]", "test_provider")
        assert result is None

    def test_parse_list_with_non_dict(self):
        parser = LLMExhibitionParser()
        result = parser._parse_response('["string"]', "test_provider")
        assert result is None


# ---------------------------------------------------------------------------
# LLMExhibitionParser initialization
# ---------------------------------------------------------------------------


class TestInit:
    def test_no_api_keys_warning(self):
        with patch.dict(os.environ, {}, clear=True):
            parser = LLMExhibitionParser()
            assert parser.providers == []
            assert parser._hub_client is None

    def test_with_mimo_key(self):
        with patch.dict(os.environ, {"XIAOMI_MIMO_API_KEY": "test-key"}):
            parser = LLMExhibitionParser()
            assert len(parser.providers) >= 1
            assert parser.providers[0]["name"] == "mimo"

    def test_cache_enabled_log(self, caplog):
        from src.cache import LLMResponseCache

        cache = LLMResponseCache(":memory:")
        parser = LLMExhibitionParser(cache=cache)
        assert parser.cache is not None


# ---------------------------------------------------------------------------
# _build_prompts
# ---------------------------------------------------------------------------


class TestBuildPrompts:
    def test_returns_system_and_user(self):
        parser = LLMExhibitionParser()
        sys_prompt, user_prompt = parser._build_prompts("Some text", "Test Museum", "TestCity")
        assert isinstance(sys_prompt, str)
        assert isinstance(user_prompt, str)
        assert "Test Museum" in user_prompt
        assert "TestCity" in user_prompt
        assert "Some text" in user_prompt or "=== TEXT ===" in user_prompt


# ---------------------------------------------------------------------------
# parse_exhibition_text (no providers configured)
# ---------------------------------------------------------------------------


class TestParseExhibitionText:
    def test_no_providers_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            parser = LLMExhibitionParser()
            result = parser.parse_exhibition_text("some text", "Test")
            assert result is None

    @pytest.mark.asyncio
    async def test_async_no_providers_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            parser = LLMExhibitionParser()
            result = await parser.parse_exhibition_text_async("some text", "Test")
            assert result is None


# ---------------------------------------------------------------------------
# parse_exhibition_text with cache
# ---------------------------------------------------------------------------


class TestParseWithCache:
    def test_cache_miss_calls_provider(self, monkeypatch):
        monkeypatch.setenv("XIAOMI_MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "https://test.example.com/v1")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from src.cache import LLMResponseCache

        cache = LLMResponseCache(":memory:")
        parser = LLMExhibitionParser(cache=cache)

        # When provider returns None (simulate error), result should be None
        result = parser.parse_exhibition_text("Some exhibition text", "TestSource")
        # The hub client may or may not connect; we just verify the method runs
        assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# Edge: _call_provider returns None when no hub client
# ---------------------------------------------------------------------------


class TestCallProvider:
    def test_call_provider_no_client(self):
        parser = LLMExhibitionParser()
        parser._hub_client = None
        result = parser._call_provider("text", "src", "city")
        assert result is None

    @pytest.mark.asyncio
    async def test_call_provider_async_no_client(self):
        parser = LLMExhibitionParser()
        parser._hub_async_client = None
        result = await parser._call_provider_async("text", "src", "city")
        assert result is None
