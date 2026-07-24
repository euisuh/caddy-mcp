import httpx
import pytest
import respx

from caddy_mcp.client import CaddyAdminClient, CaddyAPIError


@respx.mock
def test_get_config_fetches_root_config():
    respx.get("http://caddy.test/config/").mock(return_value=httpx.Response(200, json={"apps": {}}))
    client = CaddyAdminClient("http://caddy.test")
    assert client.get_config() == {"apps": {}}


@respx.mock
def test_get_config_fetches_subpath():
    respx.get("http://caddy.test/config/apps/http").mock(return_value=httpx.Response(200, json={"servers": {}}))
    client = CaddyAdminClient("http://caddy.test")
    assert client.get_config("/apps/http") == {"servers": {}}


@respx.mock
def test_load_config_dry_run_does_not_call_api():
    client = CaddyAdminClient("http://caddy.test")
    result = client.load_config({"apps": {}}, dry_run=True)
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/load"
    assert not respx.calls


@respx.mock
def test_load_config_posts_json_when_not_dry_run():
    route = respx.post("http://caddy.test/load").mock(return_value=httpx.Response(200, json={"ok": True}))
    client = CaddyAdminClient("http://caddy.test")
    assert client.load_config({"apps": {}}, dry_run=False) == {"ok": True}
    assert route.called


@respx.mock
def test_errors_are_actionable_and_redacted():
    respx.get("http://caddy.test/config/").mock(return_value=httpx.Response(500, text="secret-token leaked"))
    client = CaddyAdminClient("http://caddy.test")
    with pytest.raises(CaddyAPIError) as exc:
        client.get_config()
    assert "GET /config/ failed with 500" in str(exc.value)
    assert "secret-token" not in str(exc.value)
