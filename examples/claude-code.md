# Claude Code

Run locally over stdio:

```bash
claude mcp add caddy --env CADDY_ADMIN_URL=http://127.0.0.1:2019 -- caddy-mcp
```

Run as an SSE sidecar:

```bash
MCP_TRANSPORT=sse MCP_HOST=127.0.0.1 MCP_PORT=8000 caddy-mcp
claude mcp add caddy http://127.0.0.1:8000/sse
```

Read-only (no `load_config`/`patch_config`/`stop_caddy`):

```bash
claude mcp add caddy --env CADDY_ADMIN_URL=http://127.0.0.1:2019 --env CADDY_READ_ONLY=1 -- caddy-mcp
```

With `MCP_BEARER_TOKEN` set on the SSE server, add `--header "Authorization: Bearer $MCP_BEARER_TOKEN"` and `--transport sse` to the `claude mcp add` URL form.
