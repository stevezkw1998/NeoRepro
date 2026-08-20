#!/usr/bin/env python3
"""Deterministically audit NeoRepro manuscript citations and required artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED = (
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "RESEARCH_SPEC.md",
    "research/research_gap.md",
    "research/predictor_landscape.csv",
    "data/predictor_registry.csv",
    "data/processed/benchmark.csv",
    "data/audit_results.csv",
    "results/final_results.csv",
    "results/tables/fixed_predictor_summary.csv",
    "results/figures/fixed_predictor_performance.png",
    "paper/manuscript.md",
    "paper/references.bib",
    "paper/reviewer_comments.md",
    "paper/reviewer_response.md",
    "FINAL_REPORT.md",
    "research/extension_protocol.json",
    "research/training_overlap_summary_zhao.json",
    "data/processed/zhao_vaccine_benchmark.csv",
    "results/analysis/zhao/fixed/metrics.json",
    "reports/extension_summary.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manuscript = (root / args.manuscript).read_text(encoding="utf-8")
    bib = (root / "paper/references.bib").read_text(encoding="utf-8")
    cited = set(re.findall(r"\[@([A-Za-z0-9_:-]+)\]", manuscript))
    available = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
    unresolved = sorted(cited - available)
    uncited = sorted(available - cited)
    missing = [path for path in REQUIRED if not (root / path).is_file()]
    placeholders = sorted(set(re.findall(r"\{\{[^}]+\}\}", manuscript)))
    forbidden = [
        phrase
        for phrase in ("clinically effective", "proves clinical benefit", "is universally superior")
        if phrase.lower() in manuscript.lower()
    ]
    report = {
        "status": "pass" if not (unresolved or missing or placeholders or forbidden) else "fail",
        "citations_used": sorted(cited),
        "unresolved_citations": unresolved,
        "uncited_bibliography_entries": uncited,
        "missing_required_artifacts": missing,
        "unresolved_placeholders": placeholders,
        "forbidden_overclaims": forbidden,
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
