"""The only file that talks to Gemini."""

import logging
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


FALLBACK_CODES = (404, 429, 503, 504)


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=30_000),  
    )


def _generate(system_instruction: str, prompt: str, json_mode: bool) -> str:
    if not settings.gemini_model:
        raise RuntimeError(
            "GEMINI_MODEL is missing. Run: python -m app.rag.list_models, "
            "then put a model name in .env"
        )

    config_options: dict = {"system_instruction": system_instruction}
    if json_mode:
        config_options["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**config_options)

    models = [settings.gemini_model]
    if (
        settings.gemini_fallback_model
        and settings.gemini_fallback_model != settings.gemini_model
    ):
        models.append(settings.gemini_fallback_model)

    last_error: Exception | None = None
    for model in models:
        try:
            response = _client().models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.text or ""
        except Exception as exc:
            last_error = exc
            code = getattr(exc, "code", None)
            if code not in FALLBACK_CODES:
                raise
            logger.warning("Model %s unavailable (code=%s)", model, code)
    assert last_error is not None
    raise last_error


def generate_json(system_instruction: str, prompt: str) -> str:
    """Ask Gemini for a JSON reply and return it as text."""
    return _generate(system_instruction, prompt, json_mode=True)


def generate_text(system_instruction: str, prompt: str) -> str:
    """Ask Gemini for a plain-text reply."""
    return _generate(system_instruction, prompt, json_mode=False)