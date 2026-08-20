from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data/processed/zhao_vaccine_benchmark_full.csv"


def test_vaccine_benchmark_contract() -> None:
    with BENCHMARK.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2317
    assert sum(int(row["immunogenicity"]) for row in rows) == 313
    assert len({row["patient_id"] for row in rows}) == 352
    assert {row["study_id"] for row in rows} == {"ZHAO_DC_VACCINE_2026"}
    assert {len(row["peptide"]) for row in rows} <= {8, 9, 10, 11}
    assert all(row["patient_id"] and row["hla"].startswith("HLA-") for row in rows)
    assert len({row["record_id"] for row in rows}) == len(rows)


def test_vaccine_summary_matches_source() -> None:
    summary = json.loads((ROOT / "data/zhao_vaccine_summary.json").read_text())
    assert summary["source_rows"] == 2317
    assert summary["patients"] == 352
    assert summary["positives"] == 313
    assert summary["label_rule"] == "ELSPOT ratio >= 2.0"
