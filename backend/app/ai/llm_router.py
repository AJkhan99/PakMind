"""Multi-LLM router — Google Gemini (free), Groq (free), OpenAI (paid).

Default setup (100% free):
  - Primary LLM: Google Gemini (free tier) via REST API
  - Verification LLM: Groq Llama (free tier) via OpenAI-compatible API
  - Fallback chain: Google -> Groq -> OpenAI (if configured)

Domain-specific prompt builders (generate_answer, verify_answer, etc.)
live in each domain package (app.guide.prompts, app.watch.prompts, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_openai_client = None
_groq_client = None

_GOOGLE_CHAT_URL = "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=get_settings().openai_api_key)
    return _openai_client


def _get_groq():
    global _groq_client
    if _groq_client is None:
        from openai import OpenAI
        settings = get_settings()
        _groq_client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq_client


# ---------------------------------------------------------------------------
# Low-level LLM calls
# ---------------------------------------------------------------------------

def _call_google(messages: list[dict[str, str]], json_mode: bool = True) -> str:
    """Call Google Gemini (FREE tier) via REST API. Rotates API keys on 429."""
    settings = get_settings()
    url = _GOOGLE_CHAT_URL.format(model=settings.gemini_model)

    system_instruction = ""
    user_parts: list[str] = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            user_parts.append(msg["content"])

    contents = [{"parts": [{"text": "\n\n".join(user_parts)}]}]
    payload: dict[str, Any] = {"contents": contents}

    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    generation_config: dict[str, Any] = {"temperature": 0.2}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    payload["generationConfig"] = generation_config

    quota_exhausted = False
    for api_key in settings.google_api_keys():
        resp = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=60,
        )
        if resp.status_code == 429:
            quota_exhausted = True
            continue  # try the next configured key
        if resp.status_code != 200:
            raise RuntimeError(f"Google Gemini error ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {json.dumps(data)[:200]}")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError(f"Gemini returned empty parts: {json.dumps(data)[:200]}")
        return parts[0].get("text", "")

    if quota_exhausted:
        raise RuntimeError("Google Gemini quota exceeded (all configured keys)")
    raise RuntimeError("Google Gemini: no usable API keys configured")


def _call_groq(messages: list[dict[str, str]], json_mode: bool = True) -> str:
    """Call Groq Llama (FREE tier) — uses OpenAI-compatible API."""
    settings = get_settings()
    client = _get_groq()
    kwargs: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        # Groq validates JSON server-side and rejects outputs like a bare
        # refusal sentence (code "json_validate_failed"). Recover using the
        # model's intended text from failed_generation instead of failing.
        body = getattr(exc, "body", None)
        err = body.get("error") or {} if isinstance(body, dict) else {}
        failed_gen = err.get("failed_generation") if err.get("code") == "json_validate_failed" else None
        if not failed_gen:
            raise
        text = str(failed_gen).strip()
        # If the intended output is already valid JSON, pass it through;
        # otherwise wrap it as an answer (e.g. the no-results refusal sentence).
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            logger.warning("Groq JSON validation failed — wrapping intended text as answer")
            return json.dumps({"answer": text})
    return response.choices[0].message.content or ""


def _call_openai(messages: list[dict[str, str]], json_mode: bool = True) -> str:
    """Call OpenAI chat completions (PAID)."""
    settings = get_settings()
    client = _get_openai()
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.2,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


_PROVIDERS = {
    "google": _call_google,
    "groq": _call_groq,
    "openai": _call_openai,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_llm(messages: list[dict[str, str]], provider: str | None = None, json_mode: bool = True) -> str:
    """Call an LLM by provider name. Falls back through the chain on failure."""
    settings = get_settings()
    primary = provider or settings.primary_llm

    all_providers = ["google", "groq", "openai"]
    providers = [primary] + [p for p in all_providers if p != primary]

    for prov in providers:
        if prov == "openai" and not settings.openai_api_key:
            continue
        if prov == "groq" and (not settings.groq_api_key or settings.groq_api_key.startswith("your_")):
            continue
        if prov == "google" and (not settings.google_api_key or settings.google_api_key.startswith("your_")):
            continue

        try:
            return _PROVIDERS[prov](messages, json_mode=json_mode)
        except Exception as exc:
            logger.warning("LLM provider '%s' failed: %s — trying fallback", prov, exc)
            continue

    raise RuntimeError("All LLM providers failed. Check your API keys in .env")


def call_llm_json(messages: list[dict[str, str]], provider: str | None = None) -> dict[str, Any]:
    """Call an LLM and parse the response as JSON."""
    raw = call_llm(messages, provider=provider, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM returned non-JSON response: %s", raw[:200])
        return {"error": "Failed to parse LLM response", "raw": raw[:500]}


# ---------------------------------------------------------------------------
# Grounded web search (FREE — 5,000 searches/month on the free tier)
# ---------------------------------------------------------------------------

def call_google_grounded(query: str, system_instruction: str = "") -> tuple[str, list[dict[str, Any]]]:
    """Call Gemini with the google_search tool and return (text, web_sources).

    Web sources are extracted from the response's groundingMetadata
    (groundingChunks), so they are the actual pages the model searched.
    """
    settings = get_settings()
    url = _GOOGLE_CHAT_URL.format(model=settings.gemini_model)

    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],
        # JSON responseMimeType is not supported together with tools — the
        # prompt asks for JSON instead and it is parsed from plain text.
        "generationConfig": {"temperature": 0.2},
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    quota_exhausted = False
    for api_key in settings.google_api_keys():
        resp = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=90,
        )
        if resp.status_code == 429:
            quota_exhausted = True
            continue  # try the next configured key
        if resp.status_code != 200:
            raise RuntimeError(f"Grounded Gemini error ({resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Grounded Gemini returned no candidates: {json.dumps(data)[:200]}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        web_sources: list[dict[str, Any]] = []
        grounding = candidates[0].get("groundingMetadata", {}) or {}
        for chunk in grounding.get("groundingChunks", []) or []:
            web = chunk.get("web", {}) or {}
            if web.get("uri"):
                web_sources.append({
                    "title": web.get("title") or web.get("uri"),
                    "url": web["uri"],
                })

        return text, web_sources

    if quota_exhausted:
        raise RuntimeError("Grounded Gemini quota exceeded (all configured keys)")
    raise RuntimeError("Grounded Gemini: no usable API keys configured")
