from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

from caddy_mcp.caddyfile import adapt_caddyfile, validate_caddyfile
from caddy_mcp.client import CaddyAdminClient
from caddy_mcp.validation import validate_json_object


def build_server() -> FastMCP:
    mcp = FastMCP("caddy-mcp")
    client = CaddyAdminClient(os.environ.get("CADDY_ADMIN_URL"))

    @mcp.tool
    def get_config(path: str = "") -> Any:
        """Read Caddy's active JSON config, optionally below /config/{path}."""
        return client.get_config(path)

    @mcp.tool
    def list_reverse_proxy_upstreams() -> list[dict[str, Any]]:
        """Summarize host matchers and reverse_proxy upstreams from the active config."""
        return client.reverse_proxy_upstreams()

    @mcp.tool
    def validate_caddyfile_text(caddyfile: str) -> dict[str, Any]:
        """Run `caddy validate` against Caddyfile text without loading it."""
        return validate_caddyfile(caddyfile)

    @mcp.tool
    def adapt_caddyfile_text(caddyfile: str, dry_run: bool = True) -> dict[str, Any]:
        """Convert Caddyfile text to JSON. Defaults to dry_run command preview."""
        return adapt_caddyfile(caddyfile, dry_run=dry_run)

    @mcp.tool
    def load_config(config: dict, dry_run: bool = True) -> Any:
        """Replace Caddy's active config via POST /load. Defaults to dry_run."""
        return client.load_config(validate_json_object(config, "config"), dry_run=dry_run)

    @mcp.tool
    def patch_config(path: str, value: Any, dry_run: bool = True) -> Any:
        """Patch a config subpath via PATCH /config/{path}. Defaults to dry_run."""
        return client.patch_config(path, value, dry_run=dry_run)

    @mcp.tool
    def stop_caddy(dry_run: bool = True) -> Any:
        """Stop the Caddy process via POST /stop. Defaults to dry_run."""
        return client.stop(dry_run=dry_run)

    return mcp


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    mcp = build_server()
    if transport == "sse":
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "stdio":
        mcp.run()
    else:
        raise SystemExit("MCP_TRANSPORT must be 'stdio' or 'sse'")


if __name__ == "__main__":
    main()
