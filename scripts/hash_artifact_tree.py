#!/usr/bin/env python3
"""Create a deterministic content manifest for an uncommitted third-party artifact tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tree = args.tree.resolve()
    if not tree.is_dir():
        raise SystemExit(f"artifact tree not found: {tree}")
    files = []
    for path in sorted(candidate for candidate in tree.rglob("*") if candidate.is_file()):
        relative = str(path.relative_to(tree))
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": file_hash(path)})
    digest = hashlib.sha256()
    for item in files:
        digest.update(f"{item['sha256']}  {item['path']}\n".encode())
    report = {
        "tree_name": tree.name,
        "files": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "tree_sha256": digest.hexdigest(),
        "entries": files,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("tree_name", "files", "bytes", "tree_sha256")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
