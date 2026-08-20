#!/usr/bin/env python3
"""Hash frozen NeoRepro inputs and outputs into a machine-readable manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_PATHS = (
    "data/processed/improve_benchmark_full.csv",
    "data/processed/improve_benchmark.csv",
    "data/improve_summary.json",
    "data/improve_leakage_filter_summary.json",
    "data/improve_fixed_sensitivity_summary.json",
    "data/improve_patient_peptide_sensitivity_summary.json",
    "data/improve_patient_peptide_hla_rank_sensitivity_summary.json",
    "research/training_overlap_audit_improve.csv",
    "research/training_overlap_summary_improve.json",
    "results/raw_predictions/improve/mhcflurry-2.2.1.csv",
    "results/raw_predictions/improve/bigmhc-v1.0.csv",
    "results/raw_predictions/improve/prime-2.0.csv",
    "results/raw_predictions/improve/baselines/lopo/hla-only-lopo.csv",
    "results/raw_predictions/improve/baselines/lopo/peptide-lr-lopo.csv",
    "results/raw_predictions/improve/baselines/lopo/hla-peptide-lr-lopo.csv",
    "results/raw_predictions/improve/baselines/loso/hla-only-loso.csv",
    "results/raw_predictions/improve/baselines/loso/peptide-lr-loso.csv",
    "results/raw_predictions/improve/baselines/loso/hla-peptide-lr-loso.csv",
    "results/analysis/improve/fixed/metrics.json",
    "results/analysis/improve/baselines/lopo/metrics.json",
    "results/analysis/improve/baselines/loso/metrics.json",
    "results/analysis/improve/peptide_sensitivity/metrics.json",
    "results/analysis/improve/peptide_sensitivity_hla_rank/metrics.json",
    "results/analysis/improve/exact_peptide_free/metrics.json",
    "results/analysis/improve/near_overlap_free/metrics.json",
    "results/analysis/improve/length_9_10/metrics.json",
    "results/analysis/improve/lopo_folds.csv",
    "results/analysis/improve/loso_folds.csv",
    "results/analysis/improve/hla_sensitivity.csv",
    "results/analysis/improve/per_hla_metrics.csv",
    "reports/metric_validation.json",
    "reports/manuscript_audit.json",
    "reports/mhcflurry_model_manifest.json",
    "reports/full_predictor_run.json",
    "reports/prime_full_rerun.json",
    "results/final_results.csv",
    "results/tables/fixed_predictor_summary.csv",
    "results/tables/heldout_baseline_summary.csv",
    "results/figures/fixed_predictor_performance.png",
    "results/figures/heldout_baselines.png",
    "results/figures/hla_sensitivity.png",
    "results/figures/patient_recall20.png",
    "paper/manuscript.md",
    "paper/references.bib",
    "paper/reviewer_comments.md",
    "paper/reviewer_response.md",
    "FINAL_REPORT.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("results/manifest.json"))
    parser.add_argument("--path", action="append", dest="paths")
    args = parser.parse_args()
    root = args.root.resolve()
    paths = args.paths or DEFAULT_PATHS
    artifacts = []
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"missing manifest artifact: {relative}")
        artifacts.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    status = git_output(root, "status", "--porcelain")
    benchmark = read_csv(root / "data/processed/improve_benchmark.csv")
    filter_summary = json.loads(
        (root / "data/improve_leakage_filter_summary.json").read_text(encoding="utf-8")
    )
    source_summary = json.loads((root / "data/improve_summary.json").read_text(encoding="utf-8"))
    fixed_metrics = json.loads(
        (root / "results/analysis/improve/fixed/metrics.json").read_text(encoding="utf-8")
    )
    predictor_revisions = {}
    for path in (
        root / "results/raw_predictions/improve/mhcflurry-2.2.1.csv",
        root / "results/raw_predictions/improve/bigmhc-v1.0.csv",
        root / "results/raw_predictions/improve/prime-2.0.csv",
    ):
        row = read_csv(path)[0]
        predictor_revisions[row["predictor"]] = row["predictor_version"]
    predictor_revisions["IMPROVE data"] = source_summary["source_revision"]
    manifest = {
        "schema_version": "1.0",
        "generated_date": datetime.now(UTC).date().isoformat(),
        "project_commit": git_output(root, "rev-parse", "HEAD"),
        "project_worktree_clean": status == "",
        "benchmark": {
            "records": len(benchmark),
            "positives": sum(int(row["immunogenicity"]) for row in benchmark),
            "patients": len({row["patient_id"] for row in benchmark}),
            "studies": len({row["study_id"] for row in benchmark}),
            "exact_prime2_training_overlaps_excluded": filter_summary[
                "excluded_exact_prime2_peptide_hla_rows"
            ],
        },
        "predictor_revisions": predictor_revisions,
        "evaluation": {
            "bootstrap_replicates": fixed_metrics["config"]["bootstrap"],
            "seed": fixed_metrics["config"]["seed"],
            "top_k": fixed_metrics["config"]["ks"],
            "tie_policy": "analytic expectation over score ties",
        },
        "artifacts": artifacts,
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "artifacts": len(artifacts)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
