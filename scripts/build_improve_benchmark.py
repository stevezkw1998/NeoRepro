#!/usr/bin/env python3
"""Build the provenance-complete IMPROVE patient benchmark from its pinned data archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

SOURCE_URL = (
    "https://raw.githubusercontent.com/SRHgroup/IMPROVE_paper/"
    "c67094276b52358b5202ad9e5597acd87888ea1d/data.zip"
)
SOURCE_DOI = "10.3389/fimmu.2024.1360281"
MEMBER = "data/01_data/01_Validated_neoepitopes.txt"
EXPECTED = {"rows": 17520, "positives": 467, "patients": 70, "cohorts": 3}
COHORTS = {
    "bladder": {
        "study_id": "IMPROVE-mUC",
        "cancer_type": "metastatic_urothelial_carcinoma",
        "clinical_context": "PD-L1 checkpoint inhibition",
        "source_doi": "10.1038/s41467-022-29342-0",
        "source_pmid": "35410325",
    },
    "melanoma": {
        "study_id": "IMPROVE-melanoma",
        "cancer_type": "metastatic_melanoma",
        "clinical_context": "tumor-infiltrating-lymphocyte adoptive cell therapy",
        "source_doi": "10.1172/JCI150535",
        "source_pmid": "34813506",
    },
    "Basket": {
        "study_id": "IMPROVE-basket",
        "cancer_type": "mixed_pan_cancer",
        "clinical_context": "basket trial with checkpoint blockade",
        "source_doi": "10.1101/2024.03.17.585416",
        "source_pmid": "",
    },
}
FIELDS = [
    "record_id",
    "sample_id",
    "patient_id",
    "study_id",
    "cancer_type",
    "gene",
    "mutation",
    "wildtype_sequence",
    "mutant_sequence",
    "peptide",
    "peptide_length",
    "hla",
    "mhc_class",
    "assay_type",
    "immunogenicity",
    "presentation_evidence",
    "mass_spec_evidence",
    "clinical_context",
    "source_doi",
    "source_pmid",
    "source_url",
    "original_dataset",
    "evidence_level",
    "source_license",
    "source_checksum",
    "accessed_at",
]


def normalize_hla(value: str) -> str:
    value = value.strip().upper().replace("HLA-", "")
    return f"HLA-{value[0]}*{value[1:]}"


def stable_id(patient: str, hla: str, peptide: str) -> str:
    identity = f"{patient}|{hla}|{peptide}".encode()
    return "improve-" + hashlib.sha256(identity).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--member", default=MEMBER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--accessed-at", default="2026-08-20")
    args = parser.parse_args()

    with ZipFile(args.archive) as archive:
        raw = archive.read(args.member)
    member_hash = hashlib.sha256(raw).hexdigest()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter="\t")
    rows = []
    for source in reader:
        cohort = COHORTS[source["cohort"]]
        peptide = source["Mut_peptide"].strip().upper()
        wildtype = source["Norm_peptide"].strip().upper()
        hla = normalize_hla(source["HLA_allele"])
        label_text = source["response"].strip().lower()
        if label_text not in {"yes", "no", "1", "0"}:
            raise ValueError(f"unsupported response label: {source['response']!r}")
        label = int(label_text in {"yes", "1"})
        rows.append(
            {
                "record_id": stable_id(source["Patient"], hla, peptide),
                "sample_id": source["Sample"],
                "patient_id": source["Patient"],
                "study_id": cohort["study_id"],
                "cancer_type": cohort["cancer_type"],
                "gene": source["Gene_Symbol"] or "unknown",
                "mutation": source["Amino_Acid_Change"] or "unknown",
                "wildtype_sequence": wildtype,
                "mutant_sequence": peptide,
                "peptide": peptide,
                "peptide_length": len(peptide),
                "hla": hla,
                "mhc_class": "I",
                "assay_type": "DNA-barcoded peptide-MHC multimer T-cell recognition",
                "immunogenicity": label,
                "presentation_evidence": (
                    "candidate preselection primarily used NetMHCpan 4.0 RankEL; "
                    "not experimental presentation evidence"
                ),
                "mass_spec_evidence": "unknown",
                "clinical_context": cohort["clinical_context"],
                "source_doi": cohort["source_doi"],
                "source_pmid": cohort["source_pmid"],
                "source_url": SOURCE_URL,
                "original_dataset": f"IMPROVE {source['cohort']} cohort",
                "evidence_level": "patient-matched T-cell recognition screen",
                "source_license": "CC-BY-4.0 article and data-availability statement",
                "source_checksum": member_hash,
                "accessed_at": args.accessed_at,
            }
        )

    record_ids = [row["record_id"] for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("duplicate patient-HLA-peptide identity in IMPROVE source")
    observed = {
        "rows": len(rows),
        "positives": sum(int(row["immunogenicity"]) for row in rows),
        "patients": len({row["patient_id"] for row in rows}),
        "cohorts": len({row["study_id"] for row in rows}),
    }
    if observed != EXPECTED:
        raise ValueError(f"source drift: expected {EXPECTED}, observed {observed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        **observed,
        "positive_bearing_patients": len(
            {row["patient_id"] for row in rows if int(row["immunogenicity"]) == 1}
        ),
        "negative_only_patients": len({row["patient_id"] for row in rows})
        - len({row["patient_id"] for row in rows if int(row["immunogenicity"]) == 1}),
        "hla_alleles": len({row["hla"] for row in rows}),
        "peptide_lengths": dict(
            sorted(Counter(str(row["peptide_length"]) for row in rows).items())
        ),
        "rows_by_study": dict(sorted(Counter(row["study_id"] for row in rows).items())),
        "positives_by_study": dict(
            sorted(
                Counter(row["study_id"] for row in rows if int(row["immunogenicity"]) == 1).items()
            )
        ),
        "source_archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "source_member": args.member,
        "source_member_sha256": member_hash,
        "source_revision": "c67094276b52358b5202ad9e5597acd87888ea1d",
        "source_url": SOURCE_URL,
        "article_doi": SOURCE_DOI,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(observed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
