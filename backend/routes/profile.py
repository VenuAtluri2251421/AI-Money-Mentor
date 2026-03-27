"""
backend/routes/profile.py — User profile CRUD (protected).

GET  /profile  → read current user's financial profile
PUT  /profile  → create or update (upsert) the profile
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.models.orm import UserORM, UserProfileORM
from backend.models.profile import UserProfileCreate, UserProfileRead
from backend.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["User Profile"])


@router.get(
    "",
    response_model=UserProfileRead,
    summary="Get your financial profile",
)
async def get_profile(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileRead:
    result = await db.execute(
        select(UserProfileORM).where(UserProfileORM.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Use PUT /profile to create one.",
        )
    return UserProfileRead.model_validate(profile)


@router.put(
    "",
    response_model=UserProfileRead,
    summary="Create or update your financial profile",
)
async def upsert_profile(
    body: UserProfileCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileRead:
    result = await db.execute(
        select(UserProfileORM).where(UserProfileORM.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        # Update existing
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
    else:
        # Create new
        profile = UserProfileORM(
            user_id=current_user.id,
            **body.model_dump(exclude_unset=True),
        )
        db.add(profile)

    await db.flush()
    await db.refresh(profile)
    return UserProfileRead.model_validate(profile)
