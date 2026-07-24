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
