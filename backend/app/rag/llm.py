"""The only file that talks to Gemini."""

from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=30_000),  # 30 seconds, in milliseconds
    )


def generate_json(system_instruction: str, prompt: str) -> str:
    """Ask Gemini for a JSON reply and return it as text."""
    if not settings.gemini_model:
        raise RuntimeError(
            "GEMINI_MODEL is missing. Run: python -m app.rag.list_models, "
            "then put a model name in .env"
        )
    response = _client().models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    return response.text or ""