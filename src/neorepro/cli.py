"""Command-line entry point for NeoRepro."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def project_root() -> Path:
    return Path.cwd()


def list_predictors(root: Path) -> int:
    registry = root / "research/predictor_landscape.csv"
    if not registry.exists():
        raise SystemExit(f"missing {registry}")
    with registry.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        print(f"{row['tool_name']}\t{row['candidate_for_benchmark']}\t{row['installation_status']}")
    return 0


def status(root: Path) -> int:
    checks = {
        "research_spec": root / "RESEARCH_SPEC.md",
        "predictor_landscape": root / "research/predictor_landscape.csv",
        "related_work": root / "research/related_work_matrix.csv",
        "predictor_registry": root / "data/predictor_registry.csv",
        "benchmark": root / "data/processed/benchmark.csv",
        "final_results": root / "results/final_results.csv",
        "manuscript": root / "paper/manuscript.tex",
    }
    for name, path in checks.items():
        print(f"{name}\t{'present' if path.exists() else 'missing'}\t{path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neorepro")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list-predictors")
    subparsers.add_parser("status")
    args = parser.parse_args(argv)
    root = project_root()
    if args.command == "list-predictors":
        return list_predictors(root)
    if args.command == "status":
        return status(root)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

