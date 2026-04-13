"""Storage adapters for API key validation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class APIKeyRecord:
    """Persisted API key metadata."""

    key_hash: str
    name: str
    is_active: bool = True
    scopes: tuple[str, ...] = field(default_factory=tuple)


class APIKeyStore(Protocol):
    """Key lookup contract for reusable auth modules."""

    async def get_by_hash(self, key_hash: str) -> APIKeyRecord | None:
        """Return matching API key record if present."""


def _normalize_scopes(raw: Any) -> tuple[str, ...]:
    """Normalize DB scopes from list/tuple/string into tuple[str, ...]."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    return (str(raw),)


class PostgresAPIKeyStore:
    """Postgres-backed key store."""

    def __init__(self, dsn: str) -> None:
        """Initialize store with a Postgres DSN."""
        if not dsn:
            raise ValueError("Missing Postgres DSN for API key store")
        self._dsn = dsn

    def _get_by_hash_sync(self, key_hash: str) -> APIKeyRecord | None:
        """Blocking query implementation used through a thread hop."""
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "psycopg is required for Postgres API key store"
            ) from exc

        query = (
            "SELECT key_hash, name, is_active, COALESCE(scopes, '{}') "
            "FROM agent_api_keys WHERE key_hash = %s LIMIT 1"
        )

        with psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(query, (key_hash,))
            row = cur.fetchone()

        if row is None:
            return None

        row_key_hash, row_name, row_is_active, row_scopes = row
        scopes = _normalize_scopes(row_scopes)
        return APIKeyRecord(
            key_hash=str(row_key_hash),
            name=str(row_name),
            is_active=bool(row_is_active),
            scopes=scopes,
        )

    async def get_by_hash(self, key_hash: str) -> APIKeyRecord | None:
        """Read key metadata by hash from Postgres."""
        return await asyncio.to_thread(self._get_by_hash_sync, key_hash)


def resolve_db_uri(env: Mapping[str, str], override: str | None = None) -> str:
    """Resolve Postgres connection URI from override or environment."""
    dsn = override or env.get("AGENT_API_KEY_DB_URI") or env.get("POSTGRES_URI")
    if not dsn:
        raise ValueError("Set AGENT_API_KEY_DB_URI or POSTGRES_URI")
    return dsn


def create_api_key_store(env: Mapping[str, str]) -> APIKeyStore:
    """Create Postgres store from AGENT_API_KEY_DB_URI or POSTGRES_URI."""
    dsn = resolve_db_uri(env)
    return PostgresAPIKeyStore(dsn=dsn)
