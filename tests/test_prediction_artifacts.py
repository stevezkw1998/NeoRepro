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
BASELINES = {
    "HLA-only LOPO": (
        ROOT / "results/raw_predictions/baselines/hla-only-lopo.csv",
        "c59f381d1b416e3697ed39f425c278d4b1a1146ac62f48fe61595b7017bfb5d5",
    ),
    "HLA+peptide LR LOPO": (
        ROOT / "results/raw_predictions/baselines/hla-peptide-lr-lopo.csv",
        "b04991c454c66a03de1d25f36d491fdff17720cde2eb8e47a03e1d07de08b2af",
    ),
    "Peptide LR LOPO": (
        ROOT / "results/raw_predictions/baselines/peptide-lr-lopo.csv",
        "f10d1c8b03338e7f1601000a66be38924e1bb9271afaf6ea7861b83bcc4e86c7",
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
    assert result["common_support"] == [
        {
            "left": "BigMHC",
            "right": "PRIME",
            "task": "immunogenicity",
            "n_common": 520,
            "positives_common": 35,
            "patients_common": 6,
        }
    ]
    assert set(metrics["BigMHC"]["study"]) == {"TESLA2020"}
    assert len(metrics["BigMHC"]["patient_values"]) == 6
    assert paired["auroc"]["n_common"] == 520
    assert paired["auroc"]["ci_low"] > 0


@pytest.mark.parametrize(("predictor", "artifact"), BASELINES.items())
def test_lopo_baseline_contract(predictor: str, artifact: tuple[Path, str]) -> None:
    path, expected_hash = artifact
    prediction_rows = rows(path)
    assert len(prediction_rows) == 520
    assert {row["predictor"] for row in prediction_rows} == {predictor}
    assert {row["task"] for row in prediction_rows} == {"immunogenicity_lopo"}
    assert {row["split_unit"] for row in prediction_rows} == {"patient_id"}
    assert len({row["held_out_group"] for row in prediction_rows}) == 6
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash


def test_training_overlap_audit_blocks_generalization_claims() -> None:
    summary = json.loads((ROOT / "research/training_overlap_summary.json").read_text())
    assert summary["benchmark_record_classifications"] == {"exact_label_concordant": 520}
    assert summary["benchmark_records_exact_bigmhc_im_trainval_overlap"] == 520
