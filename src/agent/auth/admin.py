"""SQLAdmin setup for admin-only user and panel management."""

from __future__ import annotations

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from agent.auth.config import settings
from agent.auth.db import SessionLocal, engine
from agent.auth.models import PanelAccess, User
from agent.auth.security import verify_password


def _get_user_by_username(session: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username).limit(1)
    return session.execute(statement).scalar_one_or_none()


class AdminAuth(AuthenticationBackend):
    """Session-backed auth for SQLAdmin, restricted to admin users."""

    def __init__(self) -> None:
        """Initialize session signer used by SQLAdmin auth cookies."""
        super().__init__(secret_key=settings.admin_session_secret)

    async def login(self, request: Request) -> bool:
        """Authenticate admin credentials from SQLAdmin login form."""
        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", "")).strip()

        with SessionLocal() as session:
            user = _get_user_by_username(session, username)
            if user is None or not user.is_active or not user.is_admin:
                return False
            if not verify_password(password, user.password_hash):
                return False

        request.session.update(
            {
                "token": f"admin:{user.id}",
                "admin_user_id": user.id,
                "admin_username": user.username,
            }
        )
        return True

    async def logout(self, request: Request) -> bool:
        """Clear SQLAdmin session state."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        """Authorize requests to /admin endpoints."""
        user_id = request.session.get("admin_user_id")
        if user_id is None:
            return RedirectResponse(url="/admin/login", status_code=302)

        with SessionLocal() as session:
            user = session.get(User, int(user_id))
            if user is None or not user.is_active or not user.is_admin:
                request.session.clear()
                return RedirectResponse(url="/admin/login", status_code=302)

        return True


class UserAdmin(ModelView, model=User):
    """Admin management UI for users."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.username,
        User.is_active,
        User.is_admin,
        User.created_at,
    ]
    column_searchable_list = [User.username]
    column_sortable_list = [
        User.id,
        User.username,
        User.is_active,
        User.is_admin,
        User.created_at,
    ]
    column_details_exclude_list = [User.password_hash]

    form_columns = [User.username, User.password_hash, User.is_active, User.is_admin]
    form_widget_args = {
        "password_hash": {
            "type": "password",
            "autocomplete": "new-password",
            "placeholder": "Enter new password",
        }
    }

    async def on_model_change(
        self, data, model: User, is_created: bool, request: Request
    ) -> None:
        """Convert plain password input to bcrypt hash before saving."""
        raw_password = str(data.get("password_hash", "")).strip()
        if not raw_password:
            if is_created:
                raise ValueError("Password is required")
            data.pop("password_hash", None)
            return

        from agent.auth.security import hash_password

        data["password_hash"] = hash_password(raw_password)


class PanelAccessAdmin(ModelView, model=PanelAccess):
    """Admin management UI for per-panel access mappings."""

    name = "Panel Access"
    name_plural = "Panel Access"
    icon = "fa-solid fa-table-cells"

    column_list = [
        PanelAccess.id,
        PanelAccess.user_id,
        PanelAccess.panel_key,
        PanelAccess.created_at,
    ]
    column_sortable_list = [
        PanelAccess.id,
        PanelAccess.user_id,
        PanelAccess.panel_key,
        PanelAccess.created_at,
    ]
    form_columns = [PanelAccess.user_id, PanelAccess.panel_key]


def mount_admin(app) -> None:
    """Mount SQLAdmin with admin-only auth backend."""
    admin = Admin(app, engine, authentication_backend=AdminAuth())
    admin.add_view(UserAdmin)
    admin.add_view(PanelAccessAdmin)
