import math

import pytest

from neorepro.metrics import auroc, average_precision, ranking_metrics


def test_perfect_pooled_ranking() -> None:
    labels = [1, 0, 1, 0]
    scores = [0.9, 0.1, 0.8, 0.2]
    assert auroc(labels, scores) == 1.0
    assert average_precision(labels, scores) == 1.0


def test_auroc_ties_use_average_ranks() -> None:
    assert auroc([1, 0], [0.5, 0.5]) == 0.5


def test_average_precision_handles_ties_at_threshold_level() -> None:
    assert average_precision([1, 0], [0.5, 0.5]) == 0.5
    assert average_precision([1, 0, 1, 0], [1.0, 1.0, 0.0, 0.0]) == 0.5


def test_patient_top_k_uses_available_candidates() -> None:
    result = ranking_metrics([0, 1, 0], [1, 2, 5])
    assert result["mrr"] == 0.5
    assert result["recall@1"] == 0.0
    assert result["recall@2"] == 1.0
    assert result["precision@5"] == pytest.approx(1 / 3)
    assert math.isfinite(result["ndcg@5"])


def test_ranking_requires_positive_patient() -> None:
    with pytest.raises(ValueError, match="positive-bearing"):
        ranking_metrics([0, 0], [5])
