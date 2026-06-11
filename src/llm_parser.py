import asyncio
import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field, SecretStr, ValidationError

from src.cache import LLMResponseCache, make_cache_key

logger = logging.getLogger("auto_curation.llm_parser")


class ArtworkModel(BaseModel):
    artist_name: str | None = Field(None, description="Name of the artist")
    work_title: str | None = Field(None, description="Title of the artwork")
    work_year: str | None = Field(None, description="Year of creation")
    medium: str | None = Field(None, description="Materials/medium of the artwork")
    dimensions: str | None = Field(None, description="Physical dimensions")
    caption: str | None = Field(None, description="Full caption label information")


class ExhibitionModel(BaseModel):
    title: str = Field(..., description="Exhibition title/theme")
    preface: str | None = Field(None, description="Exhibition introduction/preface")
    concept: str | None = Field(None, description="Curatorial concept/theoretical background")
    preface_en: str | None = Field(
        None, description="Detailed exhibition preface/description in original English"
    )
    concept_en: str | None = Field(
        None, description="Theoretical concept/background in original English"
    )
    biographies: str | None = Field(
        None, description="Detailed biographies of artists and collaborators in original English"
    )
    biographies_cn: str | None = Field(
        None, description="A brief summary/translation of the primary artist biography in Chinese"
    )
    credits: str | None = Field(
        None,
        description="Detailed exhibition credits, curators, production, and special thanks in original English",
    )
    curators: list[str] = Field(default_factory=list, description="List of curators")
    images: list[str] = Field(
        default_factory=list,
        description="List of exhibition image URLs (posters, installation shots, artwork photos)",
    )
    start_date: str | None = Field(None, description="Exhibition start date")
    end_date: str | None = Field(None, description="Exhibition end date")
    location: str | None = Field(None, description="Gallery location within the institution")
    city: str | None = Field(None, description="Host city")
    artworks: list[ArtworkModel] = Field(
        default_factory=list, description="List of exhibited artworks"
    )


