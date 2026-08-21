#!/usr/bin/env python3
"""Fail when a release tracks private environments, upstream sources, or raw inputs."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

FORBIDDEN_PARTS = {".venv", "source", "vendor", "__pycache__"}
SECRET_PATTERN = re.compile(
    rb"(?:sk-proj-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|"
    rb"(?:OPENAI|ANTHROPIC)_API_KEY\s*=\s*[^\s]+)"
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    tracked = [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]
    violations: list[str] = []
    for relative in tracked:
        parts = set(relative.parts)
        if FORBIDDEN_PARTS & parts:
            violations.append(f"forbidden tracked directory: {relative}")
        if relative.parts[:2] == ("data", "raw") and relative.name != ".gitkeep":
            violations.append(f"raw input tracked: {relative}")
        path = root / relative
        if path.is_file() and path.stat().st_size <= 5_000_000:
            try:
                payload = path.read_bytes()
            except OSError as error:
                violations.append(f"unreadable tracked file: {relative}: {error}")
                continue
            if SECRET_PATTERN.search(payload):
                violations.append(f"possible credential in tracked file: {relative}")
    report = {
        "status": "pass" if not violations else "fail",
        "tracked_files": len(tracked),
        "forbidden_parts": sorted(FORBIDDEN_PARTS),
        "violations": violations,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
