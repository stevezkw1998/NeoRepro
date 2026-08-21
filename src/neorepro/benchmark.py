"""Portable, dependency-free benchmark entry point for external predictions."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import random
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from statistics import mean

from neorepro.metrics import auroc, average_precision, tie_aware_ranking_metrics

REQUIRED_COLUMNS = ("record_id", "patient_id", "study_id", "label", "score", "predictor")
OPTIONAL_COLUMNS = (
    "score_direction",
    "status",
    "training_overlap",
    "hla",
    "assay",
    "cancer_type",
)
VALID_DIRECTIONS = {"higher", "lower"}
VALID_STATUSES = {"predicted", "unsupported", "failed", "invalid"}
VALID_OVERLAP = {"exact", "none", "unknown"}
KS = (5, 10, 20)
PATIENT_METRICS = ("mrr",) + tuple(
    f"{metric}@{k}"
    for k in KS
    for metric in ("recall", "precision", "hitrate", "ndcg")
)


class BenchmarkError(ValueError):
    """Raised when a standard prediction submission is invalid."""


@dataclass(frozen=True)
class Record:
    record_id: str
    patient_id: str
    study_id: str
    label: int
    hla: str
    assay: str
    cancer_type: str


@dataclass(frozen=True)
class Submission:
    path: Path
    records: dict[str, Record]
    scores: dict[str, dict[str, float | None]]
    statuses: dict[str, dict[str, str]]
    overlaps: dict[str, dict[str, str]]
    directions: dict[str, str]
    rows: int
    columns: tuple[str, ...]
    sha256: str


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _interval(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"low": _percentile(values, 0.025), "high": _percentile(values, 0.975)}


def _parse_label(value: str, line: int) -> int:
    if value.strip() not in {"0", "1"}:
        raise BenchmarkError(f"line {line}: label must be 0 or 1")
    return int(value)


def read_submission(path: Path, default_direction: str = "higher") -> Submission:
    """Read and strictly validate one portable benchmark CSV."""
    if default_direction not in VALID_DIRECTIONS:
        raise BenchmarkError("default score direction must be higher or lower")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BenchmarkError(f"cannot read {path}: {error}") from error
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise BenchmarkError("prediction CSV must be UTF-8 encoded") from error

    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        raise BenchmarkError("prediction CSV has no header")
    columns = tuple(reader.fieldnames)
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise BenchmarkError("prediction CSV missing columns: " + ", ".join(missing))

    records: dict[str, Record] = {}
    optional_values: dict[str, dict[str, str]] = defaultdict(dict)
    scores: dict[str, dict[str, float | None]] = defaultdict(dict)
    statuses: dict[str, dict[str, str]] = defaultdict(dict)
    overlaps: dict[str, dict[str, str]] = defaultdict(dict)
    directions: dict[str, str] = {}
    rows = 0
    for line, row in enumerate(reader, start=2):
        rows += 1
        record_id = row["record_id"].strip()
        patient_id = row["patient_id"].strip()
        study_id = row["study_id"].strip()
        predictor = row["predictor"].strip()
        if not all((record_id, patient_id, study_id, predictor)):
            raise BenchmarkError(
                f"line {line}: record_id, patient_id, study_id and predictor are required"
            )
        label = _parse_label(row["label"], line)
        metadata = {
            field: row.get(field, "").strip() for field in ("hla", "assay", "cancer_type")
        }
        if record_id in records:
            existing = records[record_id]
            if (existing.patient_id, existing.study_id, existing.label) != (
                patient_id,
                study_id,
                label,
            ):
                raise BenchmarkError(f"line {line}: conflicting truth metadata for {record_id}")
            for field, value in metadata.items():
                previous = optional_values[record_id].get(field, "")
                if previous and value and previous != value:
                    raise BenchmarkError(
                        f"line {line}: conflicting {field} metadata for {record_id}"
                    )
                if value:
                    optional_values[record_id][field] = value
        else:
            optional_values[record_id] = metadata
            records[record_id] = Record(
                record_id=record_id,
                patient_id=patient_id,
                study_id=study_id,
                label=label,
                hla=metadata["hla"],
                assay=metadata["assay"],
                cancer_type=metadata["cancer_type"],
            )

        if record_id in scores[predictor]:
            raise BenchmarkError(f"line {line}: duplicate predictor/record_id pair")
        direction = row.get("score_direction", "").strip() or default_direction
        if direction not in VALID_DIRECTIONS:
            raise BenchmarkError(f"line {line}: score_direction must be higher or lower")
        if predictor in directions and directions[predictor] != direction:
            raise BenchmarkError(f"line {line}: inconsistent score direction for {predictor}")
        directions[predictor] = direction

        score_text = row["score"].strip()
        status = row.get("status", "").strip() or ("predicted" if score_text else "unsupported")
        if status not in VALID_STATUSES:
            raise BenchmarkError(f"line {line}: invalid status {status!r}")
        score: float | None = None
        if status == "predicted":
            try:
                score = float(score_text)
            except ValueError as error:
                raise BenchmarkError(f"line {line}: predicted score must be numeric") from error
            if not math.isfinite(score):
                raise BenchmarkError(f"line {line}: predicted score must be finite")
        elif score_text:
            raise BenchmarkError(f"line {line}: non-predicted rows must have a blank score")

        overlap = row.get("training_overlap", "").strip() or "unknown"
        if overlap not in VALID_OVERLAP:
            raise BenchmarkError(
                f"line {line}: training_overlap must be exact, none, or unknown"
            )
        scores[predictor][record_id] = score
        statuses[predictor][record_id] = status
        overlaps[predictor][record_id] = overlap

    if not rows:
        raise BenchmarkError("prediction CSV has no data rows")

    # Rebuild records after nonblank optional values have been reconciled across predictors.
    records = {
        record_id: Record(
            record_id=record.record_id,
            patient_id=record.patient_id,
            study_id=record.study_id,
            label=record.label,
            hla=optional_values[record_id].get("hla", ""),
            assay=optional_values[record_id].get("assay", ""),
            cancer_type=optional_values[record_id].get("cancer_type", ""),
        )
        for record_id, record in records.items()
    }
    return Submission(
        path=path,
        records=records,
        scores=dict(scores),
        statuses=dict(statuses),
        overlaps=dict(overlaps),
        directions=directions,
        rows=rows,
        columns=columns,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def _oriented(score: float, direction: str) -> float:
    return score if direction == "higher" else -score


def _classification_metrics(
    labels: list[int], raw_scores: list[float], direction: str, threshold: float
) -> dict[str, object]:
    oriented = [_oriented(score, direction) for score in raw_scores]
    predicted = [
        int(score >= threshold) if direction == "higher" else int(score <= threshold)
        for score in raw_scores
    ]
    tp = sum(label == 1 and call == 1 for label, call in zip(labels, predicted, strict=True))
    tn = sum(label == 0 and call == 0 for label, call in zip(labels, predicted, strict=True))
    fp = sum(label == 0 and call == 1 for label, call in zip(labels, predicted, strict=True))
    fn = sum(label == 1 and call == 0 for label, call in zip(labels, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    result: dict[str, object] = {
        "records": len(labels),
        "positives": sum(labels),
        "prevalence": sum(labels) / len(labels),
        "threshold": threshold,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mcc": (tp * tn - fp * fn) / denominator if denominator else None,
    }
    if len(set(labels)) == 2:
        result["auroc"] = auroc(labels, oriented)
    else:
        result["auroc"] = None
    result["average_precision"] = average_precision(labels, oriented) if sum(labels) else None
    if direction == "higher" and all(0 <= score <= 1 for score in raw_scores):
        result["brier_score"] = mean(
            (score - label) ** 2 for label, score in zip(labels, raw_scores, strict=True)
        )
        result["brier_status"] = "computed_from_probability_range_scores"
    else:
        result["brier_score"] = None
        result["brier_status"] = "not_computed_scores_are_not_higher_is_better_probabilities"
    return result


def _patient_values(
    record_ids: set[str], submission: Submission, predictor: str
) -> dict[str, dict[str, float]]:
    by_patient: dict[str, list[str]] = defaultdict(list)
    for record_id in sorted(record_ids):
        by_patient[submission.records[record_id].patient_id].append(record_id)
    values = {}
    for patient_id, patient_records in by_patient.items():
        labels = [submission.records[record_id].label for record_id in patient_records]
        if not sum(labels):
            continue
        scores = [submission.scores[predictor][record_id] for record_id in patient_records]
        if any(score is None for score in scores):
            raise AssertionError("patient metrics require numeric common-support scores")
        direction = submission.directions[predictor]
        values[patient_id] = tie_aware_ranking_metrics(
            labels,
            [_oriented(float(score), direction) for score in scores],
            KS,
        )
    return values


def _patient_summary(
    values: dict[str, dict[str, float]], bootstrap: int, seed: int
) -> dict[str, object]:
    if not values:
        return {"eligible_positive_bearing_patients": 0, "metrics": {}}
    patient_ids = sorted(values)
    samples: dict[str, list[float]] = {metric: [] for metric in PATIENT_METRICS}
    if bootstrap:
        rng = random.Random(seed)
        for _ in range(bootstrap):
            draw = rng.choices(patient_ids, k=len(patient_ids))
            for metric in PATIENT_METRICS:
                samples[metric].append(mean(values[patient_id][metric] for patient_id in draw))
    return {
        "eligible_positive_bearing_patients": len(patient_ids),
        "bootstrap_unit": "patient",
        "bootstrap_replicates": bootstrap,
        "seed": seed,
        "metrics": {
            metric: {
                "estimate": mean(patient[metric] for patient in values.values()),
                "ci95": _interval(samples[metric]),
            }
            for metric in PATIENT_METRICS
        },
    }


def _paired_differences(
    patient_values: dict[str, dict[str, dict[str, float]]], bootstrap: int, seed: int
) -> list[dict[str, object]]:
    results = []
    for pair_index, (left, right) in enumerate(combinations(sorted(patient_values), 2)):
        patient_ids = sorted(set(patient_values[left]) & set(patient_values[right]))
        if not patient_ids:
            continue
        rng = random.Random(seed + pair_index)
        samples: dict[str, list[float]] = {metric: [] for metric in PATIENT_METRICS}
        if bootstrap:
            for _ in range(bootstrap):
                draw = rng.choices(patient_ids, k=len(patient_ids))
                for metric in PATIENT_METRICS:
                    samples[metric].append(
                        mean(
                            patient_values[left][patient_id][metric]
                            - patient_values[right][patient_id][metric]
                            for patient_id in draw
                        )
                    )
        results.append(
            {
                "left": left,
                "right": right,
                "eligible_paired_patients": len(patient_ids),
                "difference": {
                    metric: {
                        "estimate": mean(
                            patient_values[left][patient_id][metric]
                            - patient_values[right][patient_id][metric]
                            for patient_id in patient_ids
                        ),
                        "ci95": _interval(samples[metric]),
                    }
                    for metric in PATIENT_METRICS
                },
            }
        )
    return results


def _stratified_views(
    record_ids: set[str], submission: Submission, predictor: str
) -> dict[str, list[dict[str, object]]]:
    result = {}
    direction = submission.directions[predictor]
    for field in ("study_id", "hla", "assay", "cancer_type"):
        grouped: dict[str, list[str]] = defaultdict(list)
        for record_id in record_ids:
            value = getattr(submission.records[record_id], field)
            if value:
                grouped[value].append(record_id)
        views = []
        for value, ids in sorted(grouped.items()):
            labels = [submission.records[record_id].label for record_id in ids]
            raw_scores = [submission.scores[predictor][record_id] for record_id in ids]
            scores = [_oriented(float(score), direction) for score in raw_scores]
            views.append(
                {
                    "group": value,
                    "records": len(ids),
                    "patients": len(
                        {submission.records[record_id].patient_id for record_id in ids}
                    ),
                    "positives": sum(labels),
                    "auroc": auroc(labels, scores) if len(set(labels)) == 2 else None,
                    "average_precision": average_precision(labels, scores) if sum(labels) else None,
                }
            )
        if views:
            result[field] = views
    return result


def evaluate_submission(
    path: Path,
    *,
    threshold: float = 0.5,
    bootstrap: int = 1000,
    seed: int = 20260820,
    rank_unit: str = "pMHC",
    default_direction: str = "higher",
) -> dict[str, object]:
    """Evaluate a standard joined prediction file on leakage-filtered common support."""
    if not math.isfinite(threshold):
        raise BenchmarkError("threshold must be finite")
    if bootstrap < 0:
        raise BenchmarkError("bootstrap must be non-negative")
    if rank_unit not in {"pMHC", "peptide"}:
        raise BenchmarkError("rank unit must be pMHC or peptide")
    if rank_unit == "peptide":
        raise BenchmarkError(
            "peptide ranking requires an explicit cross-HLA aggregation rule; use pMHC"
        )
    submission = read_submission(path, default_direction)
    predictors = sorted(submission.scores)
    universe = set(submission.records)
    support = {
        predictor: {
            record_id
            for record_id, score in submission.scores[predictor].items()
            if score is not None
        }
        for predictor in predictors
    }
    exact = {
        predictor: {
            record_id
            for record_id, overlap in submission.overlaps[predictor].items()
            if overlap == "exact"
        }
        for predictor in predictors
    }
    audited_support = {
        predictor: support[predictor] - exact[predictor] for predictor in predictors
    }
    raw_common = set.intersection(*(support[predictor] for predictor in predictors))
    common = set.intersection(*(audited_support[predictor] for predictor in predictors))
    if not common:
        raise BenchmarkError("no leakage-filtered common support remains for evaluation")

    models = {}
    patient_values = {}
    for predictor in predictors:
        labels = [submission.records[record_id].label for record_id in sorted(common)]
        scores = [float(submission.scores[predictor][record_id]) for record_id in sorted(common)]
        values = _patient_values(common, submission, predictor)
        patient_values[predictor] = values
        status_counts = {
            status: sum(value == status for value in submission.statuses[predictor].values())
            for status in sorted(VALID_STATUSES)
        }
        overlap_counts = {
            overlap: sum(value == overlap for value in submission.overlaps[predictor].values())
            for overlap in sorted(VALID_OVERLAP)
        }
        models[predictor] = {
            "score_direction": submission.directions[predictor],
            "coverage": len(support[predictor]) / len(universe),
            "submitted_records": len(submission.scores[predictor]),
            "omitted_records": len(universe - set(submission.scores[predictor])),
            "supported_records": len(support[predictor]),
            "status_counts": status_counts,
            "training_overlap": overlap_counts,
            "exact_overlap_excluded": len(exact[predictor]),
            "pooled_common_support": _classification_metrics(
                labels, scores, submission.directions[predictor], threshold
            ),
            "patient_common_support": _patient_summary(values, bootstrap, seed),
            "stratified_descriptive": _stratified_views(common, submission, predictor),
        }

    random_values = {}
    by_patient: dict[str, list[str]] = defaultdict(list)
    for record_id in common:
        by_patient[submission.records[record_id].patient_id].append(record_id)
    for patient_id, record_ids in by_patient.items():
        labels = [submission.records[record_id].label for record_id in record_ids]
        if sum(labels):
            random_values[patient_id] = tie_aware_ranking_metrics(
                labels, [0.0] * len(labels), KS
            )

    return {
        "schema_version": 1,
        "protocol": {
            "score_direction": "declared_per_predictor; default higher",
            "classification_threshold": threshold,
            "rank_unit": rank_unit,
            "top_k": list(KS),
            "tie_rule": "analytic expectation over tied-score permutations",
            "primary_comparison": "exact-overlap-filtered common support",
            "bootstrap": {
                "unit": "patient",
                "replicates": bootstrap,
                "seed": seed,
            },
            "interpretation": (
                "descriptive discrimination and prioritization; not clinical efficacy or "
                "held-out generalization"
            ),
        },
        "input": {
            "path": str(path),
            "sha256": submission.sha256,
            "rows": submission.rows,
            "records": len(universe),
            "predictors": predictors,
            "columns": list(submission.columns),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "support": {
            "raw_common_records": len(raw_common),
            "leakage_filtered_common_records": len(common),
            "leakage_filtered_common_coverage": len(common) / len(universe),
        },
        "models": models,
        "support_matched_random_ranking": _patient_summary(random_values, bootstrap, seed),
        "paired_patient_differences": _paired_differences(patient_values, bootstrap, seed),
        "limitations": [
            "Unknown training overlap remains unknown and is not evidence of independence.",
            "Stratified results are descriptive; this command does not fit held-out folds.",
            "Brier score is computed only for higher-is-better scores entirely in [0, 1].",
            "Clinical efficacy cannot be inferred from predictor benchmark performance.",
        ],
    }


def markdown_report(result: dict[str, object]) -> str:
    """Render a concise, self-contained human-readable benchmark report."""
    support = result["support"]
    protocol = result["protocol"]
    lines = [
        "# NeoRepro standard benchmark report",
        "",
        f"Input SHA-256: `{result['input']['sha256']}`",
        "",
        (
            f"Primary comparison uses **{support['leakage_filtered_common_records']}** "
            f"records ({support['leakage_filtered_common_coverage']:.1%}) on "
            "exact-overlap-filtered common support."
        ),
        "",
        "| Predictor | Coverage | AUROC | AUPRC | Recall@20 | NDCG@5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for predictor, model in result["models"].items():
        pooled = model["pooled_common_support"]
        patient = model["patient_common_support"]["metrics"]

        def value(metric: object) -> str:
            return "NA" if metric is None else f"{float(metric):.3f}"

        lines.append(
            f"| {predictor} | {model['coverage']:.1%} | {value(pooled['auroc'])} | "
            f"{value(pooled['average_precision'])} | "
            f"{value(patient.get('recall@20', {}).get('estimate'))} | "
            f"{value(patient.get('ndcg@5', {}).get('estimate'))} |"
        )
    lines += [
        "",
        "## Evaluation contract",
        "",
        f"- Classification threshold: `{protocol['classification_threshold']}`.",
        f"- Ranking unit: `{protocol['rank_unit']}`; Top-K: `{protocol['top_k']}`.",
        f"- Tie handling: {protocol['tie_rule']}.",
        (
            f"- Patient bootstrap: {protocol['bootstrap']['replicates']} replicates, "
            f"seed `{protocol['bootstrap']['seed']}`."
        ),
        "- Missing or failed predictions are reported and never imputed.",
        "- Exact declared training overlaps are excluded; unknown overlap remains unknown.",
        "",
        "## Interpretation limits",
        "",
    ]
    lines.extend(f"- {limitation}" for limitation in result["limitations"])
    return "\n".join(lines) + "\n"


def run_benchmark(
    path: Path,
    output_dir: Path,
    *,
    threshold: float = 0.5,
    bootstrap: int = 1000,
    seed: int = 20260820,
    rank_unit: str = "pMHC",
    default_direction: str = "higher",
) -> tuple[dict[str, object], Path, Path]:
    """Evaluate one submission and atomically publish JSON and Markdown outputs."""
    result = evaluate_submission(
        path,
        threshold=threshold,
        bootstrap=bootstrap,
        seed=seed,
        rank_unit=rank_unit,
        default_direction=default_direction,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation.json"
    report_path = output_dir / "report.md"
    json_temp = output_dir / ".evaluation.json.tmp"
    report_temp = output_dir / ".report.md.tmp"
    json_temp.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_temp.write_text(markdown_report(result), encoding="utf-8")
    json_temp.replace(json_path)
    report_temp.replace(report_path)
    return result, json_path, report_path
