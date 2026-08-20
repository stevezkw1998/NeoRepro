#!/usr/bin/env python3
"""Create a common benchmark subset after a versioned row-level overlap audit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    benchmark = read_csv(args.benchmark)
    audit = {row["record_id"]: row for row in read_csv(args.audit)}
    if set(audit) != {row["record_id"] for row in benchmark}:
        raise ValueError("overlap audit does not cover the benchmark exactly")
    excluded = {
        record_id
        for record_id, row in audit.items()
        if row["exact_peptide_hla_in_prime2_train"] == "1"
    }
    retained = [row for row in benchmark if row["record_id"] not in excluded]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(retained[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(retained)
    summary = {
        "input_rows": len(benchmark),
        "excluded_exact_prime2_peptide_hla_rows": len(excluded),
        "retained_rows": len(retained),
        "retained_patients": len({row["patient_id"] for row in retained}),
        "retained_studies": len({row["study_id"] for row in retained}),
        "retained_positives": sum(int(row["immunogenicity"]) for row in retained),
        "policy": "union exclusion for a common PRIME2/BigMHC evaluation set",
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
