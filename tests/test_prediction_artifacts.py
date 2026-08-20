import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data/processed/benchmark.csv"
PREDICTIONS = {
    "MHCflurry": (
        ROOT / "results/raw_predictions/mhcflurry-2.2.1.csv",
        "bbb3dfa9e735a0452e766ac136d7c5fc65c7292129effcca4559959fca798fe6",
    ),
    "BigMHC": (
        ROOT / "results/raw_predictions/bigmhc-v1.0.csv",
        "6848cc5ea890629b82942f4444b93f0e3df2df2c0deca2f85ea07d044a0b5f18",
    ),
    "PRIME": (
        ROOT / "results/raw_predictions/prime-2.0.csv",
        "ea247e4234b707d4eff51c8dda89657999db7a6f393aaa276631dd320711a336",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize(("predictor", "artifact"), PREDICTIONS.items())
def test_prediction_artifact_contract(
    predictor: str, artifact: tuple[Path, str]
) -> None:
    path, expected_hash = artifact
    benchmark_ids = {row["record_id"] for row in rows(BENCHMARK)}
    prediction_rows = rows(path)
    assert len(prediction_rows) == 520
    assert {row["record_id"] for row in prediction_rows} == benchmark_ids
    assert {row["predictor"] for row in prediction_rows} == {predictor}
    assert {row["status"] for row in prediction_rows} == {"predicted"}
    assert {row["score_direction"] for row in prediction_rows} == {"higher"}
    assert all(row["score"] for row in prediction_rows)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash


def test_frozen_analysis_matches_metric_fixtures() -> None:
    result = json.loads((ROOT / "results/analysis/metrics.json").read_text())
    metrics = result["metrics"]
    assert metrics["BigMHC"]["pooled"]["auroc"] == pytest.approx(0.8744035346)
    assert metrics["MHCflurry"]["pooled"]["average_precision"] == pytest.approx(
        0.1938426254
    )
    assert metrics["PRIME"]["patient"]["recall@20"] == pytest.approx(0.5277777778)
    paired = {
        row["metric"]: row
        for row in result["paired_same_task"]
        if row["left"] == "BigMHC" and row["right"] == "PRIME"
    }
    assert paired["auroc"]["ci_low"] > 0
