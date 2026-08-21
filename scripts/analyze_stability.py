#!/usr/bin/env python3
"""Descriptive cross-dataset stability and model-selection-risk analysis.

This intentionally treats fixed predictors as descriptive/exploratory. It does
not fit models, test causal hypotheses, or relabel unsupported predictions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from itertools import combinations
from pathlib import Path

KS = (1, 5, 10, 20)


def read_csv(p):
    with Path(p).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def auc(rows):
    x = sorted((float(r["score"]), int(r["label"])) for r in rows)
    pos = sum(y for _, y in x)
    neg = len(x) - pos
    if not pos or not neg:
        return None
    rank = 0
    s = 0
    i = 0
    while i < len(x):
        j = i + 1
        while j < len(x) and x[j][0] == x[i][0]:
            j += 1
        rank = (i + j + 1) / 2
        s += rank * sum(y for _, y in x[i:j])
        i = j
    return (s - pos * (pos + 1) / 2) / (pos * neg)


def patient_metric(rows, k):
    groups = defaultdict(list)
    for r in rows:
        groups[r["patient_id"]].append(r)
    vals = []
    for rs in groups.values():
        pos = sum(int(r["label"]) for r in rs)
        if not pos:
            continue
        rs = sorted(rs, key=lambda r: -float(r["score"]))
        top = rs[: min(k, len(rs))]
        hits = sum(int(r["label"]) for r in top)
        vals.append(hits / pos)
    return sum(vals) / len(vals) if vals else None


def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=v.__getitem__)
        out = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i + 1
            while j < len(v) and v[order[j]] == v[order[i]]:
                j += 1
            z = (i + j + 1) / 2
            for q in order[i:j]:
                out[q] = z
            i = j
        return out

    if len(a) < 2:
        return None
    ra, rb = rank(a), rank(b)
    ma = sum(ra) / len(ra)
    mb = sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--coverage", nargs="+", type=float, default=[0.5, 0.8, 0.95])
    ap.add_argument("--benchmark", nargs="+", required=True)
    ap.add_argument("--predictions", nargs="+")
    ap.add_argument("--prediction-dir", nargs="+")
    args = ap.parse_args()
    if args.prediction_dir and len(args.prediction_dir) != len(args.benchmark):
        ap.error("prediction-dir count must match benchmark count")
    if not args.prediction_dir and (
        not args.predictions or len(args.benchmark) != len(args.predictions)
    ):
        ap.error("provide aligned predictions or prediction-dir per benchmark")
    datasets = {}
    meta = {}
    for idx, bp in enumerate(args.benchmark):
        prediction_paths = (
            sorted(Path(args.prediction_dir[idx]).glob("*.csv"))
            if args.prediction_dir
            else [Path(args.predictions[idx])]
        )
        for pp in prediction_paths:
            b = {r["record_id"]: r for r in read_csv(bp)}
            prs = read_csv(pp)
            pred = prs[0]["predictor"]
            rows = []
            status = defaultdict(int)
            for p in prs:
                status[p["status"]] += 1
                if p["status"] == "predicted":
                    r = b[p["record_id"]]
                    score = float(p["score"])
                    score = score if p["score_direction"] == "higher" else -score
                    rows.append(
                        {
                            "record_id": p["record_id"],
                            "patient_id": r["patient_id"],
                            "study_id": r["study_id"],
                            "hla": r["hla"],
                            "label": int(r["immunogenicity"]),
                            "score": score,
                        }
                    )
            datasets.setdefault(Path(bp).stem, {})[pred] = rows
            meta[pred] = {
                "task": prs[0]["task"],
                "version": prs[0]["predictor_version"],
                "status": dict(status),
            }
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    matrix = []
    rank_rows = []
    first_rows = []
    sens = []
    lodo = []
    domain_meta = []
    for ds, preds in datasets.items():
        supports = [{r["record_id"] for r in rs} for rs in preds.values()]
        common = set.intersection(*supports)
        benchmark_rows = read_csv(next(bp for bp in args.benchmark if Path(bp).stem == ds))
        domain_meta.append(
            {
                "dataset": ds,
                "endpoint": benchmark_rows[0].get("assay_type", "unknown"),
                "clinical_context": benchmark_rows[0].get("clinical_context", "unknown"),
                "n_records": len(benchmark_rows),
                "n_patients": len({r["patient_id"] for r in benchmark_rows}),
                "n_studies": len({r["study_id"] for r in benchmark_rows}),
            }
        )
        for pred, rs in preds.items():
            rr = [r for r in rs if r["record_id"] in common]
            matrix += [
                {
                    "dataset": ds,
                    "predictor": pred,
                    "metric": "AUROC",
                    "value": auc(rr),
                    "n": len(rr),
                    "coverage": len(rr)
                    / len(read_csv(next(bp for bp in args.benchmark if Path(bp).stem == ds))),
                }
            ]
            for k in KS:
                matrix.append(
                    {
                        "dataset": ds,
                        "predictor": pred,
                        "metric": f"Recall@{k}",
                        "value": patient_metric(rr, k),
                        "n": len(rr),
                        "coverage": len(rr)
                        / len(read_csv(next(bp for bp in args.benchmark if Path(bp).stem == ds))),
                    }
                )
        study_ids = sorted({r["study_id"] for r in benchmark_rows})
        for held_out in study_ids:
            for pred, rs in preds.items():
                rr = [r for r in rs if r["record_id"] in common and r["study_id"] != held_out]
                lodo.append(
                    {
                        "dataset": ds,
                        "held_out_domain": held_out,
                        "predictor": pred,
                        "metric": "AUROC",
                        "value": auc(rr),
                        "n": len(rr),
                        "patients": len({r["patient_id"] for r in rr}),
                        "analysis_type": "descriptive_leave_one_domain_out",
                    }
                )
        pairs = list(combinations(sorted(preds), 2))
        byid = {p: {r["record_id"]: r for r in preds[p]} for p in preds}
        for a, bp in pairs:
            ids = sorted(set(byid[a]) & set(byid[bp]))
            ra = [byid[a][i] for i in ids]
            rb = [byid[bp][i] for i in ids]
            rank_rows.append(
                {
                    "dataset": ds,
                    "left": a,
                    "right": bp,
                    "metric": "record_score_spearman",
                    "value": spearman([r["score"] for r in ra], [r["score"] for r in rb]),
                    "n": len(ids),
                }
            )
            for k in KS:
                av = patient_metric(ra, k)
                bv = patient_metric(rb, k)
                rank_rows.append(
                    {
                        "dataset": ds,
                        "left": a,
                        "right": bp,
                        "metric": f"patient_Recall@{k}_difference",
                        "value": av - bv if av is not None and bv is not None else None,
                        "n": len(ids),
                    }
                )
        patients = sorted({r["patient_id"] for r in next(iter(preds.values()))})
        rng = random.Random(args.seed)
        wins = defaultdict(int)
        reversals = defaultdict(int)
        task_groups = defaultdict(list)
        for p in preds:
            task_groups[meta[p]["task"]].append(p)
        for _ in range(args.bootstrap):
            draw = rng.choices(patients, k=len(patients))
            vals = {}
            for p, rs in preds.items():
                by = defaultdict(list)
                for r in rs:
                    by[r["patient_id"]].append(r)
                boot = []
                for i, pt in enumerate(draw):
                    boot += [{**r, "patient_id": f"{i}:{pt}"} for r in by[pt]]
                vals[p] = patient_metric(boot, 5) or float("nan")
            for task, group in task_groups.items():
                finite = {p: vals[p] for p in group if math.isfinite(vals[p])}
                if finite:
                    top = max(finite.values())
                    [
                        wins.__setitem__((task, p), wins[(task, p)] + 1)
                        for p, v in finite.items()
                        if v == top
                    ]
            if (
                "BigMHC" in vals
                and "PRIME" in vals
                and math.isfinite(vals["BigMHC"])
                and math.isfinite(vals["PRIME"])
            ):
                reversals["BigMHC_vs_PRIME"] += int((vals["BigMHC"] - vals["PRIME"]) < 0)
        for task, group in task_groups.items():
            for p in group:
                first_rows.append(
                    {
                        "dataset": ds,
                        "task": task,
                        "predictor": p,
                        "metric": "Recall@5",
                        "probability_first": wins[(task, p)] / args.bootstrap,
                    }
                )
        for key, v in reversals.items():
            sens.append(
                {
                    "dataset": ds,
                    "comparison": key,
                    "metric": "probability_BigMHC_below_PRIME",
                    "value": v / args.bootstrap,
                    "strategy": "common_support",
                    "k": 5,
                }
            )
    for c in args.coverage:
        for ds, preds in datasets.items():
            total = len(read_csv(next(bp for bp in args.benchmark if Path(bp).stem == ds)))
            eligible = {p: rs for p, rs in preds.items() if len(rs) / total >= c}
            eligible_supports = [{r["record_id"] for r in rs} for rs in eligible.values()]
            union = set.intersection(*eligible_supports) if eligible_supports else set()
            sens.append(
                {
                    "dataset": ds,
                    "comparison": "coverage_filtered_predictors",
                    "metric": "common_support_n",
                    "value": len(union),
                    "strategy": f"coverage_threshold_{c}",
                    "predictors_in_support": "|".join(sorted(eligible)),
                    "k": 5,
                }
            )

    def write(name, rows):
        if not rows:
            return
        fields = sorted({k for r in rows for k in r})
        with (out / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    write("dataset_predictor_metric_matrix.csv", matrix)
    write("rank_stability.csv", rank_rows)
    write("model_selection_first_probability.csv", first_rows)
    write("sensitivity_summary.csv", sens)
    write("leave_one_domain_out.csv", lodo)
    write("endpoint_domain_metadata.csv", domain_meta)
    try:
        import matplotlib.pyplot as plt

        labels = [f"{r['dataset']}\n{r['endpoint']}" for r in domain_meta]
        names = sorted({r["predictor"] for r in matrix})
        vals = []
        for name in names:
            vals.append(
                [
                    next(
                        (
                            float(r["value"])
                            for r in matrix
                            if r["dataset"] == d["dataset"]
                            and r["predictor"] == name
                            and r["metric"] == "AUROC"
                        ),
                        float("nan"),
                    )
                    for d in domain_meta
                ]
            )
        fig, ax = plt.subplots(figsize=(8, 3.8))
        im = ax.imshow(vals, aspect="auto", vmin=0, vmax=1, cmap="viridis")
        ax.set_yticks(range(len(names)), names)
        ax.set_xticks(range(len(labels)), labels, rotation=20, ha="right")
        ax.set_title("Exploratory AUROC by endpoint/domain and predictor")
        fig.colorbar(im, ax=ax, label="AUROC")
        fig.tight_layout()
        fig.savefig(out / "endpoint_domain_auroc.png", dpi=180)
        fig.savefig(out / "endpoint_domain_auroc.svg")
        plt.close(fig)
    except (ImportError, ModuleNotFoundError) as exc:
        (out / "visualization_error.txt").write_text(f"matplotlib unavailable: {exc}\n")
    (out / "analysis_metadata.json").write_text(
        json.dumps(
            {
                "analysis_type": "exploratory_descriptive_heterogeneity",
                "bootstrap": args.bootstrap,
                "seed": args.seed,
                "ks": KS,
                "coverage_thresholds": args.coverage,
                "datasets": list(datasets),
                "predictors": meta,
                "limitations": [
                    "fixed pretrained scores; no causal inference",
                    "model-selection probabilities are conditional on observed patient samples",
                    "coverage strategies are descriptive and not multiplicity-adjusted",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "output_dir": str(out),
                "datasets": list(datasets),
                "matrix_rows": len(matrix),
                "bootstrap": args.bootstrap,
            }
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
