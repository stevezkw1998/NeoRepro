#!/usr/bin/env python3
"""Download small public NeoRepro source tables and verify frozen checksums."""

from __future__ import annotations

import argparse
import csv
import hashlib
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/sources.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        sources = list(csv.DictReader(handle))
    for source in sources:
        request = urllib.request.Request(
            source["source_url"],
            headers={"User-Agent": "NeoRepro/0.1 public-data fetcher"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        observed = hashlib.sha256(payload).hexdigest()
        if observed != source["sha256"]:
            raise SystemExit(
                f"checksum mismatch for {source['source_id']}: {observed} != {source['sha256']}"
            )
        destination = args.output_dir / f"{source['source_id']}.csv"
        destination.write_bytes(payload)
        print(f"verified {source['source_id']} {len(payload)} bytes -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

