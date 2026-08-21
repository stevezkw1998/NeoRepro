"""Command-line entry point for NeoRepro."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from neorepro.audit import AuditError, audit_predictions
from neorepro.contract import (
    ContractError,
    evaluate,
    markdown_report,
    validate_artifact,
    validate_card,
)


def project_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "RESEARCH_SPEC.md").exists():
        return cwd
    # Keep the legacy audit usable when invoked from another working directory.
    return Path(__file__).resolve().parents[2]


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
    audit_parser = subparsers.add_parser(
        "audit",
        help="audit external prediction scores against frozen benchmark evidence",
        description=(
            "Audit a CSV containing exactly patient_id, peptide, hla, score, model. "
            "Scores must be numeric or blank for unsupported rows; higher is better."
        ),
    )
    audit_parser.add_argument("predictions", type=Path, help="five-column prediction CSV")

    def add_path_command(name, help_text):
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("path", type=Path)
        return p

    dataset_parser = subparsers.add_parser("dataset", help="validate a Dataset Card JSON")
    dataset_parser.add_argument("action", choices=["validate"])
    dataset_parser.add_argument("path", type=Path)
    predictor_parser = subparsers.add_parser("predictor", help="validate a Predictor Card JSON")
    predictor_parser.add_argument("action", choices=["validate"])
    predictor_parser.add_argument("path", type=Path)
    artifact_parser = add_path_command("artifact", "validate a prediction artifact CSV")
    artifact_parser.add_argument("--benchmark", type=Path)
    overlap_parser = add_path_command(
        "overlap-audit", "run the frozen legacy overlap/common-support audit"
    )
    overlap_parser.add_argument("--root", type=Path, default=None)
    evaluate_parser = subparsers.add_parser("evaluate", help="evaluate artifacts on common support")
    evaluate_parser.add_argument("benchmark", type=Path)
    evaluate_parser.add_argument("artifacts", nargs="+", type=Path)
    evaluate_parser.add_argument("--overlap-audit", type=Path)
    evaluate_parser.add_argument(
        "--output", type=Path, default=Path("results/contract_evaluation.json")
    )
    evaluate_parser.add_argument(
        "--report", type=Path, default=Path("reports/contract_evaluation.md")
    )
    report_parser = subparsers.add_parser("report", help="render an evaluation JSON as Markdown")
    report_parser.add_argument("evaluation", type=Path)
    report_parser.add_argument(
        "--output", type=Path, default=Path("reports/contract_evaluation.md")
    )
    args = parser.parse_args(argv)
    root = project_root()
    if args.command == "list-predictors":
        return list_predictors(root)
    if args.command == "status":
        return status(root)
    if args.command == "audit":
        try:
            report = audit_predictions(args.predictions, root)
        except AuditError as error:
            parser.error(str(error))
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    try:
        if args.command == "dataset":
            print(json.dumps(validate_card(args.path, "dataset"), indent=2))
            return 0
        if args.command == "predictor":
            print(json.dumps(validate_card(args.path, "predictor"), indent=2))
            return 0
        if args.command == "artifact":
            print(json.dumps(validate_artifact(args.path, args.benchmark), indent=2))
            return 0
        if args.command == "overlap-audit":
            report = audit_predictions(args.path, args.root or root)
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        if args.command == "evaluate":
            result = evaluate(args.benchmark, args.artifacts, args.output, args.overlap_audit)
            markdown_report(result, args.report)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command == "report":
            markdown_report(json.loads(args.evaluation.read_text()), args.output)
            return 0
    except (ContractError, OSError, KeyError, ValueError) as error:
        parser.error(str(error))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
