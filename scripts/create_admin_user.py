"""Create or update an admin user in Postgres."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import select

from agent.auth.db import SessionLocal
from agent.auth.models import User
from agent.auth.security import hash_password


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Create/update admin as inactive",
    )
    return parser


def main() -> int:
    """Create admin user if missing, otherwise update password and admin flags."""
    parser = build_parser()
    args = parser.parse_args()

    username = args.username.strip()
    if not username:
        parser.error("--username must not be empty")

    with SessionLocal() as session:
        statement = select(User).where(User.username == username).limit(1)
        user = session.execute(statement).scalar_one_or_none()

        password_hash = hash_password(args.password)
        is_active = not args.inactive

        if user is None:
            user = User(
                username=username,
                password_hash=password_hash,
                is_admin=True,
                is_active=is_active,
            )
            session.add(user)
            action = "created"
        else:
            user.password_hash = password_hash
            user.is_admin = True
            user.is_active = is_active
            action = "updated"

        session.commit()

    print(f"Admin user '{username}' {action}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"create_admin_user failed: {exc}\n")
        raise
