"""
backend/routes/advisor.py — AI Financial Advisor endpoints (Artha / Gemini).

Routes:
  POST /advisor/chat    → Chat with Artha (Gemini)
  POST /advisor/extract → Extract structured profile from natural language
  POST /advisor/explain → Plain-English explanation of a financial insight
  POST /advisor/context → Build formatted user context string
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field


class LenientModel(BaseModel):
    """Drop extra fields silently — React can send metadata without causing 422."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

from ai.advisor import (
    chat_with_advisor,
    extract_profile_from_text,
    explain_insight,
)
from ai.context import build_user_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advisor", tags=["AI Advisor (Artha)"])


# ── /chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(LenientModel):
    message: str = Field(..., min_length=1, description="User's question or message")
    user_context: str = Field(
        "",
        description="Pre-formatted context string from /advisor/context. Leave empty if unavailable.",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description=(
            'Prior conversation turns. '
            'Accepts both Gemini format {"role":"user"|"model"} '
            'and OpenAI format {"role":"user"|"assistant"}.'
        ),
    )


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse, summary="Chat with Artha — AI Finance Advisor")
async def advisor_chat(req: ChatRequest) -> ChatResponse:
    """
    Send a message to Artha. On any API failure returns a graceful HTTP 200 fallback
    — never returns HTTP 500.
    """
    try:
        reply = chat_with_advisor(
            message=req.message,
            user_context=req.user_context,
            conversation_history=req.conversation_history,
        )
    except Exception as exc:
        logger.error("advisor_chat unexpected error: %s", exc)
        reply = "I'm having trouble connecting right now. Please try again."
    return ChatResponse(response=reply)


# ── /extract ──────────────────────────────────────────────────────────────────

class ExtractRequest(LenientModel):
    text: str = Field(..., min_length=1, description="Free-form text describing the user's finances")


@router.post("/extract", summary="Extract Financial Profile from Natural Language")
async def advisor_extract(req: ExtractRequest) -> dict[str, Any]:
    """
    Parse free-form text and return a structured financial profile.
    Returns all-null dict on any failure — never returns HTTP 500.
    """
    try:
        return extract_profile_from_text(req.text)
    except Exception as exc:
        logger.error("advisor_extract unexpected error: %s", exc)
        return {
            "age": None, "monthly_income": None, "monthly_expenses": None,
            "existing_savings": None, "monthly_sip": None, "retirement_age": None,
            "risk_profile": None, "life_events": [], "goals": [],
            "deductions": {
                "sec80c": None, "sec80d": None, "hra_exemption": None, "nps_80ccd": None,
            },
        }


# ── /explain ──────────────────────────────────────────────────────────────────

class ExplainRequest(LenientModel):
    insight_type: str = Field(
        ...,
        description="One of: xirr, health_score, fire_gap, tax_saving, rebalancing",
    )
    data: dict[str, Any] = Field(..., description="Insight-specific data dict")
    user_age: int = Field(..., ge=18, le=100)
    user_income: float = Field(..., ge=0, description="Annual income (₹)")


class ExplainResponse(BaseModel):
    explanation: str


@router.post("/explain", response_model=ExplainResponse, summary="Explain a Financial Insight")
async def advisor_explain(req: ExplainRequest) -> ExplainResponse:
    """
    Generate a plain-English (under 150 words) explanation of a financial insight.
    On any API failure returns a graceful HTTP 200 fallback.
    """
    try:
        text = explain_insight(req.insight_type, req.data, req.user_age, req.user_income)
    except Exception as exc:
        logger.error("advisor_explain unexpected error: %s", exc)
        text = "I'm having trouble generating an explanation right now. Please try again."
    return ExplainResponse(explanation=text)


# ── /context ──────────────────────────────────────────────────────────────────

class ContextRequest(LenientModel):
    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="User profile dict (age, monthly_income, monthly_expenses, etc.)",
    )
    calculated_results: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Calculator outputs. Supported keys: health_score, fire_result, "
            "tax_result, portfolio_xirr."
        ),
    )


class ContextResponse(BaseModel):
    context: str


@router.post(
    "/context",
    response_model=ContextResponse,
    summary="Build Formatted User Context String",
)
async def advisor_context(req: ContextRequest) -> ContextResponse:
    """
    Build a concise (<500 token) context string from the user's profile and
    calculator results. Pass the returned `context` string to /advisor/chat
    or /advisor/explain to ground the AI in the user's actual numbers.
    """
    try:
        ctx = build_user_context(req.profile, req.calculated_results)
    except Exception as exc:
        logger.error("advisor_context error: %s", exc)
        ctx = "User context unavailable."
    return ContextResponse(context=ctx)
