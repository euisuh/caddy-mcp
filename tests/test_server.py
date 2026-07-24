import pytest
from fastmcp import Client

from caddy_mcp.server import build_server


@pytest.mark.asyncio
async def test_tool_registry_exposes_safe_default_tools():
    async with Client(build_server()) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools}
    assert names == {
        "get_config",
        "list_reverse_proxy_upstreams",
        "validate_caddyfile_text",
        "adapt_caddyfile_text",
        "load_config",
        "patch_config",
        "stop_caddy",
    }


@pytest.mark.asyncio
async def test_mutating_tools_default_to_dry_run(monkeypatch):
    monkeypatch.setenv("CADDY_ADMIN_URL", "http://caddy.test")
    async with Client(build_server()) as client:
        result = await client.call_tool("stop_caddy", {})
    assert result.data["dry_run"] is True
    assert result.data["path"] == "/stop"
