from unittest.mock import patch

from caddy_mcp.caddyfile import adapt_caddyfile, validate_caddyfile


def test_adapt_caddyfile_dry_run_returns_command_preview():
    result = adapt_caddyfile("example.com { respond ok }", dry_run=True)
    assert result["dry_run"] is True
    assert result["command"][:2] == ["caddy", "adapt"]


def test_validate_caddyfile_uses_caddy_binary():
    completed = type("Completed", (), {"returncode": 0, "stdout": "", "stderr": "valid"})()
    with patch("caddy_mcp.caddyfile.subprocess.run", return_value=completed):
        assert validate_caddyfile("example.com { respond ok }")["valid"] is True


def test_missing_caddy_binary_is_reported_not_raised():
    with patch("caddy_mcp.caddyfile.subprocess.run", side_effect=FileNotFoundError):
        result = validate_caddyfile("x")
    assert result["valid"] is False and "not found" in result["stderr"]


def test_timeout_is_reported_not_raised():
    import subprocess

    with patch("caddy_mcp.caddyfile.subprocess.run", side_effect=subprocess.TimeoutExpired("caddy", 15)):
        result = adapt_caddyfile("x", dry_run=False)
    assert result["ok"] is False and "timed out" in result["stderr"]


def test_adapt_failure_and_non_json_output():
    bad = type("C", (), {"returncode": 1, "stdout": "", "stderr": "syntax"})()
    with patch("caddy_mcp.caddyfile.subprocess.run", return_value=bad):
        assert adapt_caddyfile("x", dry_run=False)["ok"] is False
    junk = type("C", (), {"returncode": 0, "stdout": "not json", "stderr": ""})()
    with patch("caddy_mcp.caddyfile.subprocess.run", return_value=junk):
        assert adapt_caddyfile("x", dry_run=False)["ok"] is False
