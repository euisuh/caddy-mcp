from __future__ import annotations

import secrets

from starlette.responses import JSONResponse


class HealthCheckMiddleware:
    """Unauthenticated liveness endpoint for SSE deployments."""

    def __init__(self, app, path: str = "/healthz") -> None:
        self.app = app
        self.path = path

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http" and scope.get("path") == self.path:
            await JSONResponse({"ok": True, "service": "caddy-mcp"})(scope, receive, send)
            return
        await self.app(scope, receive, send)


class BearerTokenAuthMiddleware:
    """Require a static bearer token on the SSE transport."""

    def __init__(self, app, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
            if not secrets.compare_digest(headers.get("authorization", ""), f"Bearer {self.token}"):
                response = JSONResponse(
                    {"error": "unauthorized", "detail": "Missing or invalid bearer token"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
