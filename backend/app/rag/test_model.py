"""Check whether a Gemini model works with your key. 
"""

import sys

from google import genai

from app.config import settings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m app.rag.test_model <model-name>")
    model = sys.argv[1]
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = client.models.generate_content(
            model=model, contents="Reply with the single word: OK"
        )
        print(f"{model} -> {(response.text or '').strip()}")
    except Exception as exc:
        print(f"{model} -> FAILED (code {getattr(exc, 'code', None)}, {type(exc).__name__})")