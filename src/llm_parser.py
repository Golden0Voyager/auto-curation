import os
import json
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, SecretStr
from src.cache import LLMResponseCache, make_cache_key

logger = logging.getLogger("auto_curation.llm_parser")

class ArtworkModel(BaseModel):
    artist_name: Optional[str] = Field(None, description="Name of the artist")
    work_title: Optional[str] = Field(None, description="Title of the artwork")
    work_year: Optional[str] = Field(None, description="Year of creation")
    medium: Optional[str] = Field(None, description="Materials/medium of the artwork")
    dimensions: Optional[str] = Field(None, description="Physical dimensions")
    caption: Optional[str] = Field(None, description="Full caption label information")

class ExhibitionModel(BaseModel):
    title: str = Field(..., description="Exhibition title/theme")
    preface: Optional[str] = Field(None, description="Exhibition introduction/preface")
    concept: Optional[str] = Field(None, description="Curatorial concept/theoretical background")
    preface_en: Optional[str] = Field(None, description="Detailed exhibition preface/description in original English")
    concept_en: Optional[str] = Field(None, description="Theoretical concept/background in original English")
    biographies: Optional[str] = Field(None, description="Detailed biographies of artists and collaborators in original English")
    biographies_cn: Optional[str] = Field(None, description="A brief summary/translation of the primary artist biography in Chinese")
    credits: Optional[str] = Field(None, description="Detailed exhibition credits, curators, production, and special thanks in original English")
    curators: List[str] = Field(default_factory=list, description="List of curators")
    start_date: Optional[str] = Field(None, description="Exhibition start date")
    end_date: Optional[str] = Field(None, description="Exhibition end date")
    location: Optional[str] = Field(None, description="Gallery location within the institution")
    city: Optional[str] = Field(None, description="Host city")
    artworks: List[ArtworkModel] = Field(default_factory=list, description="List of exhibited artworks")


