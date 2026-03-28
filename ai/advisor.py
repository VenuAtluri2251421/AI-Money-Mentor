"""
ai/advisor.py

Gemini integration for the Dinero financial advisor. Lazy client init so the
server doesn't fail at startup if GEMINI_API_KEY is missing — it fails at
first request, which gives a clean 200 fallback instead of a 500 crash.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from ai.prompts import (
    SYSTEM_PROMPT_ADVISOR,
    SYSTEM_PROMPT_EXTRACTOR,
    INSIGHT_PROMPTS,
    build_system_prompt,
)
from ai.context import build_context, build_user_context

logger = logging.getLogger(__name__)

# Read at module load time so we pick up any re-configure without restarting
_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

_genai = None


def _get_genai():
    """Lazy init — configure the SDK once and cache it."""
    global _genai
    if _genai is not None:
        return _genai

    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        raise RuntimeError(
            "google-generativeai is not installed. Run: pip install google-generativeai==0.7.2"
        )

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    genai.configure(api_key=api_key)
    _genai = genai
    return _genai


def _make_model(system_instruction: str, temperature: float = 0.4, max_tokens: int = 1000):
    genai = _get_genai()
    return genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=system_instruction,
        generation_config={"max_output_tokens": max_tokens, "temperature": temperature},
    )


_NULL_PROFILE: dict = {
    "age": None, "monthly_income": None, "monthly_expenses": None,
    "existing_savings": None, "monthly_sip": None, "retirement_age": None,
    "risk_profile": None, "life_events": [], "goals": [],
    "deductions": {"sec80c": None, "sec80d": None, "hra_exemption": None, "nps_80ccd": None},
}


def extract_profile_from_text(user_text: str) -> dict:
    """
    Extract a structured financial profile from free-form text.

    Merges system + user content into one prompt because system_instruction
    alone is unreliable for JSON-only output in gemini-2.0 models.
    Three parse attempts before giving up — the model sometimes wraps
    valid JSON in markdown fences, newlines, or extra prose.

    Returns all-null dict on any failure so callers always get a usable shape.
    TODO: Add confidence scoring so the frontend can prompt users to verify
          auto-extracted values before using them in calculations.
    """
    merged_prompt = (
        SYSTEM_PROMPT_EXTRACTOR.strip()
        + "\n\nUser input to extract from:\n"
        + user_text
    )
    try:
        genai = _get_genai()
        model = genai.GenerativeModel(
            model_name=_MODEL_NAME,
            generation_config={"max_output_tokens": 512, "temperature": 0.1},
        )
        response = model.generate_content(merged_prompt)
        raw = response.text.strip()

        # Attempt 1: clean JSON
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Attempt 2: strip markdown fences
        stripped = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # Attempt 3: grab the first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("extract_profile_from_text: all 3 JSON parse attempts failed. Raw: %s", raw[:200])
        parsed = dict(_NULL_PROFILE)

    except Exception as exc:
        # Broad catch intentional — Gemini can raise various google.api_core exceptions
        # (ResourceExhausted, InvalidArgument, etc.) and we never want to 500 on extraction.
        logger.error("extract_profile_from_text failed with %s: %s", type(exc).__name__, exc)
        parsed = dict(_NULL_PROFILE)

    # ── Regex fallback for commonly missed fields ────────────────────────────
    # Even when Gemini returns valid JSON, age and retirement_age are sometimes
    # null. A simple regex over the original user text catches the obvious cases.
    if parsed.get("age") is None:
        age_match = re.search(r"(?:I(?:'| a)m\s+|age\s*[:=]?\s*|^\s*)(\d{1,3})\s*(?:,|\.|$|years?|yr)", user_text, re.IGNORECASE)
        if age_match:
            val = int(age_match.group(1))
            if 10 <= val <= 120:
                parsed["age"] = val

    if parsed.get("retirement_age") is None:
        ret_match = re.search(r"retir\w*\s+(?:at|by|age)?\s*(\d{2})", user_text, re.IGNORECASE)
        if ret_match:
            val = int(ret_match.group(1))
            if 30 <= val <= 90:
                parsed["retirement_age"] = val

    return parsed


def chat_with_advisor(
    message: str,
    user_context: str,
    conversation_history: list[dict],
) -> str:
    """
    Send a message to Dinero and return the reply text.

    Normalises history roles from OpenAI format (assistant) to Gemini format (model)
    so callers don't need to know which SDK we're using.

    Returns a graceful fallback string on any API failure — callers should never
    need to handle exceptions from this function.
    """
    try:
        system = SYSTEM_PROMPT_ADVISOR + "\n\nUser Financial Context:\n" + user_context
        model = _make_model(system, temperature=0.4, max_tokens=1000)

        history = []
        for turn in conversation_history:
            role = "model" if turn.get("role") == "assistant" else turn.get("role", "user")
            history.append({"role": role, "parts": [turn.get("content", "")]})

        chat = model.start_chat(history=history)
        response = chat.send_message(message)
        return response.text

    except Exception as exc:
        logger.error("chat_with_advisor failed with %s: %s", type(exc).__name__, exc)
        return "I'm having trouble connecting right now. Please try again."


def chat_with_advisor_stream(
    message: str,
    user_context: str,
    conversation_history: list[dict],
):
    """
    Streaming version of chat_with_advisor. Yields text chunks as they arrive
    from Gemini. Uses ``stream=True`` on ``send_message``.

    This is a sync generator — the route wraps it in an async SSE response.
    """
    try:
        system = SYSTEM_PROMPT_ADVISOR + "\n\nUser Financial Context:\n" + user_context
        model = _make_model(system, temperature=0.4, max_tokens=1000)

        history = []
        for turn in conversation_history:
            role = "model" if turn.get("role") == "assistant" else turn.get("role", "user")
            history.append({"role": role, "parts": [turn.get("content", "")]})

        chat = model.start_chat(history=history)
        response = chat.send_message(message, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as exc:
        logger.error("chat_with_advisor_stream failed with %s: %s", type(exc).__name__, exc)
        yield "I'm having trouble connecting right now. Please try again."


def explain_insight(
    insight_type: str,
    data: dict,
    user_age: int,
    user_income: float,
) -> str:
    """
    Generate a <150-word plain-English explanation of a financial insight.

    Falls back to the generic advisor prompt if insight_type isn't in INSIGHT_PROMPTS —
    useful when the frontend sends a new insight type before the backend has a template for it.

    Note: user_income is ANNUAL (matches the route's field description).
          All prompt templates have been standardised to say "Annual income".
    """
    system_prompt = INSIGHT_PROMPTS.get(insight_type, SYSTEM_PROMPT_ADVISOR)
    user_message = (
        f"User age: {user_age}, Annual income: ₹{user_income:,.0f}\n"
        f"Insight data: {json.dumps(data, default=str)}"
    )
    try:
        model = _make_model(system_prompt, temperature=0.6, max_tokens=300)
        response = model.generate_content(user_message)
        return response.text

    except Exception as exc:
        logger.error("explain_insight failed (type=%s) with %s: %s", insight_type, type(exc).__name__, exc)
        return "I'm having trouble generating an explanation right now. Please try again."


async def get_advice(
    user_message: str,
    chat_history: list[dict[str, str]] | None = None,
    profile: dict[str, Any] | None = None,
    portfolios: list[dict[str, Any]] | None = None,
    recent_calculations: list[dict[str, Any]] | None = None,
) -> str:
    """Legacy async wrapper kept for backward compatibility with older route handlers."""
    ctx = build_context(profile, portfolios, recent_calculations)
    user_context = (
        f"Profile:\n{ctx.profile_section}\n\n"
        f"Portfolio:\n{ctx.portfolio_section}\n\n"
        f"Calculations:\n{ctx.calculations_section}"
    )
    return chat_with_advisor(
        message=user_message,
        user_context=user_context,
        conversation_history=chat_history or [],
    )
