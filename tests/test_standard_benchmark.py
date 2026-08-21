import json
from pathlib import Path

import pytest

from neorepro.benchmark import BenchmarkError, evaluate_submission, run_benchmark
from neorepro.cli import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "contracts/synthetic/standard_predictions.csv"


def test_standard_benchmark_reports_full_contract(tmp_path: Path) -> None:
    result, json_path, report_path = run_benchmark(
        EXAMPLE, tmp_path / "result", bootstrap=50, seed=7
    )

    assert result["support"]["raw_common_records"] == 3
    assert result["support"]["leakage_filtered_common_records"] == 3
    assert result["models"]["Example-A"]["pooled_common_support"]["auroc"] == 1.0
    assert result["models"]["Example-A"]["patient_common_support"]["metrics"][
        "recall@20"
    ]["estimate"] == 1.0
    assert result["models"]["Example-B"]["status_counts"]["unsupported"] == 1
    assert result["support_matched_random_ranking"]["metrics"]["ndcg@5"]
    assert len(result["paired_patient_differences"]) == 1
    assert json.loads(json_path.read_text())["schema_version"] == 1
    assert "NeoRepro standard benchmark report" in report_path.read_text()


def test_exact_overlap_is_removed_from_common_support(tmp_path: Path) -> None:
    text = EXAMPLE.read_text().replace(
        "s1,P1,SYNTHETIC,1,0.9,Example-A,higher,predicted,none",
        "s1,P1,SYNTHETIC,1,0.9,Example-A,higher,predicted,exact",
    )
    path = tmp_path / "overlap.csv"
    path.write_text(text)

    result = evaluate_submission(path, bootstrap=0)

    assert result["models"]["Example-A"]["exact_overlap_excluded"] == 1
    assert result["support"]["leakage_filtered_common_records"] == 2


def test_standard_benchmark_rejects_conflicting_truth(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "record_id,patient_id,study_id,label,score,predictor\n"
        "r1,p1,s1,1,0.9,A\n"
        "r1,p1,s1,0,0.8,B\n"
    )

    with pytest.raises(BenchmarkError, match="conflicting truth"):
        evaluate_submission(path)


def test_standard_benchmark_cli_writes_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_dir = tmp_path / "cli"
    assert main(
        [
            "benchmark",
            str(EXAMPLE),
            "--output-dir",
            str(output_dir),
            "--bootstrap",
            "10",
        ]
    ) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "ok"
    assert (output_dir / "evaluation.json").exists()
    assert (output_dir / "report.md").exists()
