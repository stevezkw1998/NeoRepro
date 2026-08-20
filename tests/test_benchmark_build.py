import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data" / "processed" / "benchmark.csv"


def test_frozen_pilot_benchmark_contract() -> None:
    with BENCHMARK.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 520
    assert sum(int(row["immunogenicity"]) for row in rows) == 35
    assert len({row["patient_id"] for row in rows}) == 6
    assert {row["study_id"] for row in rows} == {"TESLA2020"}
    identities = {(row["patient_id"], row["peptide"], row["hla"]) for row in rows}
    assert len(identities) == len(rows)


def test_frozen_pilot_checksum_and_duplicate_report() -> None:
    digest = hashlib.sha256(BENCHMARK.read_bytes()).hexdigest()
    assert digest == "95c047fce5556faff64f97fdcb6760a89164680ea693fc5648bf96ef02ea7f49"
    report = json.loads((ROOT / "data" / "processing_report.json").read_text())
    assert report["source_rows"] == 522
    assert report["output_rows"] == 520
    assert len(report["removed_exact_duplicate_rows"]) == 2
