#!/usr/bin/env python3
"""Build exact-peptide-free, near-overlap-free and 9–10mer sensitivity subsets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    benchmark = read_csv(args.benchmark)
    audit = {row["record_id"]: row for row in read_csv(args.audit)}
    subsets = {
        "exact_peptide_free": [
            row for row in benchmark if audit[row["record_id"]]["peptide_in_prime2_train"] == "0"
        ],
        "near_overlap_free": [
            row
            for row in benchmark
            if audit[row["record_id"]]["near_hamming1_same_hla_prime2_train"] == "0"
        ],
        "length_9_10": [row for row in benchmark if int(row["peptide_length"]) in {9, 10}],
    }
    prediction_rows = {path: read_csv(path) for path in args.predictions}
    summary = {}
    for name, rows in subsets.items():
        ids = {row["record_id"] for row in rows}
        write_csv(args.output_root / name / "benchmark.csv", rows)
        for path, predictions in prediction_rows.items():
            selected = [row for row in predictions if row["record_id"] in ids]
            if len(selected) != len(rows):
                raise SystemExit(f"{path}: incomplete {name} predictions")
            write_csv(args.output_root / name / "predictions" / path.name, selected)
        summary[name] = {
            "rows": len(rows),
            "positives": sum(int(row["immunogenicity"]) for row in rows),
            "patients": len({row["patient_id"] for row in rows}),
            "excluded_from_common_benchmark": len(benchmark) - len(rows),
        }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
