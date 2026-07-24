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
    if ".." in clean.split("/"):
        raise ValueError("config path must not contain traversal segments")
    if clean.startswith("config"):
        clean = clean.removeprefix("config").strip("/")
    return clean


def validate_json_object(value: object, name: str = "value") -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value
