from __future__ import annotations

from typing import Any

import httpx

from caddy_mcp.validation import normalize_admin_url, normalize_config_path, validate_json_object


class CaddyAPIError(RuntimeError):
    """Actionable, redacted error from the Caddy admin API."""

    def __init__(self, method: str, path: str, status_code: int, detail: str = "") -> None:
        safe_detail = "" if not detail else " Response body redacted."
        outcome = "was unreachable" if status_code == 0 else f"failed with {status_code}"
        super().__init__(f"Caddy admin API {method} {path} {outcome}.{safe_detail}")
        self.method = method
        self.path = path
        self.status_code = status_code


class CaddyAdminClient:
    def __init__(self, admin_url: str | None = None, timeout: float = 10.0) -> None:
        self.admin_url = normalize_admin_url(admin_url)
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.admin_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = httpx.request(method, self._url(path), timeout=self.timeout, **kwargs)
        except httpx.HTTPError as exc:
            raise CaddyAPIError(method, path, 0, str(exc)) from exc
        if response.status_code >= 400:
            raise CaddyAPIError(method, path, response.status_code, response.text)
        if not response.content:
            return {"ok": True}
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        try:
            return response.json()
        except ValueError:
            return {"ok": True, "body": response.text}

    def get_config(self, path: str | None = None) -> Any:
        clean = normalize_config_path(path)
        suffix = f"/{clean}" if clean else "/"
        return self._request("GET", f"/config{suffix}")

    def load_config(self, config: dict, dry_run: bool = True) -> Any:
        config = validate_json_object(config, "config")
        if dry_run:
            return {"dry_run": True, "method": "POST", "path": "/load", "config": config}
        return self._request("POST", "/load", json=config)

    def patch_config(self, path: str, value: Any, dry_run: bool = True) -> Any:
        clean = normalize_config_path(path)
        api_path = f"/config/{clean}" if clean else "/config/"
        if dry_run:
            return {"dry_run": True, "method": "PATCH", "path": api_path, "value": value}
        return self._request("PATCH", api_path, json=value)

    def stop(self, dry_run: bool = True) -> Any:
        if dry_run:
            return {"dry_run": True, "method": "POST", "path": "/stop"}
        return self._request("POST", "/stop")

    def upstream_health(self) -> list[dict[str, Any]]:
        """GET /reverse_proxy/upstreams: address, num_requests, fails per upstream."""
        result = self._request("GET", "/reverse_proxy/upstreams")
        return result if isinstance(result, list) else []

    def reverse_proxy_upstreams(self) -> list[dict[str, Any]]:
        config = self.get_config()
        results: list[dict[str, Any]] = []
        servers = {}
        if isinstance(config, dict):
            servers = ((config.get("apps") or {}).get("http") or {}).get("servers") or {}
        for server_name, server in servers.items():
            for route_idx, route in enumerate(server.get("routes", [])):
                hosts: list[str] = []
                for matcher in route.get("match", []):
                    hosts.extend(matcher.get("host", []))
                for handler in _walk_handlers(route):
                    if handler.get("handler") == "reverse_proxy":
                        results.append(
                            {
                                "server": server_name,
                                "route_index": route_idx,
                                "hosts": hosts,
                                "upstreams": handler.get("upstreams", []),
                            }
                        )
        return results


def _walk_handlers(node: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for handler in node.get("handle", []):
        found.append(handler)
        for route in handler.get("routes", []):
            found.extend(_walk_handlers(route))
    for route in node.get("routes", []):
        found.extend(_walk_handlers(route))
    return found
