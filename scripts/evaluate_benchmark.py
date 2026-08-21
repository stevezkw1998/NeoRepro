#!/usr/bin/env python3
"""Join benchmark/prediction CSVs and run a paired patient-level evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from itertools import combinations
from math import comb
from pathlib import Path
from statistics import mean

KS = (5, 10, 20)


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        value = (start + 1 + end) / 2
        for index in order[start:end]:
            result[index] = value
        start = end
    return result


def pooled(rows: list[dict[str, object]]) -> dict[str, float | int | None]:
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    positives = sum(labels)
    negatives = len(labels) - positives
    auroc = None
    if positives and negatives:
        positive_ranks = sum(
            rank for rank, label in zip(ranks(scores), labels, strict=True) if label
        )
        auroc = (positive_ranks - positives * (positives + 1) / 2) / (positives * negatives)
    average_precision = None
    if positives:
        true_positives = 0
        predicted_positives = 0
        average_precision = 0.0
        order = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
        start = 0
        while start < len(order):
            end = start + 1
            while end < len(order) and scores[order[end]] == scores[order[start]]:
                end += 1
            group_positives = sum(labels[index] for index in order[start:end])
            true_positives += group_positives
            predicted_positives += end - start
            average_precision += (group_positives / positives) * (
                true_positives / predicted_positives
            )
            start = end
    return {
        "n": len(rows),
        "positives": positives,
        "auroc": auroc,
        "average_precision": average_precision,
        "brier": mean((score - label) ** 2 for score, label in zip(scores, labels, strict=True)),
    }


def patient_values(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row["patient_id"])].append(row)
    result = {}
    for patient, patient_rows in groups.items():
        ordered = sorted(patient_rows, key=lambda row: -float(row["score"]))
        positives = sum(int(row["label"]) for row in ordered)
        if not positives:
            continue
        score_groups = []
        start = 0
        while start < len(ordered):
            end = start + 1
            while end < len(ordered) and ordered[end]["score"] == ordered[start]["score"]:
                end += 1
            group = ordered[start:end]
            score_groups.append((len(group), sum(int(row["label"]) for row in group)))
            start = end

        offset = 0
        expected_mrr = 0.0
        for size, group_positives in score_groups:
            if group_positives:
                denominator = comb(size, group_positives)
                expected_mrr = sum(
                    (comb(size - first, group_positives - 1) / denominator)
                    / (offset + first)
                    for first in range(1, size - group_positives + 2)
                )
                break
            offset += size
        metrics = {"mrr": expected_mrr}
        for k in KS:
            limit = min(k, len(ordered))
            remaining = limit
            offset = 0
            expected_hits = 0.0
            expected_dcg = 0.0
            zero_hit_probability = 1.0
            for size, group_positives in score_groups:
                if not remaining:
                    break
                selected = min(remaining, size)
                expected_hits += selected * group_positives / size
                expected_dcg += (group_positives / size) * sum(
                    1 / math.log2(rank + 1)
                    for rank in range(offset + 1, offset + selected + 1)
                )
                if selected == size:
                    if group_positives:
                        zero_hit_probability = 0.0
                elif zero_hit_probability and group_positives:
                    zero_hit_probability *= comb(size - group_positives, selected) / comb(
                        size, selected
                    )
                remaining -= selected
                offset += selected
            metrics[f"recall@{k}"] = expected_hits / positives
            metrics[f"precision@{k}"] = expected_hits / limit
            metrics[f"hitrate@{k}"] = 1 - zero_hit_probability
            ideal_hits = min(positives, limit)
            idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
            metrics[f"ndcg@{k}"] = expected_dcg / idcg
        result[patient] = metrics
    return result


def aggregate_patient(values: dict[str, dict[str, float]]) -> dict[str, float | int]:
    result: dict[str, float | int] = {"positive_bearing_patients": len(values)}
    if not values:
        return result
    for metric in next(iter(values.values())):
        result[metric] = mean(patient[metric] for patient in values.values())
    return result


def comparison_values(rows: list[dict[str, object]]) -> dict[str, float | int | None]:
    pooled_metrics = pooled(rows)
    patient_metrics = aggregate_patient(patient_values(rows))
    return {
        "auroc": pooled_metrics["auroc"],
        "average_precision": pooled_metrics["average_precision"],
        **{
            key: value
            for key, value in patient_metrics.items()
            if key != "positive_bearing_patients"
        },
    }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def interval(values: list[float]) -> dict[str, float]:
    return {"low": percentile(values, 0.025), "high": percentile(values, 0.975)}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260820)
    args = parser.parse_args()

    benchmark_rows = load_csv(args.benchmark)
    benchmark = {row["record_id"]: row for row in benchmark_rows}
    if len(benchmark) != len(benchmark_rows):
        raise SystemExit("benchmark record_id values are not unique")
    required = {"patient_id", "study_id", "hla", "immunogenicity"}
    if benchmark_rows and required - set(benchmark_rows[0]):
        raise SystemExit("benchmark lacks required evaluation columns")

    joined: dict[str, list[dict[str, object]]] = {}
    metadata: dict[str, dict[str, object]] = {}
    missingness = []
    for path in args.predictions:
        prediction_rows = load_csv(path)
        if not prediction_rows:
            raise SystemExit(f"empty prediction file: {path}")
        predictor = prediction_rows[0]["predictor"]
        if predictor in joined:
            raise SystemExit(f"duplicate predictor name: {predictor}")
        seen = set()
        rows = []
        status_counts: dict[str, int] = defaultdict(int)
        for raw in prediction_rows:
            record_id = raw["record_id"]
            if record_id in seen:
                raise SystemExit(f"{predictor}: duplicate record_id {record_id}")
            seen.add(record_id)
            status_counts[raw["status"]] += 1
            if record_id not in benchmark:
                raise SystemExit(f"{predictor}: unknown record_id {record_id}")
            if raw["status"] != "predicted":
                continue
            try:
                score = float(raw["score"])
            except ValueError as error:
                raise SystemExit(f"{predictor}: nonnumeric predicted score") from error
            if not math.isfinite(score):
                raise SystemExit(f"{predictor}: nonfinite predicted score")
            direction = raw["score_direction"]
            if direction not in {"higher", "lower"}:
                raise SystemExit(f"{predictor}: invalid score_direction {direction}")
            source = benchmark[record_id]
            rows.append(
                {
                    "record_id": record_id,
                    "patient_id": source["patient_id"],
                    "study_id": source["study_id"],
                    "hla": source["hla"],
                    "label": int(source["immunogenicity"]),
                    "score": score if direction == "higher" else -score,
                    "raw_score": score,
                }
            )
        missing_ids = set(benchmark) - seen
        if missing_ids:
            raise SystemExit(f"{predictor}: omitted {len(missing_ids)} benchmark rows")
        joined[predictor] = rows
        metadata[predictor] = {
            "version": prediction_rows[0]["predictor_version"],
            "task": prediction_rows[0]["task"],
            "score_direction": prediction_rows[0]["score_direction"],
            "source": str(path),
        }
        for status, count in sorted(status_counts.items()):
            missingness.append({"predictor": predictor, "status": status, "count": count})

    metrics: dict[str, object] = {}
    patient_by_predictor = {}
    for predictor, rows in joined.items():
        patient = patient_values(rows)
        patient_by_predictor[predictor] = patient
        hla = {}
        hla_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        study = {}
        study_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            hla_groups[str(row["hla"])].append(row)
            study_groups[str(row["study_id"])].append(row)
        for allele, allele_rows in sorted(hla_groups.items()):
            hla[allele] = pooled(allele_rows)
        for study_id, study_rows in sorted(study_groups.items()):
            study[study_id] = pooled(study_rows)
        metrics[predictor] = {
            "metadata": metadata[predictor],
            "pooled": pooled(rows),
            "patient": aggregate_patient(patient),
            "patient_values": patient,
            "hla": hla,
            "study": study,
        }

    rng = random.Random(args.seed)
    patients = sorted({row["patient_id"] for row in benchmark_rows})
    samples: dict[str, dict[str, list[float]]] = {
        predictor: defaultdict(list) for predictor in joined
    }
    paired_samples: dict[tuple[str, str], dict[str, list[float]]] = {}
    eligible_pairs = [
        pair
        for pair in combinations(sorted(joined), 2)
        if metadata[pair[0]]["task"] == metadata[pair[1]]["task"]
    ]
    for pair in eligible_pairs:
        paired_samples[pair] = defaultdict(list)

    common_pair_rows = {}
    common_pair_points = {}
    full_pair_support = {}
    common_support = []
    for pair in eligible_pairs:
        left, right = pair
        common_ids = {str(row["record_id"]) for row in joined[left]} & {
            str(row["record_id"]) for row in joined[right]
        }
        if not common_ids:
            raise SystemExit(f"{left} and {right} have no common predicted rows")
        pair_rows = {
            predictor: [row for row in joined[predictor] if str(row["record_id"]) in common_ids]
            for predictor in pair
        }
        common_pair_rows[pair] = pair_rows
        full_pair_support[pair] = all(
            len(pair_rows[predictor]) == len(joined[predictor]) for predictor in pair
        )
        common_pair_points[pair] = {
            predictor: comparison_values(pair_rows[predictor]) for predictor in pair
        }
        common_support.append(
            {
                "left": left,
                "right": right,
                "task": metadata[left]["task"],
                "n_common": len(common_ids),
                "positives_common": sum(int(row["label"]) for row in pair_rows[left]),
                "patients_common": len({str(row["patient_id"]) for row in pair_rows[left]}),
            }
        )

    rows_by_patient = {
        predictor: {
            patient: [row for row in rows if row["patient_id"] == patient] for patient in patients
        }
        for predictor, rows in joined.items()
    }
    for _ in range(args.bootstrap):
        draws = rng.choices(patients, k=len(patients))
        replicate = {}
        for predictor in joined:
            boot_rows = []
            for draw_index, patient in enumerate(draws):
                boot_rows.extend(
                    {**row, "patient_id": f"{draw_index}:{patient}"}
                    for row in rows_by_patient[predictor][patient]
                )
            patient_metrics = aggregate_patient(patient_values(boot_rows))
            pooled_metrics = pooled(boot_rows)
            values = {
                "auroc": pooled_metrics["auroc"],
                "average_precision": pooled_metrics["average_precision"],
                **{
                    key: value
                    for key, value in patient_metrics.items()
                    if key != "positive_bearing_patients"
                },
            }
            replicate[predictor] = values
            for metric, value in values.items():
                if isinstance(value, (int, float)) and math.isfinite(value):
                    samples[predictor][metric].append(float(value))
        for pair in eligible_pairs:
            left, right = pair
            if full_pair_support[pair]:
                pair_replicate = {predictor: replicate[predictor] for predictor in pair}
            else:
                pair_rows = common_pair_rows[pair]
                pair_patients = sorted({str(row["patient_id"]) for row in pair_rows[left]})
                pair_draws = rng.choices(pair_patients, k=len(pair_patients))
                pair_replicate = {}
                for predictor in pair:
                    by_patient: dict[str, list[dict[str, object]]] = defaultdict(list)
                    for row in pair_rows[predictor]:
                        by_patient[str(row["patient_id"])].append(row)
                    boot_rows = []
                    for draw_index, patient in enumerate(pair_draws):
                        boot_rows.extend(
                            {**row, "patient_id": f"{draw_index}:{patient}"}
                            for row in by_patient[patient]
                        )
                    pair_replicate[predictor] = comparison_values(boot_rows)
            for metric in set(pair_replicate[left]) & set(pair_replicate[right]):
                left_value = pair_replicate[left][metric]
                right_value = pair_replicate[right][metric]
                if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
                    paired_samples[pair][metric].append(left_value - right_value)

    for predictor, predictor_metrics in metrics.items():
        predictor_metrics["patient_bootstrap_95ci"] = {
            metric: interval(values) for metric, values in samples[predictor].items() if values
        }
    paired = []
    for (left, right), metric_samples in paired_samples.items():
        support = next(
            row for row in common_support if row["left"] == left and row["right"] == right
        )
        for metric, values in sorted(metric_samples.items()):
            point_left = common_pair_points[(left, right)][left].get(metric)
            point_right = common_pair_points[(left, right)][right].get(metric)
            confidence = interval(values)
            paired.append(
                {
                    "left": left,
                    "right": right,
                    "task": metadata[left]["task"],
                    "metric": metric,
                    "n_common": support["n_common"],
                    "positives_common": support["positives_common"],
                    "patients_common": support["patients_common"],
                    "left_value_common": point_left,
                    "right_value_common": point_right,
                    "difference_left_minus_right": float(point_left) - float(point_right),
                    "ci_low": confidence["low"],
                    "ci_high": confidence["high"],
                }
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "config": {"bootstrap": args.bootstrap, "seed": args.seed, "ks": list(KS)},
        "benchmark": str(args.benchmark),
        "metrics": metrics,
        "common_support": common_support,
        "paired_same_task": paired,
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    with (args.output_dir / "missingness.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["predictor", "status", "count"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(missingness)
    with (args.output_dir / "paired_differences.csv").open("w", newline="") as handle:
        fields = [
            "left",
            "right",
            "task",
            "metric",
            "n_common",
            "positives_common",
            "patients_common",
            "left_value_common",
            "right_value_common",
            "difference_left_minus_right",
            "ci_low",
            "ci_high",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(paired)
    print(
        json.dumps(
            {
                "predictors": list(joined),
                "rows": {key: len(value) for key, value in joined.items()},
                "output_dir": str(args.output_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
