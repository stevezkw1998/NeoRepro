#!/usr/bin/env python3
"""Aggregate pMHC records to patient–peptide candidates for a sensitivity analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def candidate_id(patient: str, peptide: str) -> str:
    digest = hashlib.sha256(f"{patient}\t{peptide}".encode()).hexdigest()[:20]
    return f"IMPROVE-PEPTIDE-{digest}"


def mid_percentiles(values: list[float]) -> list[float]:
    """Return empirical mid-percentiles with identical values assigned identical ranks."""
    counts: dict[float, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    less = 0
    percentile = {}
    for value, count in sorted(counts.items()):
        percentile[value] = (less + 0.5 * count) / len(values)
        less += count
    return [percentile[value] for value in values]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--benchmark-output", type=Path, required=True)
    parser.add_argument("--prediction-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument(
        "--score-aggregation",
        choices=("raw-max", "within-hla-percentile-max"),
        default="raw-max",
    )
    args = parser.parse_args()

    benchmark_rows = read_csv(args.benchmark)
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in benchmark_rows:
        groups[(row["patient_id"], row["peptide"])].append(row)

    aggregated = []
    record_to_candidate = {}
    discordant = 0
    for (patient, peptide), rows in sorted(groups.items()):
        labels = {int(row["immunogenicity"]) for row in rows}
        discordant += len(labels) > 1
        first = rows[0].copy()
        first["record_id"] = candidate_id(patient, peptide)
        first["immunogenicity"] = max(labels)
        first["hla"] = "MULTI" if len({row["hla"] for row in rows}) > 1 else rows[0]["hla"]
        first["evidence_level"] = (
            "patient-peptide sensitivity unit; positive if any tested HLA record was positive"
        )
        aggregated.append(first)
        for row in rows:
            record_to_candidate[row["record_id"]] = first["record_id"]
    write_csv(args.benchmark_output, aggregated)
    benchmark_by_id = {row["record_id"]: row for row in benchmark_rows}

    for path in args.predictions:
        rows = read_csv(path)
        if not rows:
            raise SystemExit(f"empty prediction file: {path}")
        oriented_scores = []
        for row in rows:
            if row["status"] != "predicted":
                raise SystemExit(f"peptide sensitivity requires complete predictions: {path}")
            score = float(row["score"])
            if row["score_direction"] == "lower":
                score = -score
            oriented_scores.append(score)
        if args.score_aggregation == "within-hla-percentile-max":
            indices_by_hla: dict[str, list[int]] = defaultdict(list)
            for index, row in enumerate(rows):
                indices_by_hla[benchmark_by_id[row["record_id"]]["hla"]].append(index)
            normalized_scores = [0.0] * len(rows)
            for indices in indices_by_hla.values():
                percentiles = mid_percentiles([oriented_scores[index] for index in indices])
                for index, percentile in zip(indices, percentiles):
                    normalized_scores[index] = percentile
            oriented_scores = normalized_scores
        by_candidate: dict[str, list[float]] = defaultdict(list)
        for row, score in zip(rows, oriented_scores):
            by_candidate[record_to_candidate[row["record_id"]]].append(score)
        reason = (
            "max within-HLA empirical mid-percentile across tested HLA records"
            if args.score_aggregation == "within-hla-percentile-max"
            else "max oriented score across tested HLA records"
        )
        output_rows = []
        for row in aggregated:
            candidate = row["record_id"]
            output_rows.append(
                {
                    "record_id": candidate,
                    "predictor": rows[0]["predictor"],
                    "predictor_version": rows[0]["predictor_version"],
                    "task": rows[0]["task"],
                    "score": max(by_candidate[candidate]),
                    "score_direction": "higher",
                    "status": "predicted",
                    "reason": reason,
                }
            )
        write_csv(args.prediction_dir / path.name, output_rows)

    hla_counts = [len({row["hla"] for row in rows}) for rows in groups.values()]
    summary = {
        "aggregation_unit": "patient-peptide",
        "label_rule": "positive if any tested peptide-HLA record was positive",
        "score_rule": args.score_aggregation,
        "input_pmhc_records": len(benchmark_rows),
        "patient_peptide_candidates": len(groups),
        "multi_hla_candidates": sum(count > 1 for count in hla_counts),
        "records_in_multi_hla_candidates": sum(
            len(rows) for rows in groups.values() if len({row["hla"] for row in rows}) > 1
        ),
        "discordant_hla_label_candidates": discordant,
        "positives": sum(int(row["immunogenicity"]) for row in aggregated),
        "patients": len({row["patient_id"] for row in aggregated}),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
