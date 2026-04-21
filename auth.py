"""LangGraph auth handlers that trust the upstream gateway."""

from __future__ import annotations

import hmac
import os
from typing import Any

from langgraph_sdk import Auth

my_auth = Auth()

GATEWAY_UPSTREAM_SECRET = os.environ.get('GATEWAY_UPSTREAM_SECRET', '')


def _get_text_header(headers: dict[bytes, bytes], name: str) -> str | None:
    value = headers.get(name.encode('utf-8'))
    if value is None:
        return None
    if isinstance(value, bytes):
        text = value.decode('utf-8').strip()
    else:
        text = str(value).strip()
    return text or None


@my_auth.authenticate
async def authenticate(headers: dict[bytes, bytes]) -> Auth.types.MinimalUserDict:
    """Authenticate requests that come through the gateway."""
    received_secret = _get_text_header(headers, 'x-gateway-upstream-secret')
    if not GATEWAY_UPSTREAM_SECRET:
        raise Auth.exceptions.HTTPException(
            status_code=500,
            detail='Missing GATEWAY_UPSTREAM_SECRET configuration',
        )
    if received_secret is None or not hmac.compare_digest(
        received_secret, GATEWAY_UPSTREAM_SECRET
    ):
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail='Invalid gateway credentials',
        )

    user_id = _get_text_header(headers, 'x-authenticated-user-id')
    email = _get_text_header(headers, 'x-authenticated-user-email')
    if user_id is None:
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail='Missing authenticated identity headers',
        )

    user: Auth.types.MinimalUserDict = {'identity': user_id, 'is_authenticated': True}
    if email is not None:
        user['display_name'] = email
    return user


@my_auth.on
async def enforce_owner_scope(
    ctx: Auth.types.AuthContext, value: dict[str, Any]
) -> Auth.types.FilterType:
    """Persist owner metadata and restrict access to owner-scoped resources."""
    filters = {'owner': ctx.user.identity}
    metadata = value.setdefault('metadata', {})
    if isinstance(metadata, dict):
        metadata.update(filters)
    return filters
