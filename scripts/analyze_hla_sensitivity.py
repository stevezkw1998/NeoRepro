#!/usr/bin/env python3
"""Quantify how much fixed-predictor conclusions depend on HLA composition."""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from neorepro.metrics import auroc, average_precision


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for index in order[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def hla_normalized_scores(hlas: list[str], scores: list[float]) -> list[float]:
    indices: dict[str, list[int]] = defaultdict(list)
    for index, hla in enumerate(hlas):
        indices[hla].append(index)
    normalized = [0.0] * len(scores)
    for group in indices.values():
        group_ranks = average_ranks([scores[index] for index in group])
        for index, rank in zip(group, group_ranks, strict=True):
            normalized[index] = rank / (len(group) + 1)
    return normalized


def hla_means(hlas: list[str], scores: list[float]) -> list[float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for hla, score in zip(hlas, scores, strict=True):
        grouped[hla].append(score)
    lookup = {hla: mean(values) for hla, values in grouped.items()}
    return [lookup[hla] for hla in hlas]


def variance_explained(hlas: list[str], scores: list[float]) -> float:
    overall = mean(scores)
    grouped: dict[str, list[float]] = defaultdict(list)
    for hla, score in zip(hlas, scores, strict=True):
        grouped[hla].append(score)
    total = sum((score - overall) ** 2 for score in scores)
    between = sum(len(values) * (mean(values) - overall) ** 2 for values in grouped.values())
    return between / total if total else 0.0


def fixed_score_metric_inputs(scores: list[float]) -> tuple[list[float], list[list[int]]]:
    ranks = average_ranks(scores)
    order = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
    score_groups = []
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and scores[order[end]] == scores[order[start]]:
            end += 1
        score_groups.append(order[start:end])
        start = end
    return ranks, score_groups


def fixed_score_metrics(
    labels: list[int], ranks: list[float], score_groups: list[list[int]]
) -> tuple[float, float]:
    positives = sum(labels)
    negatives = len(labels) - positives
    positive_rank_sum = sum(rank for rank, label in zip(ranks, labels, strict=True) if label)
    auc = (positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
    true_positives = 0
    predicted_positives = 0
    ap = 0.0
    for group in score_groups:
        group_positives = sum(labels[index] for index in group)
        true_positives += group_positives
        predicted_positives += len(group)
        ap += (group_positives / positives) * (true_positives / predicted_positives)
    return auc, ap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-hla-output", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260820)
    args = parser.parse_args()
    benchmark = {row["record_id"]: row for row in read_csv(args.benchmark)}
    summary_rows = []
    per_hla_rows = []
    for path in args.predictions:
        predictions = read_csv(path)
        predictor = predictions[0]["predictor"]
        rows = [row for row in predictions if row["status"] == "predicted"]
        labels = [int(benchmark[row["record_id"]]["immunogenicity"]) for row in rows]
        hlas = [benchmark[row["record_id"]]["hla"] for row in rows]
        patients = [benchmark[row["record_id"]]["patient_id"] for row in rows]
        studies = [benchmark[row["record_id"]]["study_id"] for row in rows]
        scores = [float(row["score"]) for row in rows]
        if predictions[0]["score_direction"] == "lower":
            scores = [-score for score in scores]
        normalized = hla_normalized_scores(hlas, scores)
        between_only = hla_means(hlas, scores)
        raw_auroc = auroc(labels, scores)
        raw_ap = average_precision(labels, scores)
        raw_ranks, raw_score_groups = fixed_score_metric_inputs(scores)
        rng = random.Random(args.seed)
        groups: dict[str, list[int]] = defaultdict(list)
        for index, hla in enumerate(hlas):
            groups[hla].append(index)
        null_aurocs = []
        null_aps = []
        for _ in range(args.permutations):
            shuffled_labels = labels.copy()
            for indices in groups.values():
                values = [shuffled_labels[index] for index in indices]
                rng.shuffle(values)
                for index, value in zip(indices, values, strict=True):
                    shuffled_labels[index] = value
            null_auroc, null_ap = fixed_score_metrics(shuffled_labels, raw_ranks, raw_score_groups)
            null_aurocs.append(null_auroc)
            null_aps.append(null_ap)
        summary_rows.append(
            {
                "predictor": predictor,
                "n": len(rows),
                "raw_auroc": raw_auroc,
                "raw_average_precision": raw_ap,
                "within_hla_rank_auroc": auroc(labels, normalized),
                "within_hla_rank_average_precision": average_precision(labels, normalized),
                "between_hla_mean_auroc": auroc(labels, between_only),
                "between_hla_mean_average_precision": average_precision(labels, between_only),
                "score_variance_explained_by_hla": variance_explained(hlas, scores),
                "within_hla_permutation_p_auroc": (
                    1 + sum(value >= raw_auroc for value in null_aurocs)
                )
                / (args.permutations + 1),
                "within_hla_permutation_p_average_precision": (
                    1 + sum(value >= raw_ap for value in null_aps)
                )
                / (args.permutations + 1),
            }
        )
        for hla, indices in sorted(groups.items()):
            hla_labels = [labels[index] for index in indices]
            hla_scores = [scores[index] for index in indices]
            positives = sum(hla_labels)
            negatives = len(hla_labels) - positives
            per_hla_rows.append(
                {
                    "predictor": predictor,
                    "hla": hla,
                    "n": len(indices),
                    "positives": positives,
                    "patients": len({patients[index] for index in indices}),
                    "studies": len({studies[index] for index in indices}),
                    "supported_for_interpretation": int(
                        positives >= 3 and len({patients[index] for index in indices}) >= 3
                    ),
                    "auroc": auroc(hla_labels, hla_scores) if positives and negatives else "",
                    "average_precision": average_precision(hla_labels, hla_scores)
                    if positives
                    else "",
                }
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)
    args.per_hla_output.parent.mkdir(parents=True, exist_ok=True)
    with args.per_hla_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_hla_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(per_hla_rows)
    print(f"wrote HLA sensitivity for {len(summary_rows)} predictors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
