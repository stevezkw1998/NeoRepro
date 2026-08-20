#!/usr/bin/env python3
"""Download a public ZIP and retain one checksum-pinned member."""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path
from zipfile import ZipFile


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--member", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        observed = digest(args.output)
        if observed != args.sha256:
            raise SystemExit(f"existing output checksum mismatch: {observed}")
        print(f"already verified {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neorepro-archive-") as temporary:
        archive = Path(temporary) / "source.zip"
        request = urllib.request.Request(args.url, headers={"User-Agent": "NeoRepro/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        with ZipFile(archive) as handle:
            member = handle.read(args.member)
        observed = hashlib.sha256(member).hexdigest()
        if observed != args.sha256:
            raise SystemExit(f"member checksum mismatch: {observed} != {args.sha256}")
        temporary_output = args.output.with_suffix(args.output.suffix + ".part")
        temporary_output.write_bytes(member)
        os.replace(temporary_output, args.output)
    print(f"verified {args.member} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
