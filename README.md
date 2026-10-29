# Caddy MCP

MCP server for safely inspecting and operating a local Caddy admin API. Built for homelab and personal-infra workflows where an AI assistant should be able to inspect active routes, validate Caddyfile snippets, and preview admin-API mutations before applying them.

## Features

- FastMCP stdio and SSE transports.
- Safe default Caddy admin URL: `http://127.0.0.1:2019`.
- Read-only tools for active config and reverse-proxy upstream inventory.
- Caddyfile validation/adaptation helpers using the local `caddy` binary.
- Mutating tools default to `dry_run=true`.
- Redacted admin API errors.
- Optional `CADDY_READ_ONLY` mode (mutating tools not registered) and `MCP_BEARER_TOKEN` for SSE.
- Installable package layout, Dockerfile, Compose sidecar, CI, tests, and client examples.

## Tools

| Tool | Purpose | Mutates |
|---|---|---:|
| `get_config` | Read active JSON config, optionally below `/config/{path}` | no |
| `list_reverse_proxy_upstreams` | Summarize host matchers and `reverse_proxy` upstreams | no |
| `get_upstream_health` | Live upstream status (`address`, `num_requests`, `fails`) from `GET /reverse_proxy/upstreams` | no |
| `validate_caddyfile_text` | Validate Caddyfile text with `caddy validate` | no |
| `adapt_caddyfile_text` | Convert Caddyfile text to JSON; dry-run preview by default | no |
| `load_config` | Replace active config with `POST /load` | yes, unless dry-run |
| `patch_config` | Patch one config path with `PATCH /config/{path}` | yes, unless dry-run |
| `stop_caddy` | Stop Caddy with `POST /stop` | yes, unless dry-run |

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `CADDY_ADMIN_URL` | `http://127.0.0.1:2019` | Caddy admin API base URL (http or https) |
| `CADDY_READ_ONLY` | unset | `1`/`true`/`yes`: do not register `load_config`, `patch_config`, `stop_caddy` |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `sse` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | SSE bind address |
| `MCP_BEARER_TOKEN` | unset | SSE only: require `Authorization: Bearer <token>`; `/healthz` stays open |

`validate_caddyfile_text` and `adapt_caddyfile_text(dry_run=false)` shell out to a `caddy` binary on `PATH`; if it is missing they return an error result instead of raising.

## Quick start

```bash
git clone https://github.com/euisuh/caddy-mcp.git
cd caddy-mcp
python -m venv .venv
. .venv/bin/activate
pip install -e .
CADDY_ADMIN_URL=http://127.0.0.1:2019 caddy-mcp
```

For SSE sidecar mode:

```bash
MCP_TRANSPORT=sse MCP_HOST=127.0.0.1 MCP_PORT=8000 caddy-mcp
```

## Client configuration

Claude Code (stdio):

```bash
claude mcp add caddy --env CADDY_ADMIN_URL=http://127.0.0.1:2019 -- caddy-mcp
```

Claude Desktop (`claude_desktop_config.json`), using the `caddy-mcp` script from a virtualenv where the package is installed:

```json
{
  "mcpServers": {
    "caddy": {
      "command": "/path/to/caddy-mcp/.venv/bin/caddy-mcp",
      "env": { "CADDY_ADMIN_URL": "http://127.0.0.1:2019", "CADDY_READ_ONLY": "1" }
    }
  }
}
```

Drop `CADDY_READ_ONLY` to expose the dry-run-by-default mutating tools. More in [`examples/`](examples/).

## Docker sidecar

```bash
docker compose up --build
```

The Compose file binds the MCP port to localhost and points at host Caddy's admin API via `host.docker.internal:2019`.

## Safety model

- Caddy's admin API is powerful. Keep it bound to loopback or an internal network.
- This server does not expose credentials and does not persist tokens.
- Mutating tools default to dry-run and return the exact method/path/value preview.
- Set `CADDY_READ_ONLY=1` to remove the mutating tools entirely.
- The SSE transport has no auth unless `MCP_BEARER_TOKEN` is set; the Compose file passes it through.
- Use `load_config` and `patch_config` only after validating/adapting configs.
- `stop_caddy` exists for completeness but also defaults to dry-run.

## Development

```bash
pip install -e . -r requirements-dev.txt
ruff check .
pytest -q
python -m build --sdist --wheel
twine check dist/*
```

## Live smoke against a local Caddy

```bash
CADDY_ADMIN_URL=http://127.0.0.1:2019 python - <<'PY'
import asyncio
from fastmcp import Client
from caddy_mcp.server import build_server

async def main():
    async with Client(build_server()) as client:
        print([tool.name for tool in await client.list_tools()])
        print((await client.call_tool('list_reverse_proxy_upstreams', {})).data)
        print((await client.call_tool('get_upstream_health', {})).data)

asyncio.run(main())
PY
```

## License

MIT
