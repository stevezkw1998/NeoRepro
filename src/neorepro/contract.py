"""Public extension contract: cards, artifacts, gates, evaluation and reports."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from neorepro.metrics import auroc, tie_aware_ranking_metrics

DATASET_REQUIRED = {
    "dataset_id",
    "version",
    "records_path",
    "label_column",
    "patient_id_column",
    "score_tasks",
}
PREDICTOR_REQUIRED = {"predictor_id", "version", "task", "score_direction", "adapter", "license"}
ARTIFACT_REQUIRED = {
    "record_id",
    "predictor",
    "predictor_version",
    "task",
    "score",
    "score_direction",
    "status",
}
STATUSES = {"predicted", "unsupported", "failed", "invalid"}


class ContractError(ValueError):
    pass


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ContractError(f"invalid JSON: {path}: {e}") from e


def validate_card(path: Path, kind: str) -> dict:
    if kind not in {"dataset", "predictor"}:
        raise ContractError(f"unknown card kind: {kind}")
    obj = _json(path)
    required = DATASET_REQUIRED if kind == "dataset" else PREDICTOR_REQUIRED
    missing = sorted(required - obj.keys())
    if missing:
        raise ContractError(f"{kind} card missing fields: {', '.join(missing)}")
    if not isinstance(obj["version"], str) or not obj["version"]:
        raise ContractError("card version must be non-empty")
    if kind == "predictor" and obj["score_direction"] not in {"higher", "lower"}:
        raise ContractError("score_direction must be higher or lower")
    return {
        "valid": True,
        "kind": kind,
        "path": str(path),
        "id": obj.get("dataset_id", obj.get("predictor_id")),
        "version": obj["version"],
    }


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ContractError(f"CSV has no header: {path}")
        return list(r), list(r.fieldnames)


def validate_artifact(path: Path, benchmark: Path | None = None) -> dict:
    rows, header = read_csv(path)
    missing = sorted(ARTIFACT_REQUIRED - set(header))
    if missing:
        raise ContractError(f"prediction artifact missing columns: {', '.join(missing)}")
    if not rows:
        raise ContractError("prediction artifact has no rows")
    ids = set()
    problems = []
    for n, row in enumerate(rows, 2):
        if not row["record_id"] or row["record_id"] in ids:
            problems.append(f"line {n}: duplicate/blank record_id")
        ids.add(row["record_id"])
        if row["status"] not in STATUSES:
            problems.append(f"line {n}: unknown status {row['status']}")
        if row["score_direction"] not in {"higher", "lower"}:
            problems.append(f"line {n}: invalid score_direction")
        if row["status"] == "predicted":
            try:
                if not math.isfinite(float(row["score"])):
                    raise ValueError
            except ValueError:
                problems.append(f"line {n}: predicted score must be finite")
    if benchmark:
        brows, _ = read_csv(benchmark)
        expected = {r["record_id"] for r in brows}
        if ids != expected:
            problems.append(
                f"record support mismatch: submitted={len(ids)} expected={len(expected)}"
            )
    if problems:
        raise ContractError("; ".join(problems[:8]))
    return {
        "valid": True,
        "rows": len(rows),
        "predictors": sorted({r["predictor"] for r in rows}),
        "tasks": sorted({r["task"] for r in rows}),
        "predicted": sum(r["status"] == "predicted" for r in rows),
        "missing": sum(r["status"] != "predicted" for r in rows),
    }


def evaluate(
    benchmark: Path, artifacts: list[Path], output: Path, overlap_audit: Path | None = None
) -> dict:
    b, _ = read_csv(benchmark)
    labels = {r["record_id"]: int(r["label"] if "label" in r else r["immunogenicity"]) for r in b}
    patients = {r["record_id"]: r.get("patient_id", "unknown") for r in b}
    result = {
        "schema_version": 1,
        "benchmark": str(benchmark),
        "models": {},
        "gates": {"common_support": True, "missingness": True, "leakage": "not_checked"},
    }
    if overlap_audit:
        audit_rows, audit_header = read_csv(overlap_audit)
        if "record_id" not in audit_header:
            raise ContractError("overlap audit must contain record_id")
        audit_ids = {r["record_id"] for r in audit_rows}
        if not audit_ids <= set(labels):
            raise ContractError("overlap audit contains record_id absent from benchmark")
        result["gates"]["leakage"] = {
            "status": "checked",
            "audit": str(overlap_audit),
            "rows": len(audit_rows),
        }
    parsed = []
    for p in artifacts:
        validate_artifact(p, benchmark)
        rows, _ = read_csv(p)
        parsed.append(rows)
    supports = [{r["record_id"] for r in rows if r["status"] == "predicted"} for rows in parsed]
    common = set.intersection(*supports) if supports else set()
    result["common_support"] = {
        "records": len(common),
        "coverage": len(common) / len(labels) if labels else 0,
    }
    for rows, support in zip(parsed, supports):
        name = rows[0]["predictor"]
        scores = {r["record_id"]: float(r["score"]) for r in rows if r["status"] == "predicted"}
        use = common
        direction = rows[0]["score_direction"]
        vals = [scores[k] if direction == "higher" else -scores[k] for k in use]
        labs = [labels[k] for k in use]
        model = {
            "rows": len(rows),
            "predicted": len(support),
            "missing": len(set(labels) - support),
            "coverage": len(support) / len(labels),
            "task": rows[0]["task"],
            "score_direction": direction,
        }
        if len(set(labs)) == 2:
            model["auroc"] = auroc(labs, vals)
        by = defaultdict(list)
        for k in use:
            by[patients[k]].append(k)
        pm = []
        for ks in by.values():
            if any(labels[k] for k in ks):
                pm.append(
                    tie_aware_ranking_metrics(
                        [labels[k] for k in ks],
                        [scores[k] if direction == "higher" else -scores[k] for k in ks],
                        [5],
                    )
                )
        if pm:
            model["patient_ndcg@5"] = sum(x["ndcg@5"] for x in pm) / len(pm)
        result["models"][name] = model
    output.parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def markdown_report(result: dict, output: Path):
    lines = [
        "# NeoRepro evaluation report",
        "",
        f"Common support: **{result['common_support']['records']}** records ({result['common_support']['coverage']:.1%}).",
        "",
        "| Predictor | Task | Coverage | AUROC | Patient NDCG@5 |",
        "|---|---|---:|---:|---:|",
    ]
    for name, m in result["models"].items():
        lines.append(
            f"| {name} | {m['task']} | {m['coverage']:.1%} | {m.get('auroc', 'unknown')} | {m.get('patient_ndcg@5', 'unknown')} |"
        )
    lines += [
        "",
        "## Gates",
        "",
        "- Common support: passed for reported comparisons.",
        "- Missingness: reported per predictor; no failed row was imputed.",
        "- Leakage: run `neorepro overlap-audit`; unknown training overlap remains unknown.",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
