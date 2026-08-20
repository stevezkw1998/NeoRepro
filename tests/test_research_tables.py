import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_predictor_landscape_has_unique_tools_and_explicit_decisions() -> None:
    with (ROOT / "research/predictor_landscape.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    names = [row["tool_name"].casefold() for row in rows]
    assert len(rows) >= 10
    assert len(names) == len(set(names))
    assert {row["candidate_for_benchmark"] for row in rows} <= {"yes", "no", "pending"}
    assert all(row["evidence_note"] for row in rows)


def test_related_work_has_stable_identifiers() -> None:
    with (ROOT / "research/related_work_matrix.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    keys = [row["study_key"] for row in rows]
    assert len(rows) >= 15
    assert len(keys) == len(set(keys))
    assert all(row["url"].startswith("https://") for row in rows)
