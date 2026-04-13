from __future__ import annotations

import pytest

from agent.security import (
    APIKeyAuthError,
    APIKeyRecord,
    PostgresAPIKeyStore,
    create_api_key_store,
    extract_api_key,
    generate_api_key,
    hash_api_key,
    resolve_db_uri,
    validate_api_key_from_headers,
)


class DummyStore:
    """Simple async key store for validator unit tests."""

    def __init__(self, records: dict[str, APIKeyRecord]) -> None:
        self.records = records

    async def get_by_hash(self, key_hash: str) -> APIKeyRecord | None:
        return self.records.get(key_hash)


def test_generate_api_key_uses_sk_prefix() -> None:
    key = generate_api_key()

    assert key.startswith("sk-")
    assert len(key) > 20


def test_hash_api_key_is_deterministic() -> None:
    key = "sk-test"
    pepper = "pepper-123"

    assert hash_api_key(key, pepper=pepper) == hash_api_key(key, pepper=pepper)


def test_extract_api_key_from_authorization_header() -> None:
    headers = {"Authorization": "Bearer sk-abc123"}

    assert extract_api_key(headers) == "sk-abc123"


def test_extract_api_key_from_x_api_key_header() -> None:
    headers = {b"x-api-key": b"sk-xyz"}

    assert extract_api_key(headers) == "sk-xyz"


@pytest.mark.anyio
async def test_validate_api_key_from_headers_success() -> None:
    pepper = "pepper-123"
    raw_key = "sk-valid"
    key_hash = hash_api_key(raw_key, pepper=pepper)
    store = DummyStore(
        records={key_hash: APIKeyRecord(key_hash=key_hash, name="chat-ui")}
    )

    record = await validate_api_key_from_headers(
        {"Authorization": f"Bearer {raw_key}"},
        store=store,
        pepper=pepper,
    )

    assert record.name == "chat-ui"


@pytest.mark.anyio
async def test_validate_api_key_missing_header() -> None:
    store = DummyStore(records={})

    with pytest.raises(APIKeyAuthError) as exc_info:
        await validate_api_key_from_headers({}, store=store, pepper="pepper")

    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_validate_api_key_invalid_key() -> None:
    store = DummyStore(records={})

    with pytest.raises(APIKeyAuthError) as exc_info:
        await validate_api_key_from_headers(
            {"Authorization": "Bearer sk-bad"},
            store=store,
            pepper="pepper",
        )

    assert exc_info.value.status_code == 403


def test_create_api_key_store_uses_postgres_uri() -> None:
    store = create_api_key_store(
        {"POSTGRES_URI": "postgres://user:pass@localhost:5432/db"}
    )

    assert isinstance(store, PostgresAPIKeyStore)


def test_create_api_key_store_requires_db_uri() -> None:
    with pytest.raises(ValueError, match="Set AGENT_API_KEY_DB_URI or POSTGRES_URI"):
        create_api_key_store({})


def test_resolve_db_uri_prefers_override() -> None:
    dsn = resolve_db_uri(
        {"POSTGRES_URI": "postgres://env"}, override="postgres://override"
    )

    assert dsn == "postgres://override"
