"""Bearer token helpers for gateway-level authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import jwt

from agent.auth.models import User
from agent.auth.security import decode_access_token


@dataclass(frozen=True)
class AuthError(Exception):
    """Raised when gateway bearer authentication fails."""

    status_code: int
    detail: str


def _to_text(value: Any) -> str | None:
    """Convert bytes and strings to normalized header text."""
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    return str(value)


def _header_value(headers: Mapping[Any, Any], name: str) -> str | None:
    """Case-insensitive header lookup for str/bytes based mappings."""
    name_lower = name.lower()

    for key, value in headers.items():
        key_text = _to_text(key)
        if key_text is None or key_text.lower() != name_lower:
            continue

        value_text = _to_text(value)
        return value_text.strip() if value_text else None

    return None


def extract_bearer_token(headers: Mapping[Any, Any]) -> str | None:
    """Extract bearer token from Authorization header."""
    authorization = _header_value(headers, "authorization")
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None

    return token.strip()


def authenticate_bearer_from_headers(
    headers: Mapping[Any, Any], *, session: Any
) -> Any:
    """Validate bearer token and load active user from the database."""
    token = extract_bearer_token(headers)
    if not token:
        raise AuthError(status_code=401, detail="Missing bearer token")

    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise AuthError(status_code=401, detail="Invalid or expired token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise AuthError(status_code=401, detail="Token payload is missing subject")

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise AuthError(status_code=401, detail="Token subject is invalid") from exc

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError(status_code=401, detail="User is inactive or missing")

    return user
