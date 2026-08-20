from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


def load_runner():
    path = Path(__file__).parents[1] / "scripts/run_fixed_predictors.py"
    spec = importlib.util.spec_from_file_location("run_fixed_predictors", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_prediction(path: Path, record_ids: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "record_id",
                "predictor",
                "predictor_version",
                "status",
                "score",
            ),
        )
        writer.writeheader()
        for record_id in record_ids:
            writer.writerow(
                {
                    "record_id": record_id,
                    "predictor": "PRIME",
                    "predictor_version": "2.0",
                    "status": "predicted",
                    "score": "0.5",
                }
            )


def test_reuse_requires_exact_record_order_and_revision(tmp_path: Path) -> None:
    runner = load_runner()
    path = tmp_path / "prime-2.0.csv"
    write_prediction(path, ["r1", "r2"])
    receipt = runner.validated_existing("prime", ["prime", "--output", str(path)], ["r1", "r2"], tmp_path)
    assert receipt is not None
    assert receipt["execution"] == "reused_validated"
    assert receipt["rows"] == 2
    assert runner.validated_existing(
        "prime", ["prime", "--output", str(path)], ["r2", "r1"], tmp_path
    ) is None
