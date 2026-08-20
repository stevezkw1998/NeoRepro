#!/usr/bin/env python3
"""Cross-check frozen NeoRepro pooled metrics against scikit-learn."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--output", type=Path, default=Path("reports/metric_validation.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    analyses = (
        (
            "results/analysis/improve/fixed/metrics.json",
            "results/raw_predictions/improve",
            "data/processed/improve_benchmark.csv",
        ),
        (
            "results/analysis/improve/baselines/lopo/metrics.json",
            "results/raw_predictions/improve/baselines/lopo",
            "data/processed/improve_benchmark.csv",
        ),
        (
            "results/analysis/improve/baselines/loso/metrics.json",
            "results/raw_predictions/improve/baselines/loso",
            "data/processed/improve_benchmark.csv",
        ),
        (
            "results/analysis/improve/peptide_sensitivity/metrics.json",
            "results/raw_predictions/improve/peptide_sensitivity",
            "data/processed/improve_patient_peptide_sensitivity.csv",
        ),
        (
            "results/analysis/improve/peptide_sensitivity_hla_rank/metrics.json",
            "results/raw_predictions/improve/peptide_sensitivity_hla_rank",
            "data/processed/improve_patient_peptide_hla_rank_sensitivity.csv",
        ),
        (
            "results/analysis/improve/exact_peptide_free/metrics.json",
            "data/sensitivity/exact_peptide_free/predictions",
            "data/sensitivity/exact_peptide_free/benchmark.csv",
        ),
        (
            "results/analysis/improve/near_overlap_free/metrics.json",
            "data/sensitivity/near_overlap_free/predictions",
            "data/sensitivity/near_overlap_free/benchmark.csv",
        ),
        (
            "results/analysis/improve/length_9_10/metrics.json",
            "data/sensitivity/length_9_10/predictions",
            "data/sensitivity/length_9_10/benchmark.csv",
        ),
    )
    checks = []
    for metric_relative, prediction_relative, benchmark_relative in analyses:
        benchmark = {
            row["record_id"]: int(row["immunogenicity"])
            for row in read_csv(root / benchmark_relative)
        }
        result = json.loads((root / metric_relative).read_text(encoding="utf-8"))
        for path in sorted((root / prediction_relative).glob("*.csv")):
            rows = read_csv(path)
            predictor = rows[0]["predictor"]
            labels = [benchmark[row["record_id"]] for row in rows]
            scores = [
                float(row["score"]) * (-1 if row["score_direction"] == "lower" else 1)
                for row in rows
            ]
            observed = {
                "auroc": float(roc_auc_score(labels, scores)),
                "average_precision": float(average_precision_score(labels, scores)),
            }
            expected = result["metrics"][predictor]["pooled"]
            maximum_error = max(abs(observed[key] - expected[key]) for key in observed)
            checks.append(
                {
                    "predictor": predictor,
                    "prediction_file": str(path.relative_to(root)),
                    "maximum_absolute_error": maximum_error,
                    "pass": maximum_error <= args.tolerance,
                }
            )
    report = {
        "status": "pass" if all(check["pass"] for check in checks) else "fail",
        "tolerance": args.tolerance,
        "checks": checks,
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
