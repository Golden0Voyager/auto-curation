import os
import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("auto_curation.llm_parser")

class ArtworkModel(BaseModel):
    artist_name: str = Field(..., description="Name of the artist")
    work_title: str = Field(..., description="Title of the artwork")
    work_year: Optional[str] = Field(None, description="Year of creation")
    medium: Optional[str] = Field(None, description="Materials/medium of the artwork")
    dimensions: Optional[str] = Field(None, description="Physical dimensions")
    caption: Optional[str] = Field(None, description="Full caption label information")

class ExhibitionModel(BaseModel):
    title: str = Field(..., description="Exhibition title/theme")
    preface: Optional[str] = Field(None, description="Exhibition introduction/preface")
    concept: Optional[str] = Field(None, description="Curatorial concept/theoretical background")
    curators: List[str] = Field(default_factory=list, description="List of curators")
    start_date: Optional[str] = Field(None, description="Exhibition start date")
    end_date: Optional[str] = Field(None, description="Exhibition end date")
    location: Optional[str] = Field(None, description="Gallery location within the institution")
    city: Optional[str] = Field(None, description="Host city")
    artworks: List[ArtworkModel] = Field(default_factory=list, description="List of exhibited artworks")

class LLMExhibitionParser:
    """Uses Gemini API via OpenAI-compatible endpoint to parse cleaned HTML text into structured JSON."""
    
    def __init__(self):
        # Primary: SenseNova (free DeepSeek models)
        self.api_key = os.getenv("SENSENOVA_API_KEY")
        self.base_url = os.getenv("SENSENOVA_BASE_URL", "https://api.sensenova.cn/compatible-mode/v2")
        self.provider = "sensenova"

        # Fallback 1: Gemini
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
            self.provider = "gemini"
            logger.info("SENSENOVA_API_KEY not found, falling back to Gemini.")

        # Fallback 2: SiliconFlow
        if not self.api_key:
            self.api_key = os.getenv("SILICONFLOW_API_KEY")
            self.base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
            self.provider = "siliconflow"
            logger.info("GEMINI_API_KEY not found, falling back to SiliconFlow.")

        if not self.api_key:
            logger.warning("No LLM API keys found in the environment! LLM parsing will fail.")

    def parse_exhibition_text(self, text: str, source: str, default_city: str = "") -> Optional[Dict[str, Any]]:
        """Sends clean text to LLM and returns structured exhibition data.
        
        Args:
            text: The cleaned, high-density text content of the exhibition page.
            source: The name of the institution (e.g. 'MoMA').
            default_city: Default city if not found in the text.
            
        Returns:
            A dictionary matching the ExhibitionModel schema, or None if failed.
        """
        if not self.api_key:
            logger.error("Cannot parse text: API key is missing.")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
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
2. For 'preface' and 'concept', translate or summarize into fluent and professional Chinese art curatorial style.
3. For 'artworks', only extract concrete works of art explicitly listed or described in the text with their captions. If no specific artworks are listed, leave 'artworks' as an empty array []. Keep artist names and artwork titles in their original language (usually English/French/German/Italian) or original spelling.
4. Ensure 'city' is populated, using the Default City if not explicitly found in the text.
"""

        # Choose the right model depending on the active provider
        if self.provider == "sensenova":
            model_name = "DeepSeek-V3-1"
        elif self.provider == "gemini":
            model_name = "gemini-2.5-flash"
        else:
            model_name = "deepseek-ai/DeepSeek-V3"  # siliconflow fallback
            
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        
        try:
            logger.info(f"Sending LLM parsing request to {model_name}...")
            with httpx.Client(timeout=60.0) as client:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Strip markdown code blocks if the model ignored our request
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip("` \n")
                
                # Parse and validate with Pydantic
                parsed_json = json.loads(content)
                validated_data = ExhibitionModel(**parsed_json)
                
                # Convert back to standard dict
                return validated_data.model_dump()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling LLM API: {e.response.status_code} - {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM response as JSON. Content was: {content[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Error parsing exhibition text: {e}", exc_info=True)
            return None
