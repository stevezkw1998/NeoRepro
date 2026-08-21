"""Audit externally generated predictor scores against frozen NeoRepro benchmarks."""

from __future__ import annotations

import csv
import math
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from neorepro.metrics import tie_aware_ranking_metrics

INPUT_COLUMNS = ("patient_id", "peptide", "hla", "score", "model")
KS = (5, 20)
CORE_METRICS = ("recall@5", "recall@20", "ndcg@5", "mrr")
BOOTSTRAP_REPLICATES = 1000
BOOTSTRAP_SEED = 20260820

Key = tuple[str, str, str]


class AuditError(ValueError):
    """Raised when an audit cannot be performed without guessing."""


@dataclass(frozen=True)
class BenchmarkSpec:
    name: str
    benchmark_path: str
    overlap_path: str


@dataclass(frozen=True)
class BenchmarkRecord:
    dataset: str
    patient_id: str
    peptide: str
    hla: str
    label: int
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class Catalog:
    records: dict[Key, BenchmarkRecord]
    dataset_keys: dict[str, frozenset[Key]]
    overlap_rows: dict[str, dict[str, dict[str, str]]]
    collapsed_duplicate_rows: dict[str, int]


SPECS = (
    BenchmarkSpec(
        "TESLA",
        "data/processed/benchmark.csv",
        "research/training_overlap_audit.csv",
    ),
    BenchmarkSpec(
        "IMPROVE",
        "data/processed/improve_benchmark_full.csv",
        "research/training_overlap_audit_improve.csv",
    ),
    BenchmarkSpec(
        "Zhao2026",
        "data/processed/zhao_vaccine_benchmark_full.csv",
        "research/training_overlap_audit_zhao.csv",
    ),
)

MODEL_ALIASES = {
    "prime": "prime2",
    "prime2": "prime2",
    "prime20": "prime2",
    "bigmhc": "bigmhc",
    "bigmhcv10": "bigmhc",
    "deepimmuno": "deepimmuno",
    "deepimmunocnn": "deepimmuno",
    "deephlapan": "deephlapan",
    "deephlapan111": "deephlapan",
}

