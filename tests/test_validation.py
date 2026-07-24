import pytest

from caddy_mcp.validation import normalize_admin_url, normalize_config_path


def test_normalize_admin_url_defaults_loopback():
    assert normalize_admin_url(None) == "http://127.0.0.1:2019"


def test_normalize_admin_url_rejects_non_http():
    with pytest.raises(ValueError, match="http or https"):
        normalize_admin_url("file:///tmp/caddy.sock")


def test_normalize_config_path_strips_slashes():
    assert normalize_config_path("/apps/http") == "apps/http"


def test_normalize_config_path_rejects_traversal():
    with pytest.raises(ValueError, match="must not contain"):
        normalize_config_path("../apps")
