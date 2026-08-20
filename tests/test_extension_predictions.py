from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_zhao_prediction_contracts() -> None:
    benchmark = rows(ROOT / "data/processed/zhao_vaccine_benchmark.csv")
    benchmark_ids = [row["record_id"] for row in benchmark]
    outputs = sorted((ROOT / "results/raw_predictions/zhao").glob("*.csv"))
    assert len(outputs) == 5
    for output in outputs:
        prediction = rows(output)
        assert [row["record_id"] for row in prediction] == benchmark_ids
        assert all(row["status"] for row in prediction)
        assert all(
            row["score"] and math.isfinite(float(row["score"]))
            for row in prediction
            if row["status"] == "predicted"
        )


def test_deepimmuno_never_fuzzy_rescues_length() -> None:
    benchmark = {
        row["record_id"]: row for row in rows(ROOT / "data/processed/zhao_vaccine_benchmark.csv")
    }
    prediction = rows(ROOT / "results/raw_predictions/zhao/deepimmuno-cnn.csv")
    for row in prediction:
        if len(benchmark[row["record_id"]]["peptide"]) not in {9, 10}:
            assert row["status"] == "unsupported_length"
            assert row["score"] == ""


def test_extension_overlap_filter_is_common() -> None:
    full = rows(ROOT / "data/processed/zhao_vaccine_benchmark_full.csv")
    filtered = rows(ROOT / "data/processed/zhao_vaccine_benchmark.csv")
    audit = rows(ROOT / "research/training_overlap_audit_zhao.csv")
    excluded = {
        row["record_id"]
        for row in audit
        if int(row["union_known_exact_overlap"])
    }
    assert len(full) == 2317
    assert len(excluded) == 2
    assert {row["record_id"] for row in filtered} == {
        row["record_id"] for row in full
    } - excluded
