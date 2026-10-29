from __future__ import annotations

from urllib.parse import urlparse


def normalize_admin_url(value: str | None) -> str:
    url = (value or "http://127.0.0.1:2019").strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Caddy admin URL must use http or https")
    if not parsed.netloc:
        raise ValueError("Caddy admin URL must include a host")
    return url


def normalize_config_path(path: str | None = None) -> str:
    clean = (path or "").strip().strip("/")
    if any(ch in clean for ch in "?#"):
        raise ValueError("config path must not contain '?' or '#'")
    segments = clean.split("/") if clean else []
    if ".." in segments:
        raise ValueError("config path must not contain traversal segments")
    # Accept "config/apps/http" as well as "apps/http"; "configs" is a different key.
    if segments and segments[0] == "config":
        segments = segments[1:]
    return "/".join(segments)


def validate_json_object(value: object, name: str = "value") -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value