OVERLAP_FIELDS: dict[str, dict[str, dict[str, str | None]]] = {
    "TESLA": {
        "prime2": {
            "exact": "exact_peptide_hla_in_prime2_train",
            "peptide_only": "peptide_in_prime2_train",
            "near": None,
        },
        "bigmhc": {
            "exact": "exact_bigmhc_im_trainval_overlap",
            "peptide_only": None,
            "near": None,
        },
    },
    "IMPROVE": {
        "prime2": {
            "exact": "exact_peptide_hla_in_prime2_train",
            "peptide_only": "peptide_in_prime2_train",
            "near": "near_hamming1_same_hla_prime2_train",
        },
        "bigmhc": {
            "exact": "exact_bigmhc_im_trainval_overlap",
            "peptide_only": None,
            "near": None,
        },
    },
    "Zhao2026": {
        "prime2": {
            "exact": "exact_prime2_peptide_hla",
            "peptide_only": "peptide_only_prime2_different_hla",
            "near": "near_hamming1_prime2_same_hla",
        },
        "bigmhc": {
            "exact": "exact_bigmhc_im_trainval",
            "peptide_only": None,
            "near": None,
        },
        "deepimmuno": {
            "exact": "exact_deepimmuno_peptide_hla",
            "peptide_only": "peptide_only_deepimmuno_different_hla",
            "near": "near_hamming1_deepimmuno_same_hla",
        },
    },
}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise AuditError(f"missing required frozen artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise AuditError(f"CSV has no header: {path}")
        return reader.fieldnames, list(reader)


def _key(patient_id: str, peptide: str, hla: str) -> Key:
    return patient_id.strip(), peptide.strip().upper(), hla.strip()


def load_catalog(root: Path) -> Catalog:
    grouped: dict[Key, list[tuple[str, dict[str, str]]]] = defaultdict(list)
    overlap_rows: dict[str, dict[str, dict[str, str]]] = {}
    for spec in SPECS:
        _header, rows = _read_csv(root / spec.benchmark_path)
        for row in rows:
            grouped[_key(row["patient_id"], row["peptide"], row["hla"])].append(
                (spec.name, row)
            )
        _overlap_header, audit_rows = _read_csv(root / spec.overlap_path)
        overlap_by_id = {row["record_id"]: row for row in audit_rows}
        if len(overlap_by_id) != len(audit_rows):
            raise AuditError(f"duplicate record_id in {spec.overlap_path}")
        overlap_rows[spec.name] = overlap_by_id

    records: dict[Key, BenchmarkRecord] = {}
    dataset_keys: dict[str, set[Key]] = defaultdict(set)
    collapsed: dict[str, int] = defaultdict(int)
    for key, members in grouped.items():
        datasets = {dataset for dataset, _row in members}
        if len(datasets) != 1:
            raise AuditError(f"ambiguous cross-dataset benchmark key: {key}")
        dataset = next(iter(datasets))
        labels = {row["immunogenicity"] for _dataset, row in members}
        if not labels <= {"0", "1"} or len(labels) != 1:
            raise AuditError(f"conflicting or unknown labels for benchmark key: {key}")
        record_ids = tuple(sorted(row["record_id"] for _dataset, row in members))
        if any(record_id not in overlap_rows[dataset] for record_id in record_ids):
            raise AuditError(f"missing training-overlap row for benchmark key: {key}")
        records[key] = BenchmarkRecord(
            dataset=dataset,
            patient_id=key[0],
            peptide=key[1],
            hla=key[2],
            label=int(next(iter(labels))),
            record_ids=record_ids,
        )
        dataset_keys[dataset].add(key)
        collapsed[dataset] += len(members) - 1
    return Catalog(
        records=records,
        dataset_keys={name: frozenset(keys) for name, keys in dataset_keys.items()},
        overlap_rows=overlap_rows,
        collapsed_duplicate_rows=dict(collapsed),
    )


def _model_family(model: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", "", model.lower())
    return MODEL_ALIASES.get(normalized)


def _truthy_overlap(value: str) -> bool:
    return value.strip() == "1"


def _record_has_overlap(
    record: BenchmarkRecord,
    overlap_rows: dict[str, dict[str, dict[str, str]]],
    field: str,
) -> bool:
    return any(
        _truthy_overlap(overlap_rows[record.dataset][record_id].get(field, ""))
        for record_id in record.record_ids
    )


def _leakage_for_model(
    model: str,
    supported: set[Key],
    datasets: set[str],
    catalog: Catalog,
) -> tuple[dict[str, object], set[Key]]:
    family = _model_family(model)
    if family is None:
        return (
            {
                "risk": "unknown_training_reference",
                "recognized_training_reference": False,
                "exact_overlap_records": None,
                "peptide_only_overlap_records": None,
                "near_overlap_records": None,
                "checked_datasets": [],
                "unknown_datasets": sorted(datasets),
            },
            set(),
        )

    exact_keys: set[Key] = set()
    peptide_only_keys: set[Key] = set()
    near_keys: set[Key] = set()
    exact_checked: set[str] = set()
    peptide_checked: set[str] = set()
    near_checked: set[str] = set()
    unknown_datasets: set[str] = set()
    for dataset in datasets:
        fields = OVERLAP_FIELDS.get(dataset, {}).get(family)
        if fields is None or fields["exact"] is None:
            unknown_datasets.add(dataset)
            continue
        exact_checked.add(dataset)
        if fields["peptide_only"] is not None:
            peptide_checked.add(dataset)
        if fields["near"] is not None:
            near_checked.add(dataset)
        for key in supported & set(catalog.dataset_keys[dataset]):
            record = catalog.records[key]
            has_exact_overlap = _record_has_overlap(
                record, catalog.overlap_rows, str(fields["exact"])
            )
            if has_exact_overlap:
                exact_keys.add(key)
            peptide_field = fields["peptide_only"]
            if (
                peptide_field
                and not has_exact_overlap
                and _record_has_overlap(record, catalog.overlap_rows, peptide_field)
            ):
                peptide_only_keys.add(key)
            near_field = fields["near"]
            if near_field and _record_has_overlap(record, catalog.overlap_rows, near_field):
                near_keys.add(key)

    if exact_keys:
        risk = "high_exact_overlap"
    elif near_keys or peptide_only_keys:
        risk = "possible_sequence_overlap"
    elif unknown_datasets:
        risk = "partially_unknown"
    else:
        risk = "no_known_overlap_in_checked_dimensions"
    return (
        {
            "risk": risk,
            "recognized_training_reference": True,
            "model_family": family,
            "exact_overlap_records": len(exact_keys) if exact_checked else None,
            "peptide_only_overlap_records": (
                len(peptide_only_keys) if peptide_checked else None
            ),
            "near_overlap_records": len(near_keys) if near_checked else None,
            "checked_datasets": sorted(exact_checked),
            "unknown_datasets": sorted(unknown_datasets),
            "excluded_from_metrics_as_exact_overlap": len(exact_keys),
        },
        exact_keys,
    )


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _patient_metric_report(
    keys: set[Key],
    scores: dict[Key, float | None],
    catalog: Catalog,
) -> dict[str, object]:
    if not keys:
        return {
            "status": "no_leakage_filtered_common_support",
            "positive_bearing_patients": 0,
            "metrics": {},
        }
    by_patient: dict[str, list[Key]] = defaultdict(list)
    for key in sorted(keys):
        by_patient[catalog.records[key].patient_id].append(key)
    patient_values: list[dict[str, float]] = []
    for patient_keys in by_patient.values():
        labels = [catalog.records[key].label for key in patient_keys]
        if not sum(labels):
            continue
        numeric_scores = [scores[key] for key in patient_keys]
        if any(score is None for score in numeric_scores):
            raise AssertionError("common-support keys must have numeric scores")
        patient_values.append(
            tie_aware_ranking_metrics(
                labels,
                [float(score) for score in numeric_scores],
                KS,
            )
        )
    if not patient_values:
        return {
            "status": "no_positive_bearing_patients",
            "positive_bearing_patients": 0,
            "metrics": {},
        }

    rng = random.Random(BOOTSTRAP_SEED)
    samples: dict[str, list[float]] = {metric: [] for metric in CORE_METRICS}
    for _ in range(BOOTSTRAP_REPLICATES):
        draw = rng.choices(patient_values, k=len(patient_values))
        for metric in CORE_METRICS:
            samples[metric].append(mean(values[metric] for values in draw))
    metrics = {}
    for metric in CORE_METRICS:
        values = samples[metric]
        metrics[metric] = {
            "estimate": mean(patient[metric] for patient in patient_values),
            "ci95": {
                "low": _percentile(values, 0.025),
                "high": _percentile(values, 0.975),
            },
        }
    return {
        "status": "ok",
        "positive_bearing_patients": len(patient_values),
        "bootstrap_unit": "patient",
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "seed": BOOTSTRAP_SEED,
        "metrics": metrics,
    }


def audit_predictions(path: Path, root: Path) -> dict[str, object]:
    """Return a deterministic audit report for a five-column prediction CSV."""
    header, rows = _read_csv(path)
    if len(header) != len(INPUT_COLUMNS) or set(header) != set(INPUT_COLUMNS):
        raise AuditError(
            "prediction CSV header must contain exactly: " + ", ".join(INPUT_COLUMNS)
        )
    if not rows:
        raise AuditError("prediction CSV has no data rows")

    catalog = load_catalog(root)
    predictions: dict[str, dict[Key, float | None]] = defaultdict(dict)
    inferred_datasets: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        model = row["model"].strip()
        key = _key(row["patient_id"], row["peptide"], row["hla"])
        if not model or not all(key):
            raise AuditError(f"line {line_number}: patient_id, peptide, hla and model are required")
        if key not in catalog.records:
            raise AuditError(f"line {line_number}: key not found in a frozen benchmark: {key}")
        if key in predictions[model]:
            raise AuditError(f"line {line_number}: duplicate model/benchmark key for {model}: {key}")
        score_text = row["score"].strip()
        score = None
        if score_text:
            try:
                score = float(score_text)
            except ValueError as error:
                raise AuditError(f"line {line_number}: score is not numeric") from error
            if not math.isfinite(score):
                raise AuditError(f"line {line_number}: score must be finite")
        predictions[model][key] = score
        inferred_datasets.add(catalog.records[key].dataset)

    expected_keys = set().union(
        *(set(catalog.dataset_keys[dataset]) for dataset in inferred_datasets)
    )
    models = sorted(predictions)
    support_by_model: dict[str, set[Key]] = {}
    support_report = {}
    for model in models:
        submitted = set(predictions[model])
        supported = {key for key, score in predictions[model].items() if score is not None}
        support_by_model[model] = supported
        support_report[model] = {
            "expected_records": len(expected_keys),
            "submitted_records": len(submitted),
            "supported_records": len(supported),
            "blank_score_records": len(submitted - supported),
            "omitted_records": len(expected_keys - submitted),
            "coverage": len(supported) / len(expected_keys),
        }

    raw_common = set.intersection(*(support_by_model[model] for model in models))
    leakage_report = {}
    exact_exclusions = {}
    for model in models:
        leakage_report[model], exact_exclusions[model] = _leakage_for_model(
            model,
            support_by_model[model],
            inferred_datasets,
            catalog,
        )
    audited_support = {
        model: support_by_model[model] - exact_exclusions[model] for model in models
    }
    audited_common = set.intersection(*(audited_support[model] for model in models))

    patient_metrics = {
        model: _patient_metric_report(audited_common, predictions[model], catalog)
        for model in models
    }
    return {
        "schema_version": 1,
        "input": {
            "path": str(path),
            "columns": list(INPUT_COLUMNS),
            "score_direction": "higher_is_better",
            "rows": len(rows),
            "models": models,
        },
        "benchmark": {
            "datasets": sorted(inferred_datasets),
            "expected_unique_patient_peptide_hla_records": len(expected_keys),
            "collapsed_duplicate_source_rows": sum(
                catalog.collapsed_duplicate_rows.get(dataset, 0)
                for dataset in inferred_datasets
            ),
        },
        "leakage": leakage_report,
        "support": {
            "by_model": support_report,
            "raw_common_support": {
                "records": len(raw_common),
                "coverage": len(raw_common) / len(expected_keys),
            },
            "leakage_filtered_common_support": {
                "records": len(audited_common),
                "coverage": len(audited_common) / len(expected_keys),
            },
        },
        "patient_metrics": {
            "basis": "leakage-filtered common support; pMHC ranking unit",
            "models": patient_metrics,
        },
        "limitations": [
            "Only exact model aliases with frozen training references receive checked leakage labels.",
            "Unknown training overlap remains unknown; absence of a known match is not proof of independence.",
            "Omitted input rows are counted as unsupported because the five-column contract has no status field.",
        ],
    }
