#!/usr/bin/env python3
"""Strict peptide-HLA adapter for the pinned MHCnuggets BA models.

MHCnuggets emits IC50 in nM; lower is better. Unsupported alleles are not
silently rescued to the closest allele.
"""
from __future__ import annotations
import argparse, csv, re, subprocess, tempfile
from pathlib import Path

VERSION = "2.4.0@b666fea3"
FIELDS = ["record_id", "predictor", "predictor_version", "task", "score", "score_direction", "status", "raw_score", "provenance_path"]

def allele(value: str) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", value.upper().replace("HLA-", "").replace("HLA", ""))
    m = re.fullmatch(r"([ABC])([0-9]{2})([0-9]{2})", compact)
    return f"HLA-{m.group(1)}{m.group(2)}:{m.group(3)}" if m else ""

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--input", type=Path, required=True); ap.add_argument("--source-dir", type=Path, default=Path("predictors/mhcnuggets/source")); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    source = args.source_dir.resolve(); observed = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if observed != "b666fea3a54a1d357efba4ea4d8550ce5dd50aba": raise RuntimeError(f"unexpected revision {observed}")
    rows = list(csv.DictReader(args.input.open(newline="", encoding="utf-8"))); required = {"record_id", "peptide", "hla"}
    if not rows or required - set(rows[0]): raise ValueError(f"missing columns: {sorted(required-set(rows[0]))}")
    out = {r["record_id"]: {"record_id": r["record_id"], "predictor": "MHCnuggets", "predictor_version": VERSION, "task": "binding", "score": "", "score_direction": "lower", "status": "unsupported_hla", "raw_score": "", "provenance_path": str(source)} for r in rows}
    groups = {}
    for r in rows:
        h = allele(r["hla"]); model = source / "mhcnuggets" / "saves" / "production" / f"{h}_BA.h5"
        if h and model.exists(): groups.setdefault(h, []).append(r)
    with tempfile.TemporaryDirectory() as td:
        for h, group in groups.items():
            pep = Path(td) / f"{h.replace(':','_')}.peps"; pred = Path(td) / f"{h.replace(':','_')}.csv"; pep.write_text("\n".join(r["peptide"] for r in group) + "\n", encoding="utf-8")
            from mhcnuggets.src.predict import predict
            predict(class_="I", peptides_path=str(pep), mhc=h, ba_models=True, output=str(pred))
            with pred.open(newline="", encoding="utf-8") as handle:
                for r, p in zip(group, csv.DictReader(handle), strict=True): out[r["record_id"]].update(score=p["ic50"], raw_score=p["ic50"], status="predicted")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle: w = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); w.writeheader(); w.writerows(out.values())
    print(f"MHCnuggets {VERSION}: {sum(r['status']=='predicted' for r in out.values())}/{len(out)} predicted -> {args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
