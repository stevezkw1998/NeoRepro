#!/usr/bin/env python3
"""Run the pinned fixed-predictor adapters with their required local environments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

EXPECTED = {
    "mhcflurry": ("MHCflurry", "2.2.1", "mhcflurry-2.2.1.csv"),
    "bigmhc": ("BigMHC", "v1.0", "bigmhc-v1.0.csv"),
    "prime": ("PRIME", "2.0", "prime-2.0.csv"),
    "deepimmuno": ("DeepImmuno-CNN", "1.0@df42ac5b", "deepimmuno-cnn.csv"),
    "deephlapan": ("DeepHLApan", "1.1.1@ac1f4beb", "deephlapan-1.1.1.csv"),
}


def commands(root: Path, benchmark: Path, output_dir: Path) -> dict[str, list[str]]:
    return {
        "mhcflurry": [
            str(root / "predictors/mhcflurry/.venv/bin/python"),
            str(root / "predictors/mhcflurry/adapter.py"),
            "--input",
            str(benchmark),
            "--models-dir",
            str(root / "predictors/mhcflurry/vendor/2.2.0/models_class1_presentation/models"),
            "--output",
            str(output_dir / "mhcflurry-2.2.1.csv"),
        ],
        "bigmhc": [
            str(root / "predictors/bigmhc/.venv/bin/python"),
            str(root / "predictors/bigmhc/adapter.py"),
            "--input",
            str(benchmark),
            "--source-dir",
            str(root / "predictors/bigmhc/source"),
            "--python",
            str(root / "predictors/bigmhc/.venv/bin/python"),
            "--output",
            str(output_dir / "bigmhc-v1.0.csv"),
        ],
        "prime": [
            sys.executable,
            str(root / "predictors/prime/adapter.py"),
            "--input",
            str(benchmark),
            "--source-dir",
            str(root / "predictors/prime/source"),
            "--mix-dir",
            str(root / "predictors/prime/vendor/mixmhcpred"),
            "--output",
            str(output_dir / "prime-2.0.csv"),
        ],
        "deepimmuno": [
            str(root / "predictors/deepimmuno/.venv/bin/python"),
            str(root / "predictors/deepimmuno/adapter.py"),
            "--input", str(benchmark),
            "--source-dir", str(root / "predictors/deepimmuno/source"),
            "--output", str(output_dir / "deepimmuno-cnn.csv"),
        ],
        "deephlapan": [
            str(root / "predictors/deephlapan/.venv/bin/python"),
            str(root / "predictors/deephlapan/adapter.py"),
            "--input", str(benchmark),
            "--source-dir", str(root / "predictors/deephlapan/source"),
            "--output", str(output_dir / "deephlapan-1.1.1.csv"),
        ],
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validated_existing(
    name: str, command: list[str], benchmark_ids: list[str], output_dir: Path
) -> dict[str, object] | None:
    expected_predictor, expected_version, filename = EXPECTED[name]
    path = output_dir / filename
    if not path.is_file():
        return None
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error):
        return None
    if len(rows) != len(benchmark_ids):
        return None
    if [row.get("record_id") for row in rows] != benchmark_ids:
        return None
    if any(
        row.get("predictor") != expected_predictor
        or row.get("predictor_version") != expected_version
        or not row.get("status")
        or (row.get("status") == "predicted" and not row.get("score"))
        for row in rows
    ):
        return None
    print(f"reusing validated {name}: {len(rows)} rows", flush=True)
    return {
        "predictor": name,
        "command": command,
        "runtime_seconds": 0.0,
        "returncode": 0,
        "execution": "reused_validated",
        "rows": len(rows),
        "sha256": sha256(path),
    }


def run(name: str, command: list[str], root: Path) -> dict[str, object]:
    environment = os.environ.copy()
    # Python startup must decode the repository's Unicode path. PRIME's adapter
    # applies the C locale only to the upstream Perl/C++ subprocess that needs it.
    environment.update({"LC_ALL": "en_US.UTF-8", "LANG": "en_US.UTF-8"})
    print(f"starting {name}", flush=True)
    start = time.monotonic()
    result = subprocess.run(command, cwd=root, env=environment, check=False)
    elapsed = time.monotonic() - start
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
    print(f"completed {name}", flush=True)
    return {
        "predictor": name,
        "command": command,
        "runtime_seconds": elapsed,
        "returncode": 0,
        "execution": "executed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--predictors",
        nargs="+",
        choices=("mhcflurry", "bigmhc", "prime", "deepimmuno", "deephlapan"),
        default=("mhcflurry", "bigmhc", "prime"),
    )
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="reuse only outputs whose rows, IDs, model revision, status and scores validate",
    )
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    benchmark = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with benchmark.open(newline="", encoding="utf-8") as handle:
        benchmark_ids = [row["record_id"] for row in csv.DictReader(handle)]
    available = commands(root, benchmark, output_dir)
    selected = [(name, available[name]) for name in args.predictors]
    runs: list[dict[str, object]] = []
    pending = []
    for name, command in selected:
        existing = (
            validated_existing(name, command, benchmark_ids, output_dir)
            if args.reuse_existing
            else None
        )
        if existing is None:
            pending.append((name, command))
        else:
            runs.append(existing)
    if args.parallel:
        with ThreadPoolExecutor(max_workers=max(1, len(pending))) as executor:
            futures = [executor.submit(run, name, command, root) for name, command in pending]
            for future in futures:
                runs.append(future.result())
    else:
        for name, command in pending:
            runs.append(run(name, command, root))
    if args.receipt:
        artifacts = []
        for path in sorted(output_dir.glob("*.csv")):
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            artifacts.append(
                {
                    "path": str(path.relative_to(root)),
                    "rows": len(rows),
                    "predictor": rows[0]["predictor"],
                    "version": rows[0]["predictor_version"],
                    "sha256": sha256(path),
                }
            )
        receipt = {
            "completed_at": datetime.now(UTC).isoformat(),
            "platform": platform.platform(),
            "orchestrator_python": sys.version,
            "benchmark": str(benchmark.relative_to(root)),
            "parallel": args.parallel,
            "reuse_existing": args.reuse_existing,
            "runs": sorted(runs, key=lambda item: str(item["predictor"])),
            "artifacts": artifacts,
        }
        receipt_path = args.receipt.resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
