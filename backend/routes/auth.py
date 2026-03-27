"""
backend/routes/auth.py — Register, Login, Logout, Me endpoints.

All passwords are bcrypt-hashed. Login returns a JWT.
Logout blacklists the token's JTI so it cannot be reused.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.models.orm import UserORM
from backend.models.profile import UserCreate, UserLogin, UserRead, Token
from backend.security import (
    create_access_token,
    decode_access_token,
    blacklist_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from backend.rate_limit import login_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    import traceback
    try:
        # Check if email already registered
        existing = await db.execute(select(UserORM).where(UserORM.email == body.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = UserORM(
            email=body.email,
            hashed_password=hash_password(body.password),
            full_name=body.full_name,
        )
        db.add(user)
        await db.flush()  # populate user.id before commit
        await db.refresh(user)
        return UserRead.model_validate(user)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("REGISTER ERROR: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT",
    dependencies=[Depends(login_rate_limit)],
)
async def login(
    body: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(select(UserORM).where(UserORM.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently logged-in user",
)
async def me(
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout — blacklist the current JWT",
)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    """Blacklist the JWT's JTI so it can't be reused."""
    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        if jti:
            blacklist_token(jti)
    except Exception:
        pass  # Token is already invalid — that's fine for logout
    return {"detail": "Logged out successfully"}
