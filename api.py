"""
Groq API helpers for Stealth MCQ Helper.

Contains endpoint building, headers, and response parsing.
Groq uses OpenAI-compatible API format.
"""
import requests
import base64

from config import CONFIG


GROQ_API_BASE = "https://api.groq.com/openai/v1"


def _groq_endpoint() -> str:
    """Build the chat completions endpoint URL."""
    return f"{GROQ_API_BASE}/chat/completions"


def _groq_headers(api_key: str) -> dict:
    """Build headers with API key as Bearer token."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


def _encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string for Groq vision API."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _parse_groq_response(response: requests.Response) -> str:
    """
    Parse a Groq chat completions response.
    Raises RuntimeError with a user-friendly message on failure.
    """
    if response.status_code != 200:
        # Map common HTTP errors to clear messages
        if response.status_code == 400:
            raise RuntimeError(
                "Groq API returned 400 (Bad Request). "
                "The request may be malformed or exceed size limits."
            )
        if response.status_code == 401:
            raise RuntimeError(
                "Groq API returned 401 (Unauthorized). "
                "Check that your API key is valid."
            )
        if response.status_code == 403:
            raise RuntimeError(
                "Groq API returned 403 (Forbidden). "
                "Your API key may lack permission for this model."
            )
        if response.status_code == 404:
            raise RuntimeError(
                "Groq API returned 404 (Not Found). "
                "The model may not exist or is not available."
            )
        if response.status_code == 429:
            raise RuntimeError(
                "Groq API rate limit exceeded (429). Please wait and try again."
            )
        if response.status_code >= 500:
            raise RuntimeError(
                f"Groq API server error ({response.status_code}). "
                "Please try again later."
            )
        # Fallback for other status codes
        try:
            body = response.json()
            detail = body.get("error", {}).get("message", response.text[:200])
        except (ValueError, KeyError):
            detail = response.text[:200]
        raise RuntimeError(
            f"Groq API error {response.status_code}: {detail}"
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("Groq API returned invalid JSON.")

    # Extract content from choices
    try:
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Groq returned no choices (empty response).")
        message = choices[0].get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("Groq returned empty content.")
        return content
    except (KeyError, IndexError, TypeError) as e:
        from utils import log_error
        log_error("Parsing Groq response structure", e)
        raise RuntimeError(
            "Unexpected Groq response format. "
            "The API may have changed or returned an error."
        )