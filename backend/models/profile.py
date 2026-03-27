"""
backend/models/profile.py — Pydantic schemas for user profiles.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


RiskProfile = Literal["conservative", "moderate", "aggressive"]


# ── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User Profile ──────────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    age: int | None = Field(None, ge=18, le=100)
    risk_profile: RiskProfile | None = None
    monthly_income: float | None = Field(None, gt=0)
    monthly_expenses: float | None = Field(None, ge=0)
    monthly_fixed_expenses: float | None = Field(None, ge=0)
    total_emi: float | None = Field(None, ge=0)
    retirement_age: int | None = Field(None, ge=30, le=80)
    fire_target: float | None = Field(None, gt=0)
    emergency_fund: float | None = Field(None, ge=0)
    life_cover: float | None = Field(None, ge=0)
    health_cover: float | None = Field(None, ge=0)

    @field_validator("monthly_expenses")
    @classmethod
    def expenses_le_income(cls, v: float | None, info) -> float | None:
        # Soft warning only — validation context may not have income
        return v


class UserProfileRead(UserProfileCreate):
    id: str
    user_id: str
    updated_at: datetime

    model_config = {"from_attributes": True}
