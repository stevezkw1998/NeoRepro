#!/usr/bin/env python3
"""Apply a common union exclusion from a row-level training-overlap audit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--column", default="union_known_exact_overlap")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    benchmark = rows(args.benchmark)
    audit_rows = rows(args.audit)
    audit = {row["record_id"]: row for row in audit_rows}
    if len(audit) != len(audit_rows) or set(audit) != {row["record_id"] for row in benchmark}:
        raise ValueError("overlap audit and benchmark record identifiers differ")
    if audit_rows and args.column not in audit_rows[0]:
        raise ValueError(f"audit lacks exclusion column {args.column}")
    kept = [row for row in benchmark if int(audit[row["record_id"]][args.column]) == 0]
    excluded = [row for row in benchmark if int(audit[row["record_id"]][args.column]) != 0]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(benchmark[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept)
    summary = {
        "source_rows": len(benchmark),
        "exclusion_column": args.column,
        "excluded_rows": len(excluded),
        "excluded_positives": sum(int(row["immunogenicity"]) for row in excluded),
        "retained_rows": len(kept),
        "retained_positives": sum(int(row["immunogenicity"]) for row in kept),
        "retained_patients": len({row["patient_id"] for row in kept}),
        "retained_positive_bearing_patients": len(
            {
                row["patient_id"]
                for row in kept
                if int(row["immunogenicity"])
            }
        ),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
