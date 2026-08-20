#!/usr/bin/env python3
"""Generate manuscript tables and figures directly from frozen NeoRepro results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

plt.rcParams["svg.hashsalt"] = "neorepro-20260820"


def load_metrics(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_rows(result: dict, analysis: str) -> list[dict[str, object]]:
    rows = []
    for predictor, values in result["metrics"].items():
        pooled = values["pooled"]
        patient = values["patient"]
        intervals = values["patient_bootstrap_95ci"]
        row: dict[str, object] = {
            "analysis": analysis,
            "predictor": predictor,
            "task": values["metadata"]["task"],
            "n": pooled["n"],
            "positives": pooled["positives"],
            "auroc": pooled["auroc"],
            "average_precision": pooled["average_precision"],
            "brier": pooled["brier"],
            "positive_bearing_patients": patient["positive_bearing_patients"],
        }
        for metric in ("recall@5", "recall@10", "recall@20", "mrr", "ndcg@10"):
            row[metric] = patient[metric]
            row[f"{metric}_ci_low"] = intervals[metric]["low"]
            row[f"{metric}_ci_high"] = intervals[metric]["high"]
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output_dir / f"{stem}.png",
        dpi=240,
        bbox_inches="tight",
        metadata={"Software": "NeoRepro"},
    )
    fig.savefig(
        output_dir / f"{stem}.svg",
        bbox_inches="tight",
        metadata={"Creator": "NeoRepro", "Date": "2026-08-20"},
    )
    plt.close(fig)


def fixed_figure(rows: list[dict[str, object]], output_dir: Path) -> None:
    frame = pd.DataFrame(rows).sort_values("auroc")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    colors = ["#4C78A8" if task == "presentation" else "#F58518" for task in frame["task"]]
    axes[0].barh(frame["predictor"], frame["auroc"], color=colors)
    axes[0].axvline(0.5, color="0.35", linestyle="--", linewidth=1)
    axes[0].set(xlabel="Pooled AUROC", xlim=(0.45, 0.66))
    axes[1].barh(frame["predictor"], frame["average_precision"], color=colors)
    prevalence = frame["positives"].iloc[0] / frame["n"].iloc[0]
    axes[1].axvline(prevalence, color="0.35", linestyle="--", linewidth=1)
    axes[1].set(xlabel="Pooled average precision", ylabel="")
    axes[1].tick_params(axis="y", labelleft=False)
    fig.suptitle("Fixed public predictors on the overlap-filtered IMPROVE benchmark")
    fig.text(0.5, -0.03, "Blue: presentation score; orange: immunogenicity score. Dashed lines: null/reference.", ha="center", fontsize=8)
    fig.tight_layout()
    save_figure(fig, output_dir, "fixed_predictor_performance")


def baseline_figure(rows: list[dict[str, object]], output_dir: Path) -> None:
    frame = pd.DataFrame(rows)
    frame["split"] = frame["analysis"].str.upper()
    frame["model"] = frame["predictor"].str.replace(r" (LOPO|LOSO)$", "", regex=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0))
    sns.barplot(data=frame, x="auroc", y="model", hue="split", ax=axes[0], palette="colorblind")
    axes[0].axvline(0.5, color="0.35", linestyle="--", linewidth=1)
    axes[0].set(xlabel="Pooled AUROC", ylabel="")
    sns.barplot(data=frame, x="recall@20", y="model", hue="split", ax=axes[1], palette="colorblind")
    axes[1].set(xlabel="Mean patient Recall@20", ylabel="")
    if axes[1].legend_:
        axes[1].legend_.remove()
    axes[0].legend(title="Held-out unit")
    fig.suptitle("Transparent baselines under patient- and study-held-out evaluation")
    fig.tight_layout()
    save_figure(fig, output_dir, "heldout_baselines")


def patient_recall_figure(result: dict, output_dir: Path) -> None:
    matrix = {
        predictor: {patient: values["recall@20"] for patient, values in metrics["patient_values"].items()}
        for predictor, metrics in result["metrics"].items()
    }
    frame = pd.DataFrame(matrix).fillna(0.0)
    frame["mean"] = frame.mean(axis=1)
    frame = frame.sort_values("mean", ascending=False).drop(columns="mean").T
    fig, ax = plt.subplots(figsize=(14, 2.7))
    sns.heatmap(frame, cmap="viridis", vmin=0, vmax=1, ax=ax, cbar_kws={"label": "Recall@20"})
    ax.set(xlabel="Positive-bearing patient (ordered by mean pMHC-pair recall)", ylabel="")
    ax.set_xticks([])
    ax.set_title("Patient-level pMHC-pair retrieval is heterogeneous")
    fig.tight_layout()
    save_figure(fig, output_dir, "patient_recall20")


def hla_figure(path: Path, output_dir: Path) -> None:
    frame = pd.read_csv(path)
    long = frame.melt(
        id_vars=["predictor"],
        value_vars=["raw_auroc", "within_hla_rank_auroc", "between_hla_mean_auroc"],
        var_name="analysis",
        value_name="auroc",
    )
    labels = {
        "raw_auroc": "Raw scores",
        "within_hla_rank_auroc": "Within-HLA ranks",
        "between_hla_mean_auroc": "HLA means only",
    }
    long["analysis"] = long["analysis"].map(labels)
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 3.7))
    sns.barplot(data=long, x="predictor", y="auroc", hue="analysis", ax=axes[0], palette="colorblind")
    axes[0].axhline(0.5, color="0.35", linestyle="--", linewidth=1)
    axes[0].set(xlabel="", ylabel="AUROC", ylim=(0.44, 0.63))
    axes[0].legend(title="Score view", fontsize=8)
    sns.barplot(data=frame, x="predictor", y="score_variance_explained_by_hla", ax=axes[1], color="#72B7B2")
    axes[1].set(xlabel="", ylabel="Score variance explained by HLA")
    fig.suptitle("HLA-stratified sensitivity analysis")
    fig.tight_layout()
    save_figure(fig, output_dir, "hla_sensitivity")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed", type=Path, required=True)
    parser.add_argument("--lopo", type=Path, required=True)
    parser.add_argument("--loso", type=Path, required=True)
    parser.add_argument("--hla", type=Path, required=True)
    parser.add_argument("--table-dir", type=Path, default=Path("results/tables"))
    parser.add_argument("--figure-dir", type=Path, default=Path("results/figures"))
    parser.add_argument("--final-results", type=Path, default=Path("results/final_results.csv"))
    args = parser.parse_args()

    sns.set_theme(style="whitegrid", context="notebook")
    fixed = load_metrics(args.fixed)
    lopo = load_metrics(args.lopo)
    loso = load_metrics(args.loso)
    fixed_rows = metric_rows(fixed, "fixed")
    baseline_rows = metric_rows(lopo, "lopo") + metric_rows(loso, "loso")
    write_csv(args.table_dir / "fixed_predictor_summary.csv", fixed_rows)
    write_csv(args.table_dir / "heldout_baseline_summary.csv", baseline_rows)
    write_csv(args.table_dir / "fixed_paired_differences.csv", fixed["paired_same_task"])
    write_csv(args.final_results, fixed_rows + baseline_rows)
    fixed_figure(fixed_rows, args.figure_dir)
    baseline_figure(baseline_rows, args.figure_dir)
    patient_recall_figure(fixed, args.figure_dir)
    hla_figure(args.hla, args.figure_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
