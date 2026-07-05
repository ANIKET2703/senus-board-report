"""LLM provider abstraction.

Supports two providers behind one interface:
  * anthropic        - ANTHROPIC_API_KEY (Claude; also required for re-running
                       the vision extraction pipeline)
  * openai-compatible- GITHUB_TOKEN against GitHub Models (free tier), or any
                       OPENAI_API_KEY / OPENAI_BASE_URL endpoint

Commentary and chat work with either. Extraction (pipeline/extract.py) is
Claude-only: it relies on Claude's vision + forced tool-use structured output.
"""
from __future__ import annotations

from app.core.config import get_settings


def provider_available() -> str | None:
    s = get_settings()
    if s.anthropic_api_key:
        return "anthropic"
    if s.github_token or s.openai_api_key:
        return "openai"
    return None


def complete(system: str, user_content: str, max_tokens: int = 1200) -> tuple[str, str]:
    """Returns (text, model_identifier). Raises RuntimeError if no provider."""
    s = get_settings()
    provider = provider_available()
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=s.anthropic_api_key)
        r = client.messages.create(model=s.anthropic_model, max_tokens=max_tokens,
                                   system=system,
                                   messages=[{"role": "user", "content": user_content}])
        return r.content[0].text.strip(), s.anthropic_model
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(base_url=s.openai_base_url,
                        api_key=s.openai_api_key or s.github_token)
        r = client.chat.completions.create(
            model=s.openai_model, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user_content}])
        return (r.choices[0].message.content or "").strip(), s.openai_model
    raise RuntimeError("No LLM provider configured")
