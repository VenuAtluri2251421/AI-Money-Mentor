"""
backend/security.py — Password hashing, JWT creation/verification, auth dependency.

Uses passlib[bcrypt] for hashing and python-jose for JWTs.
Includes an in-memory token blacklist for logout/revocation.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db import get_db
from backend.models.orm import UserORM

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed.decode('ascii')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('ascii'))
    except (ValueError, TypeError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# In-memory blacklist for logout / token revocation.
# Stores JTI (JWT ID) strings. Cleared on server restart, meaning logged-out
# tokens become valid again. If deploying to Supabase with a process manager 
# or multiple workers, this will lead to inconsistent state.
# Acceptable for a hackathon; MUST swap to Redis for production.
_blacklisted_jtis: set[str] = set()


def create_access_token(user_id: str) -> str:
    """Create a JWT with a unique JTI for revocation support."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on any problem."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def blacklist_token(jti: str) -> None:
    """Add a JTI to the blacklist so the token is rejected on future requests."""
    _blacklisted_jtis.add(jti)


def is_blacklisted(jti: str) -> bool:
    return jti in _blacklisted_jtis


# ── FastAPI dependency ────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserORM:
    """
    Extract Bearer token → decode JWT → load user from DB.
    Returns the authenticated UserORM or raises 401.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if user_id is None:
            raise credentials_exc
        if jti and is_blacklisted(jti):
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    result = await db.execute(select(UserORM).where(UserORM.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc

    return user
