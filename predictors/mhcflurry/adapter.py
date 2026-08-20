#!/usr/bin/env python3
"""Run MHCflurry presentation prediction on canonical NeoRepro records."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

VERSION = "2.2.1"
FIELDS = [
    "record_id",
    "predictor",
    "predictor_version",
    "task",
    "score",
    "score_direction",
    "status",
    "affinity_nm",
    "affinity_percentile",
    "presentation_score",
    "presentation_percentile",
    "processing_score",
    "best_allele",
]


def required_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"record_id", "peptide", "hla"}
    missing = required - set(rows[0] if rows else [])
    if missing:
        raise ValueError(f"missing input columns: {sorted(missing)}")
    record_ids = [row["record_id"] for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("record_id must be unique")
    return rows


def scalar(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return "" if not math.isfinite(number) else f"{number:.12g}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/benchmark.csv"))
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("predictors/mhcflurry/vendor/2.2.0/models_class1_presentation/models"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/raw_predictions/mhcflurry-2.2.1.csv"),
    )
    args = parser.parse_args()

    rows = required_rows(args.input)
    from mhcflurry import Class1PresentationPredictor

    predictor = Class1PresentationPredictor.load(str(args.models_dir.resolve()))
    record_ids = [row["record_id"] for row in rows]
    predictions = predictor.predict(
        peptides=[row["peptide"] for row in rows],
        alleles={row["record_id"]: [row["hla"]] for row in rows},
        sample_names=record_ids,
        include_affinity_percentile=True,
        verbose=0,
        throw=False,
    )
    if len(predictions) != len(rows):
        raise RuntimeError(f"expected {len(rows)} output rows, received {len(predictions)}")

    output_rows = []
    for source, (_, prediction) in zip(rows, predictions.iterrows(), strict=True):
        if prediction["sample_name"] != source["record_id"]:
            raise RuntimeError("MHCflurry changed input row order")
        presentation_score = scalar(prediction.get("presentation_score"))
        output_rows.append(
            {
                "record_id": source["record_id"],
                "predictor": "MHCflurry",
                "predictor_version": VERSION,
                "task": "presentation",
                "score": presentation_score,
                "score_direction": "higher",
                "status": "predicted" if presentation_score else "unsupported_or_invalid",
                "affinity_nm": scalar(prediction.get("affinity")),
                "affinity_percentile": scalar(prediction.get("affinity_percentile")),
                "presentation_score": presentation_score,
                "presentation_percentile": scalar(prediction.get("presentation_percentile")),
                "processing_score": scalar(prediction.get("processing_score")),
                "best_allele": str(prediction.get("best_allele") or ""),
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    predicted = sum(row["status"] == "predicted" for row in output_rows)
    print(f"MHCflurry {VERSION}: {predicted}/{len(output_rows)} rows predicted -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
