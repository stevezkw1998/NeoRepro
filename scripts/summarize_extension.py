#!/usr/bin/env python3
"""Generate extension tables, figure, and a conservative evidence summary."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def f(value: object) -> str:
    return "NA" if value is None else f"{float(value):.3f}"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = load(root / "data/zhao_vaccine_summary.json")
    filtered = load(root / "data/zhao_vaccine_leakage_filter_summary.json")
    overlap = load(root / "research/training_overlap_summary_zhao.json")
    result = load(root / "results/analysis/zhao/fixed/metrics.json")
    improve = load(root / "results/analysis/improve/fixed/metrics.json")
    expanded = load(root / "results/analysis/improve/expanded_9_10/metrics.json")
    missingness: dict[str, dict[str, int]] = {}
    with (root / "results/analysis/zhao/fixed/missingness.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            missingness.setdefault(row["predictor"], {})[row["status"]] = int(row["count"])
    table = []
    evidence = []
    for name, values in sorted(result["metrics"].items()):
        predicted = sum(missingness.get(name, {}).values()) - sum(count for status, count in missingness.get(name, {}).items() if status != "predicted")
        patient = values["patient"]; pooled = values["pooled"]
        ci = values["patient_bootstrap_95ci"].get("ndcg@5", {})
        table.append({
            "predictor": name, "task": values["metadata"]["task"], "predicted": predicted,
            "coverage": predicted / filtered["retained_rows"], "auroc": pooled["auroc"],
            "average_precision": pooled["average_precision"], "ndcg@5": patient.get("ndcg@5"),
            "ndcg@5_ci_low": ci.get("low"), "ndcg@5_ci_high": ci.get("high"),
            "recall@5": patient.get("recall@5"), "mrr": patient.get("mrr"),
        })
        training = "unknown" if name == "DeepHLApan" else "known exact overlaps removed"
        evidence.append({
            "dataset": "Zhao-2026-vaccine", "predictor": name, "task": values["metadata"]["task"],
            "coverage": predicted / filtered["retained_rows"], "known_training_overlap": training,
            "primary_eligible": "yes" if values["metadata"]["task"] == "immunogenicity" else "no",
            "interpretation": "post-vaccination ELISPOT association; not natural presentation or clinical efficacy",
        })
    out = root / "results/tables"; out.mkdir(parents=True, exist_ok=True)
    with (out / "zhao_extension_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    with (out / "model_dataset_eligibility.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(evidence[0])); writer.writeheader(); writer.writerows(evidence)

    primary = [row for row in table if row["task"] == "immunogenicity"]
    ordered = sorted(primary, key=lambda row: float(row["ndcg@5"]), reverse=True)
    comparisons = [row for row in result["paired_same_task"] if row["metric"] == "ndcg@5"]
    pair_index = {(row["left"], row["right"]): row for row in comparisons}
    common_models = {}
    for name in ("BigMHC", "PRIME"):
        common_models[name] = {
            "improve_auroc": improve["metrics"][name]["pooled"]["auroc"],
            "zhao_auroc": result["metrics"][name]["pooled"]["auroc"],
            "improve_ndcg5": improve["metrics"][name]["patient"]["ndcg@5"],
            "zhao_ndcg5": result["metrics"][name]["patient"]["ndcg@5"],
        }
    machine = {
        "source": source, "filtered": filtered, "overlap": overlap,
        "primary_metric": "patient-macro NDCG@5", "ranking": ordered,
        "paired_ndcg5": comparisons, "cross_dataset": common_models,
    }
    reports = root / "reports"; reports.mkdir(parents=True, exist_ok=True)
    (reports / "extension_summary.json").write_text(json.dumps(machine, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Independent-cohort extension summary", "",
        (
            f"Zhao 2026 contributed {source['output_rows']:,} individually administered 8–11mer peptides from {source['patients']} patients. "
            f"After removing {filtered['excluded_rows']} known exact training overlaps, {filtered['retained_rows']:,} records, "
            f"{filtered['retained_positives']} positives, and {filtered['retained_positive_bearing_patients']} positive-bearing patients remained."
        ), "",
        "The endpoint is post-vaccination IFN-γ ELISPOT after peptide-pulsed dendritic-cell administration. It is a valid independent ranking test for this intervention context, but not evidence of natural tumor presentation, untreated intrinsic immunogenicity, tumor killing, or clinical benefit.", "",
        "## Frozen primary result", "",
        "| Predictor | Coverage | AUROC | AP | NDCG@5 (95% patient-bootstrap CI) | Recall@5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in ordered:
        lines.append(f"| {row['predictor']} | {row['coverage']:.1%} | {f(row['auroc'])} | {f(row['average_precision'])} | {f(row['ndcg@5'])} ({f(row['ndcg@5_ci_low'])}–{f(row['ndcg@5_ci_high'])}) | {f(row['recall@5'])} |")
    big_prime = pair_index[("BigMHC", "PRIME")]
    big_deephla = pair_index[("BigMHC", "DeepHLApan")]
    lines += [
        "",
        (
            f"On near-complete common support, BigMHC exceeded PRIME by {big_prime['difference_left_minus_right']:.3f} "
            f"NDCG@5 (95% CI {big_prime['ci_low']:.3f}–{big_prime['ci_high']:.3f}) and DeepHLApan by "
            f"{big_deephla['difference_left_minus_right']:.3f} ({big_deephla['ci_low']:.3f}–{big_deephla['ci_high']:.3f}). "
            "DeepImmuno-CNN's apparently larger marginal value is not a full-cohort win: it covered 43.8%, and its common-support differences from the other models were unresolved."
        ),
        "NDCG@5 is numerically high because the median patient had only six administered candidates; this is why cross-dataset NDCG magnitudes should not be compared directly.",
        "DeepHLApan training-set identity remains unknown because no official row-level manifest is public.",
        "", "## Cross-dataset check", "",
    ]
    for name, values in common_models.items():
        lines.append(f"- {name}: IMPROVE→Zhao AUROC {f(values['improve_auroc'])}→{f(values['zhao_auroc'])}; NDCG@5 {f(values['improve_ndcg5'])}→{f(values['zhao_ndcg5'])}.")
    lines += ["", "## Expanded IMPROVE 9–10mer model set", ""]
    for name in ("PRIME", "BigMHC", "DeepImmuno-CNN", "DeepHLApan"):
        values = expanded["metrics"][name]
        lines.append(
            f"- {name}: n={values['pooled']['n']:,}, AUROC {f(values['pooled']['auroc'])}, "
            f"patient NDCG@5 {f(values['patient']['ndcg@5'])}."
        )
    (reports / "extension_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        import matplotlib.pyplot as plt
        labels = [row["predictor"] for row in ordered]
        values = [row["ndcg@5"] for row in ordered]
        lows = [row["ndcg@5"] - row["ndcg@5_ci_low"] for row in ordered]
        highs = [row["ndcg@5_ci_high"] - row["ndcg@5"] for row in ordered]
        fig, ax = plt.subplots(figsize=(7.2, 3.8)); ax.barh(labels[::-1], values[::-1], color="#3366A6")
        ax.errorbar(values[::-1], labels[::-1], xerr=[lows[::-1], highs[::-1]], fmt="none", color="black", capsize=3)
        ax.set_xlabel("Patient-macro NDCG@5"); ax.set_title("Zhao 2026 vaccine cohort (known exact overlaps removed)")
        ax.grid(axis="x", alpha=.2); fig.tight_layout()
        figures = root / "results/figures"; figures.mkdir(parents=True, exist_ok=True)
        fig.savefig(figures / "zhao_extension_ndcg5.png", dpi=180); fig.savefig(figures / "zhao_extension_ndcg5.svg"); plt.close(fig)
    except ImportError:
        pass
    print(json.dumps({"models": len(table), "full_support_leader": "BigMHC"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
