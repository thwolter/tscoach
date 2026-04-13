"""FastAPI app wiring for auth, admin, and upstream proxy routing."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from agent.auth.admin import mount_admin
from agent.auth.config import settings
from agent.auth.routes import router as auth_router
from agent.gateway.proxy import router as proxy_router

app = FastAPI(
    title="TSCoach Auth Gateway",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(SessionMiddleware, secret_key=settings.admin_session_secret)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Lightweight gateway liveness endpoint."""
    return {"status": "ok"}


@app.get("/admin", include_in_schema=False)
async def admin_redirect() -> RedirectResponse:
    """Normalize admin base path to the mounted SQLAdmin path."""
    return RedirectResponse(url="/admin/", status_code=307)


mount_admin(app)
app.include_router(auth_router)
app.include_router(proxy_router)
