"""Small, dependency-free metric primitives used by fixtures and the pilot."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def _validate(labels: Sequence[int], scores: Sequence[float]) -> None:
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must have equal non-zero length")
    if any(label not in {0, 1} for label in labels):
        raise ValueError("labels must be binary")
    if any(not math.isfinite(score) for score in scores):
        raise ValueError("scores must be finite")


def auroc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Compute AUROC with average ranks for ties."""
    _validate(labels, scores)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("AUROC requires both classes")
    order = sorted(range(len(scores)), key=scores.__getitem__)
    ranks = [0.0] * len(scores)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and scores[order[end]] == scores[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for index in order[start:end]:
            ranks[index] = rank
        start = end
    positive_rank_sum = sum(rank for rank, label in zip(ranks, labels, strict=True) if label)
    return (positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def average_precision(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Compute non-interpolated average precision."""
    _validate(labels, scores)
    positives = sum(labels)
    if not positives:
        raise ValueError("average precision requires a positive label")
    hits = 0
    precisions: list[float] = []
    for rank, (_, label) in enumerate(sorted(zip(scores, labels), reverse=True), start=1):
        hits += label
        if label:
            precisions.append(hits / rank)
    return sum(precisions) / positives


def ranking_metrics(labels_in_rank_order: Sequence[int], ks: Iterable[int]) -> dict[str, float]:
    """Compute Top-K metrics for one positive-bearing patient."""
    if not labels_in_rank_order or any(label not in {0, 1} for label in labels_in_rank_order):
        raise ValueError("ranked labels must be a non-empty binary sequence")
    positives = sum(labels_in_rank_order)
    if not positives:
        raise ValueError("ranking recall requires a positive-bearing patient")
    first_positive = labels_in_rank_order.index(1) + 1
    result = {"mrr": 1 / first_positive}
    for k in ks:
        if k <= 0:
            raise ValueError("K must be positive")
        top = labels_in_rank_order[:k]
        hits = sum(top)
        result[f"recall@{k}"] = hits / positives
        result[f"precision@{k}"] = hits / len(top)
        result[f"hitrate@{k}"] = float(hits > 0)
        dcg = sum(label / math.log2(rank + 1) for rank, label in enumerate(top, start=1))
        ideal_hits = min(positives, len(top))
        idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        result[f"ndcg@{k}"] = dcg / idcg
    return result

