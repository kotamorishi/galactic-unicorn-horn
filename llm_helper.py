"""LLM integration for natural event text formatting via Ollama API (LLMHAT)."""

import logging

import requests

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = (
    "You are a concise calendar assistant for an LED display. "
    "Convert calendar event info into a short, natural Japanese sentence. "
    "Rules:\n"
    "- Output ONLY the formatted sentence, nothing else\n"
    "- Keep it under 40 characters\n"
    "- Use simple, friendly language\n"
    "- Include the start time naturally\n"
    "- If end time is given, you may omit it unless the duration matters\n"
    "- Do not add greetings or extra commentary"
)


def detect_ollama(ollama_url=None):
    """Check if Ollama API is reachable.

    Returns the base URL if available, None otherwise.
    """
    url = ollama_url or DEFAULT_OLLAMA_URL
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            logger.info("Ollama detected at %s", url)
            return url
    except Exception:
        logger.info("Ollama not available at %s", url)
    return None


def list_models(ollama_url):
    """List available models from Ollama."""
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        logger.info("Available models: %s", models)
        return models
    except Exception:
        logger.exception("Failed to list Ollama models")
        return []


def select_model(ollama_url, preferred_model=None):
    """Select the best available model.

    Priority:
    1. User-configured model (if available)
    2. First available model from the list
    """
    models = list_models(ollama_url)
    if not models:
        return None

    if preferred_model:
        for model in models:
            if preferred_model in model:
                logger.info("Using preferred model: %s", model)
                return model

    # Fall back to first available model
    logger.info("Using first available model: %s", models[0])
    return models[0]


def format_event_with_llm(ollama_url, model, event_text):
    """Format event text using LLM for natural language output.

    Args:
        ollama_url: Ollama API base URL
        model: Model name to use
        event_text: Raw event text (e.g. "09:00-10:00 Meeting")

    Returns:
        Formatted text string, or None if LLM call fails.
    """
    try:
        resp = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": event_text},
                ],
                "stream": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data["message"]["content"].strip()
        # Sanity check: reject overly long responses
        if len(result) > 80:
            logger.warning("LLM response too long (%d chars), using original", len(result))
            return None
        logger.info("LLM formatted: '%s' -> '%s'", event_text, result)
        return result
    except Exception:
        logger.exception("LLM formatting failed for: %s", event_text)
        return None
