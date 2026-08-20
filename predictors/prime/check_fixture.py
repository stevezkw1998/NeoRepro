#!/usr/bin/env python3
"""Verify ARM64-compiled PRIME/MixMHCpred against the distributed fixture."""

from __future__ import annotations

import argparse
import math
import shutil
import tempfile
from pathlib import Path

from adapter import parse_prime, run_prime, stage_sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("predictors/prime/source"))
    parser.add_argument(
        "--mix-dir", type=Path, default=Path("predictors/prime/vendor/mixmhcpred")
    )
    args = parser.parse_args()
    source_dir = args.source_dir.absolute()
    mix_dir = args.mix_dir.absolute()
    with tempfile.TemporaryDirectory(prefix="neorepro-prime-fixture-") as temporary:
        work = Path(temporary)
        prime_wrapper, mix_wrapper, prime_stage = stage_sources(source_dir, mix_dir, work)
        fixture_input = work / "fixture.txt"
        shutil.copyfile(source_dir / "test/test.txt", fixture_input)
        actual_path = work / "actual.tsv"
        run_prime(
            prime_wrapper,
            mix_wrapper,
            fixture_input,
            actual_path,
            ["A0101", "A2501", "B0801", "B1801"],
            prime_stage,
        )
        actual = parse_prime(actual_path)
        expected = parse_prime(source_dir / "test/out_compare.txt")
    if len(actual) != len(expected):
        raise RuntimeError(f"row count differs: {len(actual)} != {len(expected)}")
    maximum = 0.0
    for actual_row, expected_row in zip(actual, expected, strict=True):
        if actual_row["Peptide"] != expected_row["Peptide"]:
            raise RuntimeError("fixture peptide order differs")
        for column, expected_value in expected_row.items():
            if column in {"Peptide", "BestAllele"}:
                if actual_row[column] != expected_value:
                    raise RuntimeError(f"fixture categorical value differs in {column}")
                continue
            difference = abs(float(actual_row[column]) - float(expected_value))
            maximum = max(maximum, difference)
    if not math.isfinite(maximum) or maximum > 1e-6:
        raise RuntimeError(f"fixture maximum absolute difference is {maximum}")
    print(f"PRIME fixture reproduced: {len(actual)} rows; max absolute difference {maximum:g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
