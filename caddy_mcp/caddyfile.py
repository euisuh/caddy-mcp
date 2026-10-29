from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _run_caddy(args: list[str], caddyfile: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".Caddyfile", delete=False) as handle:
        handle.write(caddyfile)
        path = handle.name
    try:
        try:
            return subprocess.run(
                ["caddy", *args, "--config", path, "--adapter", "caddyfile"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(args, 127, "", "caddy binary not found on PATH")
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 124, "", "caddy timed out after 15s")
    finally:
        Path(path).unlink(missing_ok=True)


def validate_caddyfile(caddyfile: str) -> dict[str, Any]:
    completed = _run_caddy(["validate"], caddyfile)
    return {
        "valid": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def adapt_caddyfile(caddyfile: str, dry_run: bool = True) -> dict[str, Any]:
    if dry_run:
        return {"dry_run": True, "command": ["caddy", "adapt", "--config", "<tempfile>", "--adapter", "caddyfile"], "caddyfile": caddyfile}
    completed = _run_caddy(["adapt"], caddyfile)
    if completed.returncode != 0:
        return {
            "ok": False,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        }
    try:
        return {"ok": True, "config": json.loads(completed.stdout)}
    except ValueError:
        return {"ok": False, "stdout": completed.stdout, "stderr": "caddy adapt output was not JSON", "returncode": 0}
