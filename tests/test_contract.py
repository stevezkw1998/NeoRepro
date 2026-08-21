from pathlib import Path

import pytest

from neorepro.contract import ContractError, evaluate, validate_artifact, validate_card

ROOT = Path(__file__).resolve().parents[1]


def test_cards_and_artifact():
    assert validate_card(ROOT / "contracts/dataset-card.example.json", "dataset")["valid"]
    assert validate_card(ROOT / "contracts/predictor-card.example.json", "predictor")["valid"]
    assert (
        validate_artifact(
            ROOT / "contracts/synthetic/predictions.csv", ROOT / "contracts/synthetic/benchmark.csv"
        )["missing"]
        == 1
    )


def test_evaluate_synthetic(tmp_path):
    out = tmp_path / "eval.json"
    result = evaluate(
        ROOT / "contracts/synthetic/benchmark.csv",
        [ROOT / "contracts/synthetic/predictions.csv"],
        out,
    )
    assert result["common_support"]["records"] == 3
    assert result["models"]["synthetic"]["auroc"] == 1.0


def test_lower_direction_and_overlap_gate(tmp_path):
    lower = """record_id,predictor,predictor_version,task,score,score_direction,status
s1,synthetic,1.0,immunogenicity,0.1,lower,predicted
s2,synthetic,1.0,immunogenicity,0.9,lower,predicted
s3,synthetic,1.0,immunogenicity,0.2,lower,predicted
s4,synthetic,1.0,immunogenicity,,lower,unsupported
"""
    path = tmp_path / "lower.csv"
    path.write_text(lower)
    audit = tmp_path / "overlap.csv"
    audit.write_text("record_id,exact_overlap\ns1,0\ns2,0\ns3,0\ns4,0\n")
    result = evaluate(
        ROOT / "contracts/synthetic/benchmark.csv", [path], tmp_path / "out.json", audit
    )
    assert result["models"]["synthetic"]["score_direction"] == "lower"
    assert result["models"]["synthetic"]["auroc"] == 1.0
    assert result["gates"]["leakage"]["status"] == "checked"


def test_artifact_rejects_duplicate_or_missing_support(tmp_path):
    rows = (ROOT / "contracts/synthetic/predictions.csv").read_text().splitlines()
    path = tmp_path / "bad.csv"
    path.write_text("\n".join(rows[:-1] + [rows[1]]) + "\n")
    with pytest.raises(ContractError, match="duplicate|support mismatch"):
        validate_artifact(path, ROOT / "contracts/synthetic/benchmark.csv")
