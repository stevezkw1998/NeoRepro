#!/usr/bin/env python3
"""Build the canonical pilot benchmark from the frozen DeepImmuno TESLA subset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

FIELDS = [
    "record_id", "sample_id", "patient_id", "study_id", "cancer_type", "gene",
    "mutation", "wildtype_sequence", "mutant_sequence", "peptide", "peptide_length",
    "hla", "mhc_class", "assay_type", "immunogenicity", "presentation_evidence",
    "mass_spec_evidence", "clinical_context", "source_doi", "source_pmid", "source_url",
    "original_dataset", "evidence_level", "source_license", "source_checksum", "accessed_at",
]
SOURCE_CHECKSUM = "b3a38ea1a871a1cfc861a2809f9f2193228876746fb8964151255a6ea9bd0c18"
SOURCE_URL = "https://raw.githubusercontent.com/frankligy/DeepImmuno/df42ac5b6bddfe531268335e2dcb496559cd488b/reproduce/data/ori_test_cells.csv"
HLA = re.compile(r"^HLA-([ABC])\*(\d{2}):?(\d{2,3})$")


def normalize_hla(value: str) -> str:
    value = value.strip().upper()
    match = HLA.fullmatch(value)
    if not match:
        raise ValueError(f"unresolved HLA allele: {value}")
    locus, field1, field2 = match.groups()
    return f"HLA-{locus}*{field1}:{field2}"


def stable_record_id(patient: str, peptide: str, hla: str) -> str:
    key = f"deepimmuno_tesla_subset|{patient}|{peptide}|{hla}".encode()
    return "tesla-" + hashlib.sha256(key).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw/deepimmuno_tesla_subset.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/benchmark.csv"))
    parser.add_argument("--report", type=Path, default=Path("data/processing_report.json"))
    args = parser.parse_args()
    payload = args.input.read_bytes()
    if hashlib.sha256(payload).hexdigest() != SOURCE_CHECKSUM:
        raise SystemExit("pilot source checksum differs from frozen manifest")
    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        source_rows = list(csv.DictReader(handle))
    rows: list[dict[str, str | int]] = []
    seen: dict[str, dict[str, str]] = {}
    removed_exact_duplicates: list[dict[str, str | int]] = []
    for source_line, source in enumerate(source_rows, start=2):
        peptide = source["peptide"].strip().upper()
        hla = normalize_hla(source["HLA"])
        patient = f"TESLA-{source['patient'].strip()}"
        record_id = stable_record_id(patient, peptide, hla)
        if record_id in seen:
            if source != seen[record_id]:
                raise SystemExit(f"non-identical duplicate canonical identity: {record_id}")
            removed_exact_duplicates.append({"record_id": record_id, "source_line": source_line})
            continue
        seen[record_id] = source
        rows.append({
            "record_id": record_id,
            "sample_id": patient,
            "patient_id": patient,
            "study_id": "TESLA2020",
            "cancer_type": "unknown_melanoma_or_nsclc",
            "gene": "unknown",
            "mutation": "unknown",
            "wildtype_sequence": "unknown",
            "mutant_sequence": "unknown",
            "peptide": peptide,
            "peptide_length": len(peptide),
            "hla": hla,
            "mhc_class": "I",
            "assay_type": "TESLA pMHC multimer-based T-cell response",
            "immunogenicity": source["immunogenicity"].strip(),
            "presentation_evidence": "candidate selected for TESLA immune testing",
            "mass_spec_evidence": "unknown",
            "clinical_context": "six TESLA subjects; exact melanoma/NSCLC mapping pending source-table recovery",
            "source_doi": "10.1016/j.cell.2020.09.015",
            "source_pmid": "33038301",
            "source_url": SOURCE_URL,
            "original_dataset": "DeepImmuno-filtered TESLA subset",
            "evidence_level": "experimentally tested immune response; transformed public subset",
            "source_license": "MIT repository distribution; original TESLA terms tracked separately",
            "source_checksum": SOURCE_CHECKSUM,
            "accessed_at": "2026-08-20",
        })
    rows.sort(key=lambda row: (str(row["patient_id"]), str(row["peptide"]), str(row["hla"])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "source_rows": len(source_rows),
        "output_rows": len(rows),
        "removed_exact_duplicate_rows": removed_exact_duplicates,
        "source_sha256": SOURCE_CHECKSUM,
        "rule": "remove only byte-equivalent source rows sharing patient, peptide, and normalized HLA",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    positives = sum(int(row["immunogenicity"]) for row in rows)
    patients = len({row["patient_id"] for row in rows})
    print(
        f"wrote {len(rows)} rows, {positives} positives, {patients} patients; "
        f"removed {len(removed_exact_duplicates)} exact duplicate rows -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
