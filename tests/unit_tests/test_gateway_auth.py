from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

AUTH_PATH = Path(__file__).parents[2] / 'auth.py'
AUTH_SPEC = importlib.util.spec_from_file_location('tscoach_gateway_auth', AUTH_PATH)
assert AUTH_SPEC is not None
assert AUTH_SPEC.loader is not None
auth = importlib.util.module_from_spec(AUTH_SPEC)
AUTH_SPEC.loader.exec_module(auth)

_get_text_header = auth._get_text_header
authenticate = auth.authenticate
enforce_owner_scope = auth.enforce_owner_scope


class DummyUser:
    identity = 'user-123'


class DummyContext:
    user = DummyUser()


def test_get_text_header_decodes_and_strips_bytes() -> None:
    headers = {b'x-authenticated-user-id': b' user-123 '}

    assert _get_text_header(headers, 'x-authenticated-user-id') == 'user-123'


@pytest.mark.anyio
async def test_authenticate_accepts_gateway_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, 'GATEWAY_UPSTREAM_SECRET', 'shared-secret')
    headers = {
        b'x-gateway-upstream-secret': b'shared-secret',
        b'x-authenticated-user-id': b'user-123',
        b'x-authenticated-user-email': b'user@example.com',
    }

    user = await authenticate(headers)

    assert user == {
        'identity': 'user-123',
        'is_authenticated': True,
        'display_name': 'user@example.com',
    }


@pytest.mark.anyio
async def test_authenticate_rejects_invalid_gateway_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, 'GATEWAY_UPSTREAM_SECRET', 'shared-secret')

    with pytest.raises(auth.Auth.exceptions.HTTPException) as exc_info:
        await authenticate(
            {
                b'x-gateway-upstream-secret': b'wrong',
                b'x-authenticated-user-id': b'user-123',
            }
        )

    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_enforce_owner_scope_adds_owner_metadata() -> None:
    value: dict[str, object] = {}

    filters = await enforce_owner_scope(DummyContext(), value)  # type: ignore[arg-type]

    assert filters == {'owner': 'user-123'}
    assert value == {'metadata': {'owner': 'user-123'}}
