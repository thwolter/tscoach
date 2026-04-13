"""Core API-key auth primitives that can be reused across projects."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any, Mapping

from agent.security.store import APIKeyRecord, APIKeyStore

API_KEY_PREFIX = "sk-"


@dataclass(frozen=True)
class APIKeyAuthError(Exception):
    """Raised when API key authentication fails."""

    status_code: int
    detail: str


def generate_api_key(token_bytes: int = 32) -> str:
    """Generate a random API key token using the sk- prefix convention."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(token_bytes)}"


def hash_api_key(api_key: str, *, pepper: str) -> str:
    """Hash an API key with an HMAC pepper for storage-safe validation."""
    if not pepper:
        raise ValueError("Missing API key pepper")

    return hmac.new(
        pepper.encode("utf-8"),
        api_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


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


def extract_api_key(headers: Mapping[Any, Any]) -> str | None:
    """Extract API key from Authorization Bearer or X-API-Key headers."""
    authorization = _header_value(headers, "authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token.strip():
            return token.strip()

    x_api_key = _header_value(headers, "x-api-key")
    if x_api_key:
        return x_api_key.strip()

    return None


async def validate_api_key_from_headers(
    headers: Mapping[Any, Any],
    *,
    store: APIKeyStore,
    pepper: str,
) -> APIKeyRecord:
    """Validate API key from request headers and return its key record."""
    if not pepper:
        raise APIKeyAuthError(
            status_code=500,
            detail="Server auth is misconfigured: missing AGENT_API_KEY_PEPPER",
        )

    api_key = extract_api_key(headers)
    if not api_key:
        raise APIKeyAuthError(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key, pepper=pepper)
    key_record = await store.get_by_hash(key_hash)

    if key_record is None or not key_record.is_active:
        raise APIKeyAuthError(status_code=403, detail="Invalid API key")

    return key_record
