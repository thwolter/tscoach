"""HTTP routes for login and session introspection."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agent.auth.config import settings
from agent.auth.db import get_session
from agent.auth.dependencies import AuthContext, get_auth_context
from agent.auth.models import User
from agent.auth.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Credential payload accepted by the login endpoint."""

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    """JWT bearer token response payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    """Current authenticated user profile response."""

    user_id: int
    username: str
    is_admin: bool
    panels: list[str]


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_session)],
) -> TokenResponse:
    """Authenticate with username/password and return a user-specific JWT."""
    statement = (
        select(User)
        .options(selectinload(User.panel_access))
        .where(User.username == payload.username)
        .limit(1)
    )
    user = session.execute(statement).scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    panels = [entry.panel_key for entry in user.panel_access]
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        panels=panels,
    )

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=MeResponse)
def me(auth: Annotated[AuthContext, Depends(get_auth_context)]) -> MeResponse:
    """Return the current JWT subject profile."""
    return MeResponse(
        user_id=auth.user_id,
        username=auth.username,
        is_admin=auth.is_admin,
        panels=list(auth.panels),
    )


@router.get("/panels/{panel_key}", response_model=MeResponse)
def check_panel_access(
    panel_key: str,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> MeResponse:
    """Check whether the current user can access the requested panel."""
    if not (auth.is_admin or panel_key in auth.panels):
        raise HTTPException(
            status_code=403, detail=f"Missing panel access: {panel_key}"
        )

    return MeResponse(
        user_id=auth.user_id,
        username=auth.username,
        is_admin=auth.is_admin,
        panels=list(auth.panels),
    )
