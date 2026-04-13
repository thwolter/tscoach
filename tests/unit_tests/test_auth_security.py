from __future__ import annotations

import pytest

from agent.auth.gateway_security import (
    AuthError,
    authenticate_bearer_from_headers,
    extract_bearer_token,
)
from agent.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class DummyUser:
    def __init__(self, user_id: int, username: str, is_active: bool) -> None:
        self.id = user_id
        self.username = username
        self.is_active = is_active


class DummySession:
    def __init__(self, users: dict[int, DummyUser]) -> None:
        self.users = users

    def get(self, model, primary_key: int):  # noqa: ANN001
        return self.users.get(primary_key)


def test_hash_password_roundtrip() -> None:
    password = "MyStrongPassword!123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash)
    assert not verify_password("wrong", password_hash)


def test_create_and_decode_access_token_roundtrip() -> None:
    token = create_access_token(
        user_id=42,
        username="alice",
        is_admin=True,
        panels=["sales", "support"],
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["username"] == "alice"
    assert payload["is_admin"] is True
    assert payload["panels"] == ["sales", "support"]


def test_extract_bearer_token_from_authorization_header() -> None:
    headers = {"Authorization": "Bearer abc.def.ghi"}

    assert extract_bearer_token(headers) == "abc.def.ghi"


def test_extract_bearer_token_invalid_header() -> None:
    headers = {"Authorization": "Basic xyz"}

    assert extract_bearer_token(headers) is None


def test_authenticate_bearer_from_headers_success() -> None:
    token = create_access_token(
        user_id=7,
        username="bob",
        is_admin=False,
        panels=["dashboard"],
    )
    headers = {"Authorization": f"Bearer {token}"}
    session = DummySession(
        users={7: DummyUser(user_id=7, username="bob", is_active=True)}
    )

    user = authenticate_bearer_from_headers(headers, session=session)

    assert user.username == "bob"


def test_authenticate_bearer_from_headers_missing_token() -> None:
    session = DummySession(users={})

    with pytest.raises(AuthError) as exc_info:
        authenticate_bearer_from_headers({}, session=session)

    assert exc_info.value.status_code == 401


def test_authenticate_bearer_from_headers_inactive_user() -> None:
    token = create_access_token(
        user_id=9,
        username="charlie",
        is_admin=False,
        panels=[],
    )
    headers = {"Authorization": f"Bearer {token}"}
    session = DummySession(
        users={9: DummyUser(user_id=9, username="charlie", is_active=False)}
    )

    with pytest.raises(AuthError) as exc_info:
        authenticate_bearer_from_headers(headers, session=session)

    assert exc_info.value.status_code == 401
