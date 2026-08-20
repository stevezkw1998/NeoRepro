#!/usr/bin/env python3
"""Generate deterministic leave-one-patient-out transparent baselines."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
OUTPUT_FIELDS = [
    "record_id",
    "predictor",
    "predictor_version",
    "task",
    "score",
    "score_direction",
    "status",
    "split_unit",
    "held_out_group",
]


def peptide_features(peptides: list[str]) -> np.ndarray:
    features = []
    for peptide in peptides:
        counts = Counter(peptide)
        features.append(
            [len(peptide)] + [counts[amino_acid] / len(peptide) for amino_acid in AMINO_ACIDS]
        )
    return np.asarray(features, dtype=float)


def logistic_scores(
    train: list[dict[str, str]], test: list[dict[str, str]], feature_set: str
) -> np.ndarray:
    train_peptide = peptide_features([row["peptide"] for row in train])
    test_peptide = peptide_features([row["peptide"] for row in test])
    if feature_set in {"hla", "hla_peptide"}:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        train_hla = encoder.fit_transform(np.asarray([row["hla"] for row in train]).reshape(-1, 1))
        test_hla = encoder.transform(np.asarray([row["hla"] for row in test]).reshape(-1, 1))
    if feature_set == "hla":
        train_features = train_hla
        test_features = test_hla
    elif feature_set == "hla_peptide":
        train_features = np.column_stack((train_peptide, train_hla))
        test_features = np.column_stack((test_peptide, test_hla))
    elif feature_set == "peptide":
        train_features = train_peptide
        test_features = test_peptide
    else:
        raise ValueError(f"unknown feature set: {feature_set}")
    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_features)
    test_features = scaler.transform(test_features)
    model = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        random_state=20260820,
        solver="lbfgs",
    )
    model.fit(train_features, [int(row["immunogenicity"]) for row in train])
    return model.predict_proba(test_features)[:, 1]


def write_predictions(
    path: Path,
    rows: list[dict[str, str]],
    predictor: str,
    scores: dict[str, float],
    group_column: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "record_id": row["record_id"],
                    "predictor": predictor,
                    "predictor_version": "1.0",
                    "task": f"immunogenicity_{'lopo' if group_column == 'patient_id' else 'loso'}",
                    "score": f"{scores[row['record_id']]:.12g}",
                    "score_direction": "higher",
                    "status": "predicted",
                    "split_unit": group_column,
                    "held_out_group": row[group_column],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/benchmark.csv"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/raw_predictions/baselines")
    )
    parser.add_argument(
        "--fold-manifest", type=Path, default=Path("results/analysis/lopo_folds.csv")
    )
    parser.add_argument("--group-column", choices=("patient_id", "study_id"), default="patient_id")
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    groups = sorted({row[args.group_column] for row in rows})
    if len(groups) < 2:
        raise SystemExit(
            f"leave-one-group-out evaluation requires at least two {args.group_column}s"
        )
    abbreviation = "LOPO" if args.group_column == "patient_id" else "LOSO"
    scores: dict[str, dict[str, float]] = {
        f"HLA-only LR {abbreviation}": {},
        f"Peptide LR {abbreviation}": {},
        f"HLA+peptide LR {abbreviation}": {},
    }
    folds = []
    for group in groups:
        train = [row for row in rows if row[args.group_column] != group]
        test = [row for row in rows if row[args.group_column] == group]
        fold_scores = {
            f"HLA-only LR {abbreviation}": logistic_scores(train, test, feature_set="hla"),
            f"Peptide LR {abbreviation}": logistic_scores(train, test, feature_set="peptide"),
            f"HLA+peptide LR {abbreviation}": logistic_scores(
                train, test, feature_set="hla_peptide"
            ),
        }
        for predictor, values in fold_scores.items():
            scores[predictor].update(
                {row["record_id"]: float(value) for row, value in zip(test, values, strict=True)}
            )
        folds.append(
            {
                "split_unit": args.group_column,
                "held_out_group": group,
                "train_rows": len(train),
                "train_positives": sum(int(row["immunogenicity"]) for row in train),
                "test_rows": len(test),
                "test_positives": sum(int(row["immunogenicity"]) for row in test),
                "unseen_test_hlas": len(
                    {row["hla"] for row in test} - {row["hla"] for row in train}
                ),
            }
        )
    names = {
        f"HLA-only LR {abbreviation}": f"hla-only-{abbreviation.lower()}.csv",
        f"Peptide LR {abbreviation}": f"peptide-lr-{abbreviation.lower()}.csv",
        f"HLA+peptide LR {abbreviation}": f"hla-peptide-lr-{abbreviation.lower()}.csv",
    }
    for predictor, filename in names.items():
        write_predictions(
            args.output_dir / filename, rows, predictor, scores[predictor], args.group_column
        )
    args.fold_manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.fold_manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(folds[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(folds)
    print(
        f"wrote {len(names)} {abbreviation} baselines across {len(groups)} "
        f"held-out {args.group_column} groups"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
