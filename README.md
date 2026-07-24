# Caddy MCP

MCP server for safely inspecting and operating a local Caddy admin API. Built for homelab and personal-infra workflows where an AI assistant should be able to inspect active routes, validate Caddyfile snippets, and preview admin-API mutations before applying them.

## Features

- FastMCP stdio and SSE transports.
- Safe default Caddy admin URL: `http://127.0.0.1:2019`.
- Read-only tools for active config and reverse-proxy upstream inventory.
- Caddyfile validation/adaptation helpers using the local `caddy` binary.
- Mutating tools default to `dry_run=true`.
- Redacted admin API errors.
- Installable package layout, Dockerfile, Compose sidecar, CI, tests, and client examples.

## Tools

| Tool | Purpose | Mutates |
|---|---|---:|
| `get_config` | Read active JSON config, optionally below `/config/{path}` | no |
| `list_reverse_proxy_upstreams` | Summarize host matchers and `reverse_proxy` upstreams | no |
| `validate_caddyfile_text` | Validate Caddyfile text with `caddy validate` | no |
| `adapt_caddyfile_text` | Convert Caddyfile text to JSON; dry-run preview by default | no |
| `load_config` | Replace active config with `POST /load` | yes, unless dry-run |
| `patch_config` | Patch one config path with `PATCH /config/{path}` | yes, unless dry-run |
| `stop_caddy` | Stop Caddy with `POST /stop` | yes, unless dry-run |

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

## Docker sidecar

```bash
docker compose up --build
```

The Compose file binds the MCP port to localhost and points at host Caddy's admin API via `host.docker.internal:2019`.

## Safety model

- Caddy's admin API is powerful. Keep it bound to loopback or an internal network.
- This server does not expose credentials and does not persist tokens.
- Mutating tools default to dry-run and return the exact method/path/value preview.
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

asyncio.run(main())
PY
```

## License

MIT
