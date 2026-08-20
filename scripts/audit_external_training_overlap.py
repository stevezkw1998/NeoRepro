#!/usr/bin/env python3
"""Audit a canonical benchmark against PRIME2/BigMHC and DeepImmuno training rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from audit_prime2_overlap import load_training_rows


def normalize_hla(value: object) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", str(value).upper().removeprefix("HLA"))
    match = re.fullmatch(r"([ABC])(\d{2})(\d{2})", compact)
    if not match:
        raise ValueError(f"unsupported HLA value: {value!r}")
    locus, group, protein = match.groups()
    return f"HLA-{locus}*{group}:{protein}"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def indexes(
    rows: list[dict[str, object]],
) -> tuple[
    dict[tuple[str, str], set[int]],
    dict[str, set[int]],
    dict[tuple[str, int, str], set[str]],
]:
    exact: dict[tuple[str, str], set[int]] = defaultdict(set)
    peptide_only: dict[str, set[int]] = defaultdict(set)
    near: dict[tuple[str, int, str], set[str]] = defaultdict(set)
    for row in rows:
        peptide = str(row["peptide"]).strip().upper()
        hla = str(row["hla"])
        label = int(row["label"])
        exact[(peptide, hla)].add(label)
        peptide_only[peptide].add(label)
        for index in range(len(peptide)):
            near[(hla, len(peptide), peptide[:index] + "*" + peptide[index + 1 :])].add(
                peptide
            )
    return exact, peptide_only, near


def near_matches(
    peptide: str, hla: str, near: dict[tuple[str, int, str], set[str]]
) -> set[str]:
    result: set[str] = set()
    for index in range(len(peptide)):
        result.update(near.get((hla, len(peptide), peptide[:index] + "*" + peptide[index + 1 :]), set()))
    result.discard(peptide)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--prime2-archive", type=Path, required=True)
    parser.add_argument("--deepimmuno-training", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    benchmark = load_csv(args.benchmark)
    prime_rows, prime_workbook_hash = load_training_rows(
        args.prime2_archive, "mmc6.xlsx", "TableS4"
    )
    prime = [
        {
            "peptide": row["peptide"],
            "hla": row["hla"],
            "label": row["label"],
            "random": row["random"],
        }
        for row in prime_rows
    ]
    deepimmuno_raw = load_csv(args.deepimmuno_training)
    deepimmuno = []
    deepimmuno_unresolved_hla = 0
    for row in deepimmuno_raw:
        try:
            hla = normalize_hla(row["HLA"])
        except ValueError:
            deepimmuno_unresolved_hla += 1
            continue
        label_text = row["immunogenicity"].strip().lower()
        if label_text != "negative" and not label_text.startswith("positive"):
            raise ValueError(f"unknown DeepImmuno label: {row['immunogenicity']!r}")
        deepimmuno.append(
            {
                "peptide": row["peptide"].strip().upper(),
                "hla": hla,
                "label": int(label_text.startswith("positive")),
            }
        )

    prime_exact, prime_peptide, prime_near = indexes(prime)
    deep_exact, deep_peptide, deep_near = indexes(deepimmuno)
    prime_random: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in prime:
        prime_random[(str(row["peptide"]), str(row["hla"]))].add(int(row["random"]))

    output_rows = []
    for row in benchmark:
        peptide = row["peptide"].strip().upper()
        hla = row["hla"]
        label = int(row["immunogenicity"])
        key = (peptide, hla)
        prime_labels = prime_exact.get(key, set())
        deep_labels = deep_exact.get(key, set())
        prime_neighbours = near_matches(peptide, hla, prime_near)
        deep_neighbours = near_matches(peptide, hla, deep_near)
        bigmhc_exact = bool(
            len(peptide) in {9, 10} and 0 in prime_random.get(key, set())
        )
        output_rows.append(
            {
                "record_id": row["record_id"],
                "benchmark_label": label,
                "exact_prime2_peptide_hla": int(bool(prime_labels)),
                "exact_bigmhc_im_trainval": int(bigmhc_exact),
                "exact_deepimmuno_peptide_hla": int(bool(deep_labels)),
                "union_known_exact_overlap": int(bool(prime_labels or deep_labels)),
                "prime2_label_conflict": int(any(value != label for value in prime_labels)),
                "deepimmuno_label_conflict": int(any(value != label for value in deep_labels)),
                "peptide_only_prime2_different_hla": int(
                    bool(prime_peptide.get(peptide)) and not prime_labels
                ),
                "peptide_only_deepimmuno_different_hla": int(
                    bool(deep_peptide.get(peptide)) and not deep_labels
                ),
                "near_hamming1_prime2_same_hla": int(bool(prime_neighbours)),
                "near_hamming1_deepimmuno_same_hla": int(bool(deep_neighbours)),
                "deephlapan_training_overlap": "unknown_official_row_manifest_unavailable",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    summary = {
        "benchmark": str(args.benchmark),
        "benchmark_rows": len(benchmark),
        "prime2_training_rows": len(prime),
        "prime2_workbook_sha256": prime_workbook_hash,
        "deepimmuno_training_rows_source": len(deepimmuno_raw),
        "deepimmuno_training_rows_resolved": len(deepimmuno),
        "deepimmuno_unresolved_hla_rows": deepimmuno_unresolved_hla,
        "benchmark_exact_prime2": sum(row["exact_prime2_peptide_hla"] for row in output_rows),
        "benchmark_exact_bigmhc_im_trainval": sum(
            row["exact_bigmhc_im_trainval"] for row in output_rows
        ),
        "benchmark_exact_deepimmuno": sum(
            row["exact_deepimmuno_peptide_hla"] for row in output_rows
        ),
        "benchmark_union_known_exact_overlap": sum(
            row["union_known_exact_overlap"] for row in output_rows
        ),
        "benchmark_near_prime2": sum(
            row["near_hamming1_prime2_same_hla"] for row in output_rows
        ),
        "benchmark_near_deepimmuno": sum(
            row["near_hamming1_deepimmuno_same_hla"] for row in output_rows
        ),
        "overlap_dimensions": {
            "prime2_exact_peptide_hla": "checked",
            "bigmhc_published_immunogenicity_construction": "checked_via_prime2_random_flag",
            "deepimmuno_exact_peptide_hla": "checked",
            "near_sequence_same_hla_same_length": "checked_for_prime2_and_deepimmuno",
            "deephlapan_training_identity": "unknown_official_row_manifest_unavailable",
            "patient_and_study_training_identity": "unavailable",
        },
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
