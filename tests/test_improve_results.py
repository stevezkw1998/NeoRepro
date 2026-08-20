import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_fixed_improve_results_are_frozen() -> None:
    result = load_json("results/analysis/improve/fixed/metrics.json")
    expected = {
        "MHCflurry": ("presentation", 0.5367554822274058, 0.0316977826002111, 0.20210686751655044),
        "BigMHC": ("immunogenicity", 0.5458288293413741, 0.03186133541911459, 0.1458033270024836),
        "PRIME": ("immunogenicity", 0.5969085863470571, 0.039638725720073424, 0.2600474607783511),
    }
    for predictor, (task, auroc, average_precision, recall20) in expected.items():
        metrics = result["metrics"][predictor]
        assert metrics["metadata"]["task"] == task
        assert metrics["pooled"]["n"] == 17_475
        assert metrics["pooled"]["positives"] == 465
        assert metrics["pooled"]["auroc"] == pytest.approx(auroc)
        assert metrics["pooled"]["average_precision"] == pytest.approx(average_precision)
        assert metrics["patient"]["recall@20"] == pytest.approx(recall20)
        assert metrics["patient"]["positive_bearing_patients"] == 60


def test_results_manifest_hashes_every_declared_artifact() -> None:
    manifest = load_json("results/manifest.json")
    assert manifest["benchmark"] == {
        "exact_prime2_training_overlaps_excluded": 45,
        "patients": 70,
        "positives": 465,
        "records": 17_475,
        "studies": 3,
    }
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.stat().st_size == artifact["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_post_review_sensitivities_preserve_direction() -> None:
    exact = load_json("results/analysis/improve/exact_peptide_free/metrics.json")["metrics"]
    assert exact["BigMHC"]["pooled"]["n"] == 17_440
    assert exact["BigMHC"]["pooled"]["auroc"] == pytest.approx(0.5451536296678475)
    assert exact["PRIME"]["pooled"]["auroc"] == pytest.approx(0.5962768939517047)

    normalized = load_json(
        "results/analysis/improve/peptide_sensitivity_hla_rank/metrics.json"
    )["metrics"]
    recall20 = {
        predictor: normalized[predictor]["patient"]["recall@20"]
        for predictor in ("BigMHC", "MHCflurry", "PRIME")
    }
    assert recall20["BigMHC"] == pytest.approx(0.20158400709237423)
    assert recall20["MHCflurry"] == pytest.approx(0.21526135225678836)
    assert recall20["PRIME"] == pytest.approx(0.2401696615870044)
    assert recall20["BigMHC"] < recall20["MHCflurry"] < recall20["PRIME"]


def test_final_table_and_generated_manuscript_are_complete() -> None:
    with (ROOT / "results/final_results.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 9
    assert {row["analysis"] for row in rows} == {"fixed", "lopo", "loso"}
    manuscript = (ROOT / "paper/manuscript.md").read_text(encoding="utf-8")
    assert "{{AUTO_" not in manuscript
    assert "does not establish clinical utility" in manuscript
    assert "17,475" in manuscript
