#!/usr/bin/env python3
"""Build the RCC vaccine cohort from the checksum-pinned Nature workbook."""

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

EXPECTED = "c113c42b0773049fe7e3f6b983485d15cd00cb847c6fd5de532cea4c9715d0c1"
AA = set("ACDEFGHIKLMNPQRSTVWY")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def text(v):
    return "" if v is None else str(v).strip()


def norm_hla(v):
    out = []
    for allele in re.split(r"[,;]", text(v)):
        x = re.sub(r"[^A-Z0-9]", "", allele.upper().replace("HLA", ""))
        m = re.fullmatch(r"([ABC])(\d{2})(\d{2})", x)
        if not m:
            raise ValueError(f"unsupported HLA {allele!r}")
        out.append(f"HLA-{m.group(1)}*{m.group(2)}:{m.group(3)}")
    return ";".join(out)


def rows(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("RCC member checksum mismatch")
    z = zipfile.ZipFile(path)
    ss = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", NS):
        ss.append("".join(t.text or "" for t in si.findall(".//m:t", NS)))
    root = ET.fromstring(z.read("xl/worksheets/sheet2.xml"))
    table = []
    for ri, row in enumerate(root.findall(".//m:row", NS)):
        vals = []
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            val = "" if v is None else v.text
            if c.get("t") == "s" and val:
                val = ss[int(val)]
            vals.append(val)
        if ri == 0:
            headers = vals
            continue
        d = dict(zip(headers, vals))
        pep = text(d["Short_Epitope"]).upper()
        if pep.startswith("N/A") or text(d["HLA_of_best_short_epitope"]).upper() == "N/A":
            continue
        hla = norm_hla(d["HLA_of_best_short_epitope"])
        if not pep or set(pep) - AA or not 8 <= len(pep) <= 11:
            raise ValueError(f"row {ri}: invalid peptide")
        stim = [text(d[f"InVitro_PeptideStim_Replicate0{i}"]) for i in range(1, 4)]
        nostim = [text(d[f"InVitro_NoStim_Replicate0{i}"]) for i in range(1, 4)]
        if any(not x for x in stim + nostim):
            raise ValueError(f"row {ri}: incomplete assay")
        p = float(text(d["Ttest_pvalue_InVitroStim"]))
        record = f"rcc-vaccine-{hashlib.sha256((text(d['Patient_ID']) + '|' + text(d['Peptide_ID']) + '|' + pep + '|' + hla).encode()).hexdigest()[:16]}"
        table.append(
            {
                "record_id": record,
                "patient_id": "RCC-" + text(d["Patient_ID"]),
                "study_id": "RCC_PCV_VACCINE_2025",
                "hla": hla,
                "mhc_class": "I",
                "peptide": pep,
                "peptide_length": str(len(pep)),
                "immunogenicity": str(int(p < 0.05)),
                "label": str(int(p < 0.05)),
                "assay_type": "post_vaccine_invitro_IFNG_ELISPOT",
                "clinical_context": "personalized_RCC_peptide_vaccine",
                "source_doi": "10.1038/s41586-024-08507-5",
                "source_url": "https://doi.org/10.1038/s41586-024-08507-5",
                "source_checksum": EXPECTED,
                "source_row": str(ri + 1),
                "source_pvalue": text(d["Ttest_pvalue_InVitroStim"]),
                "evidence_level": "individual_peptide_stimulation_with_matched_no_stimulation_control",
            }
        )
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    a = ap.parse_args()
    data = rows(a.input)
    assert len(data) == 129 and len({r["patient_id"] for r in data}) == 9
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.summary.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(data)
    summary = {
        "rows": len(data),
        "patients": len({r["patient_id"] for r in data}),
        "positives": sum(int(r["label"]) for r in data),
        "negatives": sum(not int(r["label"]) for r in data),
        "member_sha256": EXPECTED,
        "endpoint": "post-vaccine individual-peptide IFNG ELISpot",
        "hla_semantics": "predicted best short-epitope binding allele",
    }
    a.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
