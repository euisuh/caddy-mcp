import json
from unittest.mock import patch

import httpx
import pytest
import respx
from fastmcp import Client
from fastmcp.exceptions import ToolError

from caddy_mcp.server import build_server

BASE = "http://caddy.test"
ALL_TOOLS = {
    "get_config",
    "list_reverse_proxy_upstreams",
    "get_upstream_health",
    "validate_caddyfile_text",
    "adapt_caddyfile_text",
    "load_config",
    "patch_config",
    "stop_caddy",
}
MUTATING = {"load_config", "patch_config", "stop_caddy"}

CONFIG = {
    "apps": {
        "http": {
            "servers": {
                "srv0": {
                    "routes": [
                        {
                            "match": [{"host": ["a.example.com"]}],
                            "handle": [
                                {"handler": "subroute", "routes": [
                                    {"handle": [{"handler": "reverse_proxy", "upstreams": [{"dial": "app:3000"}]}]}
                                ]}
                            ],
                        },
                        {"handle": [{"handler": "static_response"}]},
                    ]
                }
            }
        }
    }
}


@pytest.fixture(autouse=True)
def admin_url(monkeypatch):
    monkeypatch.setenv("CADDY_ADMIN_URL", BASE)
    monkeypatch.delenv("CADDY_READ_ONLY", raising=False)


async def call(name, args=None):
    async with Client(build_server()) as client:
        return (await client.call_tool(name, args or {})).data


@pytest.mark.asyncio
async def test_tool_registry():
    async with Client(build_server()) as client:
        assert {t.name for t in await client.list_tools()} == ALL_TOOLS


@pytest.mark.asyncio
async def test_read_only_hides_mutating_tools(monkeypatch):
    monkeypatch.setenv("CADDY_READ_ONLY", "1")
    async with Client(build_server()) as client:
        assert {t.name for t in await client.list_tools()} == ALL_TOOLS - MUTATING


@pytest.mark.asyncio
@respx.mock
async def test_get_config_tool():
    route = respx.get(f"{BASE}/config/apps/http").mock(return_value=httpx.Response(200, json={"servers": {}}))
    assert await call("get_config", {"path": "apps/http"}) == {"servers": {}}
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_get_config_tool_surfaces_redacted_error():
    respx.get(f"{BASE}/config/").mock(return_value=httpx.Response(500, text="secret"))
    with pytest.raises(ToolError) as exc:
        await call("get_config")
    assert "500" in str(exc.value) and "secret" not in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_list_reverse_proxy_upstreams_tool_walks_subroutes():
    respx.get(f"{BASE}/config/").mock(return_value=httpx.Response(200, json=CONFIG))
    assert await call("list_reverse_proxy_upstreams") == [
        {"server": "srv0", "route_index": 0, "hosts": ["a.example.com"], "upstreams": [{"dial": "app:3000"}]}
    ]


@pytest.mark.asyncio
@respx.mock
async def test_list_reverse_proxy_upstreams_empty_config():
    respx.get(f"{BASE}/config/").mock(return_value=httpx.Response(200, json=None))
    assert await call("list_reverse_proxy_upstreams") == []


@pytest.mark.asyncio
@respx.mock
async def test_get_upstream_health_tool():
    payload = [{"address": "app:3000", "num_requests": 2, "fails": 1}]
    respx.get(f"{BASE}/reverse_proxy/upstreams").mock(return_value=httpx.Response(200, json=payload))
    assert await call("get_upstream_health") == payload


@pytest.mark.asyncio
async def test_validate_caddyfile_text_tool():
    done = type("C", (), {"returncode": 1, "stdout": "", "stderr": "bad"})()
    with patch("caddy_mcp.caddyfile.subprocess.run", return_value=done):
        result = await call("validate_caddyfile_text", {"caddyfile": "nope {"})
    assert result["valid"] is False and result["stderr"] == "bad"


@pytest.mark.asyncio
async def test_adapt_caddyfile_text_tool_dry_run_and_real():
    assert (await call("adapt_caddyfile_text", {"caddyfile": "x"}))["dry_run"] is True
    done = type("C", (), {"returncode": 0, "stdout": json.dumps({"apps": {}}), "stderr": ""})()
    with patch("caddy_mcp.caddyfile.subprocess.run", return_value=done):
        result = await call("adapt_caddyfile_text", {"caddyfile": "x", "dry_run": False})
    assert result == {"ok": True, "config": {"apps": {}}}


@pytest.mark.asyncio
@respx.mock
async def test_load_config_tool_dry_run_then_apply():
    route = respx.post(f"{BASE}/load").mock(return_value=httpx.Response(200))
    preview = await call("load_config", {"config": {"apps": {}}})
    assert preview["dry_run"] is True and not route.called
    assert await call("load_config", {"config": {"apps": {}}, "dry_run": False}) == {"ok": True}
    assert json.loads(route.calls.last.request.content) == {"apps": {}}


@pytest.mark.asyncio
@respx.mock
async def test_patch_config_tool_dry_run_then_apply():
    route = respx.patch(f"{BASE}/config/apps/http/servers/srv0/listen").mock(return_value=httpx.Response(200))
    args = {"path": "/config/apps/http/servers/srv0/listen", "value": [":8443"]}
    preview = await call("patch_config", args)
    assert preview["dry_run"] is True and preview["path"] == "/config/apps/http/servers/srv0/listen"
    assert not route.called
    await call("patch_config", {**args, "dry_run": False})
    assert json.loads(route.calls.last.request.content) == [":8443"]


@pytest.mark.asyncio
@respx.mock
async def test_stop_caddy_tool_dry_run_then_apply():
    route = respx.post(f"{BASE}/stop").mock(return_value=httpx.Response(200))
    assert (await call("stop_caddy"))["dry_run"] is True and not route.called
    await call("stop_caddy", {"dry_run": False})
    assert route.called