class LLMExhibitionParser:
    """Uses auto_hub.llm provider chain with fallback (MiMo -> Gemini -> SiliconFlow) to parse HTML into JSON."""

    def __init__(self, cache: LLMResponseCache | None = None):
        self.providers: list[dict[str, str]] = []
        self.cache = cache
        if self.cache:
            logger.info("LLM response caching enabled.")

        self._hub_client = None
        self._hub_async_client = None

        # Primary: Xiaomi MiMo
        mimo_key = os.getenv("XIAOMI_MIMO_API_KEY")
        if mimo_key:
            self.providers.append(
                {
                    "name": "mimo",
                    "api_key": SecretStr(mimo_key),  # type: ignore[dict-item]
                    "base_url": os.getenv(
                        "MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"
                    ),
                    "model": "mimo-v2.5-pro",
                }
            )

        # Fallback 1: Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.providers.append(
                {
                    "name": "gemini",
                    "api_key": SecretStr(gemini_key),  # type: ignore[dict-item]
                    "base_url": os.getenv(
                        "GEMINI_BASE_URL",
                        "https://generativelanguage.googleapis.com/v1beta/openai/",
                    ),
                    "model": "gemini-2.5-flash",
                }
            )

        # Fallback 2: SiliconFlow
        siliconflow_key = os.getenv("SILICONFLOW_API_KEY")
        if siliconflow_key:
            self.providers.append(
                {
                    "name": "siliconflow",
                    "api_key": SecretStr(siliconflow_key),  # type: ignore[dict-item]
                    "base_url": os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
                    "model": "deepseek-ai/DeepSeek-V3",
                }
            )

        if not self.providers:
            logger.warning("No LLM API keys found in the environment! LLM parsing will fail.")
            return

        # Set up auto_hub provider chain from legacy env var names
        self._setup_auto_hub_chain()

    def _setup_auto_hub_chain(self):
        """Map legacy env var names to auto_hub.llm's AI_PROVIDER_CHAIN format."""
        from auto_hub.llm import AsyncLLMClient, LLMClient
        from auto_hub.llm.provider_chain import reset_provider_chain

        names = []
        for p in self.providers:
            name = p["name"].upper()
            os.environ.setdefault(f"{name}_API_KEY", p["api_key"].get_secret_value())
            os.environ.setdefault(f"{name}_BASE_URL", p["base_url"])
            os.environ.setdefault(f"{name}_MODEL", p["model"])
            names.append(name)

        os.environ.setdefault("AI_PROVIDER_CHAIN", ",".join(names))
        reset_provider_chain()

        self._hub_client = LLMClient(max_retries=3)
        self._hub_async_client = AsyncLLMClient(max_retries=3)

    def _is_valid_result(self, data: dict[str, Any]) -> bool:
        """Heuristic to detect content-filtered or low-quality LLM responses."""
        title = data.get("title")
        if not title or title in ("N/A", "n/a", "NA", "null", ""):
            return False
        has_dates = bool(data.get("start_date") or data.get("end_date"))
        text_content = " ".join(
            filter(
                None,
                [
                    data.get("preface", ""),
                    data.get("concept", ""),
                ],
            )
        )
        if not has_dates and len(text_content.strip()) < 30:
            return False
        concept = data.get("concept", "") or ""
        if concept and len(concept.strip()) < 20:
            return False
        return True

    def _build_prompts(self, text: str, source: str, default_city: str) -> tuple[str, str]:
        """Build system and user prompts for LLM extraction."""
        system_prompt = (
            "You are an expert contemporary art curator and metadata extractor.\n"
            "Your task is to analyze the raw text/markdown extracted from an art museum or biennial's exhibition page, "
            "and extract structured metadata into a precise JSON format.\n\n"
            "Respond ONLY with a valid JSON object matching the requested schema. Do not include markdown code block formatting (like ```json or ```). Only output raw JSON."
        )

        user_prompt = f"""
Institution: {source}
Default City: {default_city}

Analyze the following raw text/markdown and extract the structured metadata.

=== TEXT ===
{text}
=== END TEXT ===
Extract this JSON Schema exactly:
{{
  "title": "Exhibition title or theme (required, string)",
  "preface": "Detailed exhibition preface/introduction/description in Chinese (string or null)",
  "concept": "Specific curatorial concept, theoretical framework, or thematic focus in Chinese. This is the intellectual core of the exhibition — NOT a general description. (string, required — synthesize from available text)",
  "preface_en": "Detailed exhibition preface/introduction/description in original English (string or null)",
  "concept_en": "Specific curatorial concept or theoretical background in original English if mentioned (string or null)",
  "biographies": "Detailed biographies of artists and collaborators in original English, formatted in clean Markdown (string or null)",
  "biographies_cn": "A brief summary/translation of the primary artist biography in Chinese, formatted in clean Markdown (string or null)",
  "credits": "Detailed exhibition credits, curators, collaborator technical credits, production, playtesters, and special thanks in original English, formatted in clean Markdown (string or null)",
  "curators": ["List of curators (array of strings)"],
  "images": ["List of exhibition image URLs — posters, installation shots, artwork photos (array of strings, max 8, or empty array)"],
  "start_date": "Exhibition start date, e.g. 2026-05-23 (string or null)",
  "end_date": "Exhibition end date, e.g. 2026-11-22 (string or null)",
  "location": "Gallery name or gallery number inside the museum, e.g. Floor 3, Gallery 302 (string or null)",
  "city": "Host city (string or null)",
  "artworks": [
    {{
      "artist_name": "Name of the artist (required, string)",
      "work_title": "Title of the artwork in original language/English (required, string)",
      "work_year": "Year of creation (string or null)",
      "medium": "Medium/materials used, e.g. Oil on canvas, video, wood (string or null)",
      "dimensions": "Dimensions of the artwork, e.g. 120 x 200 cm (string or null)",
      "caption": "Full combined caption label string (string or null)"
    }}
  ]
}}

Strict Guidelines:
1. Ensure the 'title' field is always populated. If not clear, synthesize a suitable title from the page main headers.
2. 'preface' vs 'concept' distinction:
   - 'preface': General exhibition description, what visitors see, overview of works and artists.
   - 'concept': The CURATORIAL IDEA — why these works are brought together, the intellectual thread, the critical lens, the historical/thematic argument. If the text contains phrases like 'this exhibition explores', 'through the lens of', 'examining the intersection', 'challenging notions of', 'rethinking', those belong in CONCEPT.
   - CONCEPT must NEVER be null or empty if the page has any substantive exhibition text. Synthesize at least 1-2 sentences capturing the curatorial thesis. Minimum 50 characters.
   - For 'preface_en' and 'concept_en', extract and summarize the high-density exhibition description in English, filtering out generic navigation/ticketing information.
3. For 'artworks', extract concrete works of art explicitly listed or described in the text with their captions. If no specific artworks are listed or described, but the page is a dedicated solo or group exhibition of specific artists, you MUST synthesize at least one artwork entry for each primary artist, setting 'artist_name' to the artist's full name, and 'work_title' to 'Selected Works' (or '代表作品' / '参展作品'), so that the artists are correctly linked to the exhibition in the database. Keep artist names in their original language/spelling.
4. Ensure 'city' is populated, using the Default City if not explicitly found in the text.
5. For 'images', extract up to 8 exhibition image URLs (posters, installation shots, artwork photos). Use absolute URLs. Filter out logos, icons, tracking pixels, and navigation images. Only include .jpg, .jpeg, .png, .webp files. If no suitable images are found, return an empty array [].
6. Extract 'biographies' (biographies of artists and collaborators in original English, keeping each biography relatively concise, around 2-3 sentences per collaborator to highlight their key roles and achievements) and 'credits' (all curators, video game development, playtesters, and special thanks in original English, formatted in clean Markdown lists or sections) exactly as listed on the page. Keep lists of playtesters and special thanks concise if they are extremely long. For 'biographies_cn', translate the primary artist biography into a short, elegant Chinese biography/intro.
"""
        return system_prompt, user_prompt

    def _parse_response(self, content: str, provider_name: str) -> dict[str, Any] | None:
        """Parse and validate raw LLM response content."""
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip("` \n")

        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(
                f"[{provider_name}] Failed to decode LLM response as JSON: {e}. Content: {content[:200]}..."
            )
            return None

        if isinstance(parsed_json, list):
            if parsed_json and isinstance(parsed_json[0], dict):
                parsed_json = parsed_json[0]
            else:
                logger.error(
                    f"[{provider_name}] LLM returned a list instead of a dict: {content[:200]}..."
                )
                return None
        try:
            validated_data = ExhibitionModel(**parsed_json)
        except ValidationError as ve:
            logger.warning(f"[{provider_name}] Pydantic validation failed: {ve}")
            return None
        return validated_data.model_dump()

    def _call_provider(self, text: str, source: str, default_city: str) -> dict[str, Any] | None:
        """Call the LLM via auto_hub.llm (sync) and return parsed data or None."""
        if self._hub_client is None:
            return None

        system_prompt, user_prompt = self._build_prompts(text, source, default_city)

        try:
            content = self._hub_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=None,
                temperature=0.1,
                max_tokens=8192,
            )
            if not content:
                return None
            return self._parse_response(content, "hub")
        except Exception as e:
            logger.warning(f"[LLM] Error in sync call: {e}", exc_info=True)
            return None

    async def _call_provider_async(
        self, text: str, source: str, default_city: str
    ) -> dict[str, Any] | None:
        """Call the LLM via auto_hub.llm (async) and return parsed data or None."""
        if self._hub_async_client is None:
            return None

        system_prompt, user_prompt = self._build_prompts(text, source, default_city)

        try:
            content = await self._hub_async_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=None,
                temperature=0.1,
                max_tokens=8192,
            )
            if not content:
                return None
            return self._parse_response(content, "hub")
        except Exception as e:
            logger.warning(f"[LLM] Error in async call: {e}", exc_info=True)
            return None

    def parse_exhibition_text(
        self, text: str, source: str, default_city: str = ""
    ) -> dict[str, Any] | None:
        """Sends clean text to LLM and returns structured exhibition data.

        Uses auto_hub.llm provider chain (single call, inner chain handles fallback).
        Cache lookup happens before the call; successful results are written back.
        """
        if not self.providers:
            logger.error("Cannot parse text: no LLM providers configured.")
            return None

        cache_key = make_cache_key(f"{source}:{default_city}", text)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.info(f"Cache hit for {source} exhibition text (key: {cache_key[:8]}...)")
                return cached

        result = self._call_provider(text, source, default_city)
        if result and self._is_valid_result(result):
            logger.info(f"[hub] Successfully parsed exhibition '{result.get('title')}'")
            if self.cache:
                self.cache.set(cache_key, f"{source}:{default_city}", source, result)
            return result
        if result:
            logger.warning(f"[hub] Result failed quality check (title={result.get('title')!r}).")

        logger.error("LLM provider failed or returned low-quality results.")
        return None

    async def parse_exhibition_text_async(
        self, text: str, source: str, default_city: str = ""
    ) -> dict[str, Any] | None:
        """Async version: sends cleaned text to LLM with caching support."""
        if not self.providers:
            logger.error("Cannot parse text: no LLM providers configured.")
            return None

        cache_key = make_cache_key(f"{source}:{default_city}", text)
        if self.cache:
            cached = await asyncio.to_thread(self.cache.get, cache_key)
            if cached is not None:
                logger.info(f"Cache hit for {source} exhibition text (key: {cache_key[:8]}...)")
                return cached

        result = await self._call_provider_async(text, source, default_city)
        if result and self._is_valid_result(result):
            logger.info(f"[hub] Successfully parsed exhibition '{result.get('title')}'")
            if self.cache:
                await asyncio.to_thread(
                    self.cache.set, cache_key, f"{source}:{default_city}", source, result
                )
            return result
        if result:
            logger.warning(f"[hub] Result failed quality check (title={result.get('title')!r}).")

        logger.error("LLM provider failed or returned low-quality results.")
        return None