class LLMExhibitionParser:
    """Uses multiple LLM providers (SenseNova -> Gemini -> SiliconFlow) to parse cleaned HTML text into structured JSON.

    When the primary provider returns low-quality results (e.g., content-filtered N/A responses),
    automatically falls back to the next available provider.
    """

    def __init__(self, cache: Optional[LLMResponseCache] = None):
        self.providers: List[Dict[str, str]] = []
        self.cache = cache
        if self.cache:
            logger.info("LLM response caching enabled.")

        # Primary: SenseNova (free DeepSeek models)
        sensenova_key = os.getenv("SENSENOVA_API_KEY")
        if sensenova_key:
            self.providers.append({
                "name": "sensenova",
                "api_key": SecretStr(sensenova_key),
                "base_url": os.getenv("SENSENOVA_BASE_URL", "https://api.sensenova.cn/compatible-mode/v2"),
                "model": "DeepSeek-V3-1"
            })

        # Fallback 1: Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.providers.append({
                "name": "gemini",
                "api_key": SecretStr(gemini_key),
                "base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                "model": "gemini-2.5-flash"
            })

        # Fallback 2: SiliconFlow
        siliconflow_key = os.getenv("SILICONFLOW_API_KEY")
        if siliconflow_key:
            self.providers.append({
                "name": "siliconflow",
                "api_key": SecretStr(siliconflow_key),
                "base_url": os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
                "model": "deepseek-ai/DeepSeek-V3"
            })

        if not self.providers:
            logger.warning("No LLM API keys found in the environment! LLM parsing will fail.")

    def _is_valid_result(self, data: Dict[str, Any]) -> bool:
        """Heuristic to detect content-filtered or low-quality LLM responses."""
        title = data.get("title")
        if not title or title in ("N/A", "n/a", "NA", "null", ""):
            return False
        # If both dates are missing AND text content is negligible, treat as filtered
        has_dates = bool(data.get("start_date") or data.get("end_date"))
        text_content = " ".join(filter(None, [
            data.get("preface", ""),
            data.get("concept", ""),
        ]))
        if not has_dates and len(text_content.strip()) < 30:
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
  "concept": "Specific curatorial concept or theoretical background in Chinese if mentioned (string or null)",
  "preface_en": "Detailed exhibition preface/introduction/description in original English (string or null)",
  "concept_en": "Specific curatorial concept or theoretical background in original English if mentioned (string or null)",
  "biographies": "Detailed biographies of artists and collaborators in original English, formatted in clean Markdown (string or null)",
  "biographies_cn": "A brief summary/translation of the primary artist biography in Chinese, formatted in clean Markdown (string or null)",
  "credits": "Detailed exhibition credits, curators, collaborator technical credits, production, playtesters, and special thanks in original English, formatted in clean Markdown (string or null)",
  "curators": ["List of curators (array of strings)"],
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
2. For 'preface' and 'concept', translate or summarize into fluent and professional Chinese art curatorial style. For 'preface_en' and 'concept_en', extract and summarize the high-density exhibition description in English, filtering out generic navigation/ticketing information.
3. For 'artworks', extract concrete works of art explicitly listed or described in the text with their captions. If no specific artworks are listed or described, but the page is a dedicated solo or group exhibition of specific artists, you MUST synthesize at least one artwork entry for each primary artist, setting 'artist_name' to the artist's full name, and 'work_title' to 'Selected Works' (or '代表作品' / '参展作品'), so that the artists are correctly linked to the exhibition in the database. Keep artist names in their original language/spelling.
4. Ensure 'city' is populated, using the Default City if not explicitly found in the text.
5. Extract 'biographies' (biographies of artists and collaborators in original English, keeping each biography relatively concise, around 2-3 sentences per collaborator to highlight their key roles and achievements) and 'credits' (all curators, video game development, playtesters, and special thanks in original English, formatted in clean Markdown lists or sections) exactly as listed on the page. Keep lists of playtesters and special thanks concise if they are extremely long. For 'biographies_cn', translate the primary artist biography into a short, elegant Chinese biography/intro.
"""
        return system_prompt, user_prompt

    def _parse_response(self, content: str, provider_name: str) -> Optional[Dict[str, Any]]:
        """Parse and validate raw LLM response content."""
        # Strip markdown code blocks if the model ignored our request
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip("` \n")

        parsed_json = json.loads(content)
        if isinstance(parsed_json, list):
            if parsed_json and isinstance(parsed_json[0], dict):
                parsed_json = parsed_json[0]
            else:
                logger.error(f"[{provider_name}] LLM returned a list instead of a dict: {content[:200]}...")
                return None
        validated_data = ExhibitionModel(**parsed_json)
        return validated_data.model_dump()

    def _call_provider(
        self,
        text: str,
        source: str,
        default_city: str,
        provider: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Send a single request to one provider and return parsed data or None."""
        api_key = provider["api_key"]
        base_url = provider["base_url"]
        model_name = provider["model"]
        provider_name = provider["name"]

        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json"
        }

        system_prompt, user_prompt = self._build_prompts(text, source, default_city)

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"}
        }

        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        content = ""

        try:
            logger.info(f"[{provider_name}] Sending LLM parsing request ({model_name})...")
            with httpx.Client(timeout=60.0) as client:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                return self._parse_response(content, provider_name)

        except httpx.HTTPStatusError as e:
            logger.warning(f"[{provider_name}] HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"[{provider_name}] JSON decode error. Content: {content[:200]}...")
            return None
        except Exception as e:
            logger.warning(f"[{provider_name}] Error: {e}", exc_info=False)
            return None

    async def _call_provider_async(
        self,
        text: str,
        source: str,
        default_city: str,
        provider: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Async version: send a single request to one provider."""
        api_key = provider["api_key"]
        base_url = provider["base_url"]
        model_name = provider["model"]
        provider_name = provider["name"]

        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json"
        }

        system_prompt, user_prompt = self._build_prompts(text, source, default_city)

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"}
        }

        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        content = ""

        try:
            logger.info(f"[{provider_name}] Sending async LLM parsing request ({model_name})...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                return self._parse_response(content, provider_name)

        except httpx.HTTPStatusError as e:
            logger.warning(f"[{provider_name}] HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"[{provider_name}] JSON decode error. Content: {content[:200]}...")
            return None
        except Exception as e:
            logger.warning(f"[{provider_name}] Error: {e}", exc_info=False)
            return None

    def parse_exhibition_text(self, text: str, source: str, default_city: str = "") -> Optional[Dict[str, Any]]:
        """Sends clean text to LLM and returns structured exhibition data.

        Iterates over all configured providers; when a provider returns a low-quality
        (likely content-filtered) response, automatically tries the next one.
        Cache lookup happens before the first provider call; successful results are
        written back to the cache.

        Args:
            text: The cleaned, high-density text content of the exhibition page.
            source: The name of the institution (e.g. 'MoMA').
            default_city: Default city if not found in the text.

        Returns:
            A dictionary matching the ExhibitionModel schema, or None if all providers failed.
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

        for provider in self.providers:
            result = self._call_provider(text, source, default_city, provider)
            if result and self._is_valid_result(result):
                logger.info(f"[{provider['name']}] Successfully parsed exhibition '{result.get('title')}'")
                if self.cache:
                    self.cache.set(cache_key, f"{source}:{default_city}", source, result)
                return result
            if result:
                logger.warning(
                    f"[{provider['name']}] Result failed quality check (title={result.get('title')!r}). "
                    "Trying next provider..."
                )

        logger.error("All LLM providers failed or returned low-quality results.")
        return None

    async def parse_exhibition_text_async(self, text: str, source: str, default_city: str = "") -> Optional[Dict[str, Any]]:
        """Asynchronous version: sends cleaned text to LLM with caching support."""
        if not self.providers:
            logger.error("Cannot parse text: no LLM providers configured.")
            return None

        cache_key = make_cache_key(f"{source}:{default_city}", text)
        if self.cache:
            cached = await asyncio.to_thread(self.cache.get, cache_key)
            if cached is not None:
                logger.info(f"Cache hit for {source} exhibition text (key: {cache_key[:8]}...)")
                return cached

        for provider in self.providers:
            result = await self._call_provider_async(text, source, default_city, provider)
            if result and self._is_valid_result(result):
                logger.info(f"[{provider['name']}] Successfully parsed exhibition '{result.get('title')}'")
                if self.cache:
                    await asyncio.to_thread(self.cache.set, cache_key, f"{source}:{default_city}", source, result)
                return result
            if result:
                logger.warning(
                    f"[{provider['name']}] Result failed quality check (title={result.get('title')!r}). "
                    "Trying next provider..."
                )

        logger.error("All LLM providers failed or returned low-quality results.")
        return None
