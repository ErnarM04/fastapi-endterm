import os
from libretranslate import LibreTranslate


# Point to your LibreTranslate server; change if you host your own instance.
# You can also override via the LT_URL env var.
LT_URL = os.getenv("LT_URL", "https://libretranslate.de")
# Optional API key if your instance requires it (set LT_API_KEY env var).
LT_API_KEY = os.getenv("LT_API_KEY")

# The official LibreTranslate client
lt = LibreTranslate(url=LT_URL, api_key=LT_API_KEY)


def translate_text(text: str, source: str = "en", target: str = "es") -> str:
    """
    Translate text from source language to target language using LibreTranslate.
    Language codes: en, es, fr, de, it, pt, ru, ar, zh, ja, etc.
    Raises a RuntimeError with details if the translation fails.
    """
    try:
        return lt.translate(text, source=source, target=target)
    except Exception as exc:
        # Surface any error with context (network issues, bad URL, rate limits, etc.)
        raise RuntimeError(f"LibreTranslate translation failed: {exc}") from exc


if __name__ == "__main__":
    original = "Hello world, how are you?"
    try:
        translated = translate_text(original, source="en", target="es")
        print(f"Original:   {original}")
        print(f"Translated: {translated}")
    except Exception as exc:
        print(f"Translation failed: {exc}")

