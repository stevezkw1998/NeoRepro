import csv
import json
from pathlib import Path

import pytest

from neorepro.audit import AuditError, audit_predictions
from neorepro.cli import main

ROOT = Path(__file__).resolve().parents[1]
TESLA = ROOT / "data/processed/benchmark.csv"
ZHAO = ROOT / "data/processed/zhao_vaccine_benchmark_full.csv"
FIELDS = ["patient_id", "peptide", "hla", "score", "model"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_predictions(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prediction(source: dict[str, str], score: str, model: str) -> dict[str, str]:
    return {
        "patient_id": source["patient_id"],
        "peptide": source["peptide"],
        "hla": source["hla"],
        "score": score,
        "model": model,
    }


def test_audit_reports_leakage_support_and_patient_ci(tmp_path: Path) -> None:
    source = read_rows(TESLA)[:3]
    path = tmp_path / "predictions.csv"
    write_predictions(
        path,
        [
            prediction(source[0], "0.1", "External A"),
            prediction(source[1], "0.2", "External A"),
            prediction(source[2], "0.9", "External A"),
            prediction(source[0], "0.1", "External B"),
            prediction(source[1], "", "External B"),
            prediction(source[2], "0.8", "External B"),
        ],
    )

    report = audit_predictions(path, ROOT)

    assert report["benchmark"]["datasets"] == ["TESLA"]
    assert report["benchmark"]["expected_unique_patient_peptide_hla_records"] == 520
    assert report["leakage"]["External A"]["risk"] == "unknown_training_reference"
    assert report["support"]["by_model"]["External A"]["supported_records"] == 3
    assert report["support"]["by_model"]["External B"]["blank_score_records"] == 1
    assert report["support"]["raw_common_support"]["records"] == 2
    metric = report["patient_metrics"]["models"]["External A"]["metrics"]["ndcg@5"]
    assert metric["estimate"] == pytest.approx(1.0)
    assert metric["ci95"] == {"low": pytest.approx(1.0), "high": pytest.approx(1.0)}


def test_known_exact_overlap_is_excluded_from_metrics(tmp_path: Path) -> None:
    source = read_rows(TESLA)[:3]
    path = tmp_path / "prime.csv"
    write_predictions(
        path,
        [prediction(row, str(index), "PRIME-2.0") for index, row in enumerate(source)],
    )

    report = audit_predictions(path, ROOT)

    leakage = report["leakage"]["PRIME-2.0"]
    assert leakage["risk"] == "high_exact_overlap"
    assert leakage["exact_overlap_records"] == 3
    assert leakage["excluded_from_metrics_as_exact_overlap"] == 3
    assert report["support"]["leakage_filtered_common_support"]["records"] == 0
    assert report["patient_metrics"]["models"]["PRIME-2.0"]["metrics"] == {}


def test_five_column_key_collapses_concordant_source_duplicates(tmp_path: Path) -> None:
    source = read_rows(ZHAO)[0]
    path = tmp_path / "zhao.csv"
    write_predictions(path, [prediction(source, "0.5", "External")])

    report = audit_predictions(path, ROOT)

    assert report["benchmark"]["expected_unique_patient_peptide_hla_records"] == 2315
    assert report["benchmark"]["collapsed_duplicate_source_rows"] == 2


def test_audit_rejects_non_contract_header(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("patient_id,peptide,hla,score,model,label\n", encoding="utf-8")

    with pytest.raises(AuditError, match="header must contain exactly"):
        audit_predictions(path, ROOT)


def test_cli_prints_json_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = read_rows(TESLA)[0]
    path = tmp_path / "predictions.csv"
    write_predictions(path, [prediction(source, "0.5", "External")])

    assert main(["audit", str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["input"]["columns"] == FIELDS
    assert output["input"]["score_direction"] == "higher_is_better"
