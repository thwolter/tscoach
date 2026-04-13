"""Generate an API key and insert its hash into Postgres."""

from __future__ import annotations

import argparse
import os
import sys

import psycopg

from agent.security import generate_api_key, hash_api_key, resolve_db_uri


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name", required=True, help="Human-readable name for this key"
    )
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Optional scope. Can be repeated (for example: --scope chat:invoke)",
    )
    parser.add_argument(
        "--db-uri",
        default=None,
        help="Override Postgres URI (otherwise AGENT_API_KEY_DB_URI or POSTGRES_URI)",
    )
    return parser


def main() -> int:
    """Create a key, hash it, store hash in Postgres, and print plaintext key."""
    parser = build_parser()
    args = parser.parse_args()

    pepper = os.environ.get("AGENT_API_KEY_PEPPER", "")
    if not pepper:
        parser.error("Set AGENT_API_KEY_PEPPER before generating keys")

    try:
        db_uri = resolve_db_uri(os.environ, override=args.db_uri)
    except ValueError as exc:
        parser.error(f"{exc} (or pass --db-uri)")

    api_key = generate_api_key()
    key_hash = hash_api_key(api_key, pepper=pepper)

    insert_sql = (
        "INSERT INTO agent_api_keys (key_hash, name, is_active, scopes) "
        "VALUES (%s, %s, true, %s::text[])"
    )

    with psycopg.connect(db_uri) as conn, conn.cursor() as cur:
        cur.execute(insert_sql, (key_hash, args.name, args.scope))
        conn.commit()

    print(api_key)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"generate_api_key failed: {exc}\n")
        raise
