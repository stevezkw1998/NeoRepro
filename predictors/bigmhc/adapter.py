#!/usr/bin/env python3
"""Run pinned BigMHC EL and IM models without upstream HLA fuzzy matching."""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

VERSION = "v1.0"
REVISION = "9d84a3b4da77c9253ac90ff8cb629274003b90fd"
FIELDS = [
    "record_id",
    "predictor",
    "predictor_version",
    "task",
    "score",
    "score_direction",
    "status",
    "bigmhc_im",
    "bigmhc_el",
]


def uid(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scalar(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return "" if not math.isfinite(number) else f"{number:.12g}"


def run_model(
    python: Path, source_dir: Path, model: str, input_path: Path, output_path: Path
) -> list[dict[str, str]]:
    command = [
        str(python),
        "predict.py",
        f"-i={input_path}",
        f"-m={model}",
        "-a=0",
        "-p=1",
        "-c=1",
        "-d=cpu",
        "-j=1",
        "-f=2",
        "-v=0",
        f"-o={output_path}",
    ]
    environment = os.environ.copy()
    environment.update({"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    subprocess.run(
        command,
        cwd=source_dir / "src",
        env=environment,
        check=True,
        text=True,
    )
    return read_csv(output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/benchmark.csv"))
    parser.add_argument("--source-dir", type=Path, default=Path("predictors/bigmhc/source"))
    parser.add_argument("--python", type=Path, default=Path("predictors/bigmhc/.venv/bin/python"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/raw_predictions/bigmhc-v1.0.csv"),
    )
    args = parser.parse_args()
    source_dir = args.source_dir.resolve()
    # Keep the venv executable path itself. ``resolve()`` follows uv's symlink
    # to the base interpreter and drops the virtual environment at subprocess
    # startup, which makes installed packages such as Torch unavailable.
    python = args.python.absolute()

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != REVISION:
        raise RuntimeError(f"expected BigMHC {REVISION}, found {revision}")

    rows = read_csv(args.input)
    required = {"record_id", "peptide", "hla"}
    missing = required - set(rows[0] if rows else [])
    if missing:
        raise ValueError(f"missing input columns: {sorted(missing)}")
    supported_hlas = {uid(row["mhc"]) for row in read_csv(source_dir / "data/pseudoseqs.csv")}
    eligible = [
        row
        for row in rows
        if uid(row["hla"]) in supported_hlas and 8 <= len(row["peptide"]) <= 14
    ]

    by_id: dict[str, dict[str, str]] = {}
    if eligible:
        with tempfile.TemporaryDirectory(prefix="neorepro-bigmhc-") as temporary:
            work = Path(temporary)
            input_path = work / "input.csv"
            with input_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["mhc", "pep"], lineterminator="\n")
                writer.writeheader()
                writer.writerows({"mhc": row["hla"], "pep": row["peptide"]} for row in eligible)
            im_rows = run_model(python, source_dir, "im", input_path, work / "im.csv")
            el_rows = run_model(python, source_dir, "el", input_path, work / "el.csv")
            if len(im_rows) != len(eligible) or len(el_rows) != len(eligible):
                raise RuntimeError("BigMHC output row count differs from eligible input")
            for source, im_row, el_row in zip(eligible, im_rows, el_rows, strict=True):
                if (im_row["mhc"], im_row["pep"]) != (source["hla"], source["peptide"]):
                    raise RuntimeError("BigMHC IM changed input row identity")
                if (el_row["mhc"], el_row["pep"]) != (source["hla"], source["peptide"]):
                    raise RuntimeError("BigMHC EL changed input row identity")
                by_id[source["record_id"]] = {
                    "im": scalar(im_row["BigMHC_IM"]),
                    "el": scalar(el_row["BigMHC_EL"]),
                }

    output_rows = []
    for row in rows:
        values = by_id.get(row["record_id"], {"im": "", "el": ""})
        if uid(row["hla"]) not in supported_hlas:
            status = "unsupported_hla"
        elif not 8 <= len(row["peptide"]) <= 14:
            status = "unsupported_length"
        elif values["im"] and values["el"]:
            status = "predicted"
        else:
            status = "invalid_output"
        output_rows.append(
            {
                "record_id": row["record_id"],
                "predictor": "BigMHC",
                "predictor_version": VERSION,
                "task": "immunogenicity",
                "score": values["im"],
                "score_direction": "higher",
                "status": status,
                "bigmhc_im": values["im"],
                "bigmhc_el": values["el"],
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    predicted = sum(row["status"] == "predicted" for row in output_rows)
    print(f"BigMHC {VERSION}: {predicted}/{len(output_rows)} rows predicted -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
