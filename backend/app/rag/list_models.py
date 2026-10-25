"""Print the Gemini model names your API key can see. 
"""

from google import genai

from app.config import settings

if __name__ == "__main__":
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is missing in .env")
    client = genai.Client(api_key=settings.gemini_api_key)
    for model in client.models.list():
        name = (model.name or "").removeprefix("models/")
        if name.startswith("gemini"):
            print(name)