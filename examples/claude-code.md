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
