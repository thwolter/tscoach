"""Compatibility shim for the gateway ASGI app entrypoint."""

from agent.gateway.app import app

__all__ = ["app"]
