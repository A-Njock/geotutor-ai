"""DeepSeek client for the design brain.

The design brain keeps its own client so the three brains stay independent.
The model is used ONLY for framing, narration and clarification wording;
every number in a solution comes from the deterministic pipeline.
"""

import json
import os

DEEPSEEK_MODEL = "deepseek-chat"

_client = None


def _deepseek():
    global _client
    if _client is None:
        from openai import OpenAI
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        _client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    return _client


class LLMUnavailable(RuntimeError):
    """The language service is unreachable: quota exhausted, rate limited,
    bad key, network or provider outage. Callers show the maintenance
    message and never the underlying error."""


MAINTENANCE_MESSAGE = ("GeoTutor is under maintenance right now. Please "
                       "try again in a few minutes.")


def _call(**kwargs):
    """One place that talks to the provider; every transport failure
    becomes LLMUnavailable so no raw API error can reach a reader."""
    try:
        return _deepseek().chat.completions.create(
            model=DEEPSEEK_MODEL, **kwargs)
    except Exception as e:
        import openai
        transport = isinstance(e, (
            openai.APIError, openai.APIConnectionError,
            openai.APITimeoutError, openai.RateLimitError,
            openai.AuthenticationError, openai.PermissionDeniedError,
            openai.InternalServerError, RuntimeError,
        ))
        # log the real cause server-side for the operator
        print(f"[llm] provider failure ({type(e).__name__}): "
              f"{str(e)[:200]}")
        if transport:
            raise LLMUnavailable(MAINTENANCE_MESSAGE) from e
        raise


def chat_json(system: str, user: str, temperature: float = 0.1,
              max_tokens: int = 3000) -> dict:
    resp = _call(
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return json.loads(resp.choices[0].message.content)


def chat_text(system: str, user: str, temperature: float = 0.2,
              max_tokens: int = 2000) -> str:
    resp = _call(
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# identity scrub: the app is GeoTutor; the underlying provider must never
# surface in reader-facing prose, whatever a jailbreak coaxes the model into
# saying. Prompt rules ask; this filter guarantees.
# ---------------------------------------------------------------------------

import re as _re

_IDENTITY_RE = _re.compile(
    # provider/model names with no legitimate use in geotech prose; bare
    # human names like "Claude" are NOT scrubbed (real authors exist)
    r"deep[\s-]*seek(?:[\s-]*(?:v\d+(?:\.\d+)?|r\d+|chat|coder|llm))?"
    r"|chat[\s-]*gpt|gpt-\d[\w.-]*|openai|anthropic",
    _re.IGNORECASE)


def scrub_identity(text: str) -> str:
    if not text:
        return text
    return _IDENTITY_RE.sub("GeoTutor", text)
