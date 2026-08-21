"""Small, dependency-free metric primitives used by fixtures and the pilot."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from math import comb


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
    """Compute non-interpolated average precision with threshold-level tie handling."""
    _validate(labels, scores)
    positives = sum(labels)
    if not positives:
        raise ValueError("average precision requires a positive label")
    true_positives = 0
    predicted_positives = 0
    result = 0.0
    ordered = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and scores[ordered[end]] == scores[ordered[start]]:
            end += 1
        group_positives = sum(labels[index] for index in ordered[start:end])
        true_positives += group_positives
        predicted_positives += end - start
        result += (group_positives / positives) * (true_positives / predicted_positives)
        start = end
    return result


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


def tie_aware_ranking_metrics(
    labels: Sequence[int], scores: Sequence[float], ks: Iterable[int]
) -> dict[str, float]:
    """Compute expected patient-ranking metrics over every tied-score ordering."""
    _validate(labels, scores)
    positives = sum(labels)
    if not positives:
        raise ValueError("ranking metrics require a positive-bearing patient")
    ordered = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
    score_groups: list[tuple[int, int]] = []
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and scores[ordered[end]] == scores[ordered[start]]:
            end += 1
        score_groups.append((end - start, sum(labels[index] for index in ordered[start:end])))
        start = end

    offset = 0
    expected_mrr = 0.0
    for size, group_positives in score_groups:
        if group_positives:
            denominator = comb(size, group_positives)
            expected_mrr = sum(
                (comb(size - first, group_positives - 1) / denominator) / (offset + first)
                for first in range(1, size - group_positives + 2)
            )
            break
        offset += size

    result = {"mrr": expected_mrr}
    for k in ks:
        if k <= 0:
            raise ValueError("K must be positive")
        limit = min(k, len(ordered))
        remaining = limit
        offset = 0
        expected_hits = 0.0
        expected_dcg = 0.0
        zero_hit_probability = 1.0
        for size, group_positives in score_groups:
            if not remaining:
                break
            selected = min(remaining, size)
            expected_hits += selected * group_positives / size
            expected_dcg += (group_positives / size) * sum(
                1 / math.log2(rank + 1)
                for rank in range(offset + 1, offset + selected + 1)
            )
            if selected == size:
                if group_positives:
                    zero_hit_probability = 0.0
            elif zero_hit_probability and group_positives:
                zero_hit_probability *= comb(size - group_positives, selected) / comb(
                    size, selected
                )
            remaining -= selected
            offset += selected
        result[f"recall@{k}"] = expected_hits / positives
        result[f"precision@{k}"] = expected_hits / limit
        result[f"hitrate@{k}"] = 1 - zero_hit_probability
        ideal_hits = min(positives, limit)
        idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        result[f"ndcg@{k}"] = expected_dcg / idcg
    return result
