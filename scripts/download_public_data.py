#!/usr/bin/env python3
"""Download small public NeoRepro source tables and verify frozen checksums."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/sources.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--source-id", action="append", dest="source_ids")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        sources = list(csv.DictReader(handle))
    if args.source_ids:
        requested = set(args.source_ids)
        sources = [source for source in sources if source["source_id"] in requested]
        missing = requested - {source["source_id"] for source in sources}
        if missing:
            raise SystemExit(f"unknown source_id values: {sorted(missing)}")
    for source in sources:
        destination = args.output_dir / source["file_name"]
        if destination.exists():
            observed = hashlib.sha256(destination.read_bytes()).hexdigest()
            if observed == source["sha256"]:
                print(f"already verified {source['source_id']} -> {destination}")
                continue
            raise SystemExit(f"existing destination has wrong checksum: {destination}")
        request = urllib.request.Request(
            source["source_url"],
            headers={"User-Agent": "NeoRepro/0.1 public-data fetcher"},
        )
        temporary = destination.with_suffix(destination.suffix + ".part")
        digest = hashlib.sha256()
        size = 0
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            temporary.open("wb") as handle,
        ):
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        observed = digest.hexdigest()
        if observed != source["sha256"]:
            raise SystemExit(
                f"checksum mismatch for {source['source_id']}: {observed} != {source['sha256']}"
            )
        os.replace(temporary, destination)
        print(f"verified {source['source_id']} {size} bytes -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
