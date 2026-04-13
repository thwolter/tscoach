"""Auth gateway that protects an internal LangGraph API."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from agent.security import (
    APIKeyAuthError,
    create_api_key_store,
    validate_api_key_from_headers,
)

UPSTREAM_URL = (
    os.environ.get("LANGGRAPH_UPSTREAM_URL") or "http://langgraph-api:8000"
).rstrip("/")
PEPPER = os.environ.get("AGENT_API_KEY_PEPPER", "")
STORE = create_api_key_store(os.environ)

if not PEPPER:
    raise RuntimeError("AGENT_API_KEY_PEPPER is required")

app = FastAPI(
    title="TSCoach Auth Gateway",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
PUBLIC_PATHS = {"/docs", "/openapi.json", "/docs/oauth2-redirect", "/redoc", "/healthz"}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Lightweight gateway liveness endpoint."""
    return {"status": "ok"}


def _inject_bearer_security(spec: dict[str, Any]) -> dict[str, Any]:
    """Expose Bearer auth in Swagger UI for proxied endpoints."""
    components = spec.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "API Key",
    }

    for operations in spec.get("paths", {}).values():
        if not isinstance(operations, dict):
            continue
        for method_config in operations.values():
            if not isinstance(method_config, dict):
                continue
            method_config["security"] = [{"BearerAuth": []}]

    return spec


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
)
async def proxy(path: str, request: Request) -> Response:
    """Validate API key and forward request to upstream LangGraph API."""
    if request.url.path not in PUBLIC_PATHS:
        try:
            await validate_api_key_from_headers(
                request.headers, store=STORE, pepper=PEPPER
            )
        except APIKeyAuthError as exc:
            return JSONResponse(
                status_code=exc.status_code, content={"detail": exc.detail}
            )

    upstream_url = f"{UPSTREAM_URL}/{path}"
    query_string = request.url.query
    if query_string:
        upstream_url = f"{upstream_url}?{query_string}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    body = await request.body()

    async with httpx.AsyncClient(timeout=120.0) as client:
        upstream_response = await client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            content=body,
        )

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection"}
    }
    if request.url.path == "/openapi.json" and upstream_response.status_code == 200:
        spec = _inject_bearer_security(upstream_response.json())
        return JSONResponse(status_code=200, content=spec)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
