from __future__ import annotations

import importlib.util
from pathlib import Path


def load_module():
    path = Path(__file__).parents[1] / "scripts/build_peptide_sensitivity.py"
    spec = importlib.util.spec_from_file_location("build_peptide_sensitivity", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mid_percentiles_preserve_ties() -> None:
    module = load_module()
    assert module.mid_percentiles([1.0, 2.0, 2.0, 4.0]) == [0.125, 0.5, 0.5, 0.875]
