import anyio
from starlette.responses import JSONResponse

from caddy_mcp.server import get_sse_middleware


async def ok_app(scope, receive, send):
    await JSONResponse({"ok": True})(scope, receive, send)


def build(middleware):
    app = ok_app
    for item in reversed(middleware):
        app = item.cls(app, **item.kwargs)
    return app


def status(app, path="/sse", headers=None):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    anyio.run(app, {"type": "http", "method": "GET", "path": path, "headers": headers or []}, receive, send)
    return next(m["status"] for m in messages if m["type"] == "http.response.start")


def test_no_token_means_open_but_healthz_exists(monkeypatch):
    monkeypatch.delenv("MCP_BEARER_TOKEN", raising=False)
    app = build(get_sse_middleware())
    assert status(app) == 200 and status(app, "/healthz") == 200


def test_token_required_except_healthz(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", "s3cret")
    app = build(get_sse_middleware())
    assert status(app) == 401
    assert status(app, headers=[(b"authorization", b"Bearer wrong")]) == 401
    assert status(app, headers=[(b"authorization", b"Bearer s3cret")]) == 200
    assert status(app, "/healthz") == 200
