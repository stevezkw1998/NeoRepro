import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "data/processed/improve_benchmark_full.csv"
FILTERED = ROOT / "data/processed/improve_benchmark.csv"
AUDIT = ROOT / "research/training_overlap_audit_improve.csv"
PREDICTIONS = {
    "MHCflurry": (
        ROOT / "results/raw_predictions/improve/mhcflurry-2.2.1.csv",
        "presentation",
        "fad50cb83c207a2da1b9b3041f4161ebd5b416c5fff4b037c3b64d50bd2589d1",
    ),
    "BigMHC": (
        ROOT / "results/raw_predictions/improve/bigmhc-v1.0.csv",
        "immunogenicity",
        "8aca17b0d98e4bbace179ac5bfa2127ac8fd03ec2a963cae97f49201f850113c",
    ),
    "PRIME": (
        ROOT / "results/raw_predictions/improve/prime-2.0.csv",
        "immunogenicity",
        "8f6b8130eeaa28a3acc05be198b8f70a994c4696142f3d191d2c1980ef98362e",
    ),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_improve_full_benchmark_contract() -> None:
    data = rows(FULL)
    assert len(data) == 17_520
    assert sum(int(row["immunogenicity"]) for row in data) == 467
    assert len({row["patient_id"] for row in data}) == 70
    assert len({row["study_id"] for row in data}) == 3
    assert len({row["record_id"] for row in data}) == len(data)
    assert {int(row["peptide_length"]) for row in data} == {8, 9, 10, 11}
    assert all(len(row["peptide"]) == int(row["peptide_length"]) for row in data)
    assert all(re.fullmatch(r"HLA-[ABC]\*\d{2}:\d{2}", row["hla"]) for row in data)


def test_improve_common_filter_removes_all_exact_prime2_overlap() -> None:
    filtered = rows(FILTERED)
    audit = {row["record_id"]: row for row in rows(AUDIT)}
    assert len(filtered) == 17_475
    assert sum(int(row["immunogenicity"]) for row in filtered) == 465
    assert len({row["patient_id"] for row in filtered}) == 70
    assert len({row["study_id"] for row in filtered}) == 3
    assert all(
        audit[row["record_id"]]["exact_peptide_hla_in_prime2_train"] == "0"
        for row in filtered
    )
    excluded = set(audit) - {row["record_id"] for row in filtered}
    assert len(excluded) == 45


def test_improve_fixed_prediction_artifacts_are_complete_and_frozen() -> None:
    benchmark_ids = {row["record_id"] for row in rows(FILTERED)}
    for predictor, (path, task, expected_hash) in PREDICTIONS.items():
        prediction_rows = rows(path)
        assert len(prediction_rows) == 17_475
        assert {row["record_id"] for row in prediction_rows} == benchmark_ids
        assert {row["predictor"] for row in prediction_rows} == {predictor}
        assert {row["task"] for row in prediction_rows} == {task}
        assert {row["status"] for row in prediction_rows} == {"predicted"}
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
