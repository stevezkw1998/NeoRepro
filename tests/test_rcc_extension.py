import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_rcc_benchmark_and_overlap_contract() -> None:
    rows = load_csv("data/processed/rcc_vaccine_benchmark.csv")
    assert len(rows) == 129
    assert len({row["patient_id"] for row in rows}) == 9
    assert sum(int(row["immunogenicity"]) for row in rows) == 75
    summary = json.loads((ROOT / "research/training_overlap_summary_rcc.json").read_text())
    assert summary["benchmark_union_known_exact_overlap"] == 0
    assert summary["overlap_dimensions"]["deephlapan_training_identity"].startswith("unknown_")


def test_rcc_predictions_are_complete_artifacts() -> None:
    paths = sorted((ROOT / "results/raw_predictions/rcc").glob("*.csv"))
    assert len(paths) == 4
    for path in paths:
        rows = load_csv(str(path.relative_to(ROOT)))
        assert len(rows) == 129
        assert len({row["record_id"] for row in rows}) == 129
        assert {row["status"] for row in rows} <= {
            "predicted",
            "unsupported_hla",
            "unsupported_length",
        }


def test_generated_manuscript_contains_rcc_table() -> None:
    manuscript = (ROOT / "paper/manuscript_resource.md").read_text(encoding="utf-8")
    assert "### Endpoint-distinct RCC vaccine cohort" in manuscript
    assert "**Table 4. RCC personalized-vaccine cohort.**" in manuscript
    assert "[@braun2025rcc]" in manuscript
