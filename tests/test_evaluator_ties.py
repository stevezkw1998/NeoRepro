import importlib.util
import json
import math
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_benchmark", ROOT / "scripts/evaluate_benchmark.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_patient_top_k_uses_analytic_expectation_for_ties() -> None:
    rows = [
        {
            "record_id": str(index),
            "patient_id": "P1",
            "label": int(index == 0),
            "score": 0.5,
        }
        for index in range(10)
    ]
    values = MODULE.patient_values(rows)["P1"]
    assert values["recall@5"] == pytest.approx(0.5)
    assert values["precision@5"] == pytest.approx(0.1)
    assert values["hitrate@5"] == pytest.approx(0.5)
    assert values["mrr"] == pytest.approx(sum(1 / rank for rank in range(1, 11)) / 10)
    expected_dcg = 0.1 * sum(1 / math.log2(rank + 1) for rank in range(1, 6))
    assert values["ndcg@5"] == pytest.approx(expected_dcg)


def test_bootstrap_checkpoint_helpers_are_atomic_and_input_bound(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("a,b\n1,2\n")
    first = MODULE.input_fingerprint([source], 2000, 7)
    assert first == MODULE.input_fingerprint([source], 2000, 7)
    assert first != MODULE.input_fingerprint([source], 2000, 8)
    source.write_text("a,b\n1,3\n")
    assert first != MODULE.input_fingerprint([source], 2000, 7)

    checkpoint = tmp_path / ".bootstrap_checkpoint.json"
    state = {"completed": 50, "rng_state": repr(random.Random(7).getstate())}
    MODULE.atomic_json(checkpoint, state)
    assert json.loads(checkpoint.read_text()) == state
    assert not checkpoint.with_suffix(".json.tmp").exists()
