#!/usr/bin/env python3
"""Run PRIME 2.0 with MixMHCpred 2.2 in a space-free temporary stage."""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

VERSION = "2.0"
REVISION = "ec1aa020089d62e9193ad377ddda9c93eed7f5b1"
MIX_REVISION = "f64bb4548082768c70a1cfb5a4442d5e6ea04591"
FIELDS = [
    "record_id",
    "predictor",
    "predictor_version",
    "task",
    "score",
    "score_direction",
    "status",
    "prime_percent_rank",
    "mixmhcpred_percent_rank",
    "allele",
]


def simple_hla(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper()).removeprefix("HLA")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scalar(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return "" if not math.isfinite(number) else f"{number:.12g}"


def verify_revision(directory: Path, expected: str, name: str) -> None:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != expected:
        raise RuntimeError(f"expected {name} {expected}, found {revision}")


def stage_sources(source_dir: Path, mix_dir: Path, work: Path) -> tuple[Path, Path, Path]:
    prime_stage = work / "prime"
    mix_stage = work / "mix"
    shutil.copytree(source_dir, prime_stage, ignore=shutil.ignore_patterns(".git"))
    shutil.copytree(mix_dir, mix_stage, ignore=shutil.ignore_patterns(".git"))
    prime_wrapper = prime_stage / "PRIME"
    mix_wrapper = mix_stage / "MixMHCpred"
    prime_wrapper.write_text(
        prime_wrapper.read_text().replace("/PATH_TO_PRIME/lib", str(prime_stage / "lib"))
    )
    mix_wrapper.write_text(
        mix_wrapper.read_text().replace("/PATH_TO_MIXMHCPRED/lib", str(mix_stage / "lib"))
    )
    prime_wrapper.chmod(0o755)
    mix_wrapper.chmod(0o755)
    return prime_wrapper, mix_wrapper, prime_stage


def run_prime(
    prime_wrapper: Path,
    mix_wrapper: Path,
    input_path: Path,
    output_path: Path,
    alleles: list[str],
    cwd: Path,
) -> None:
    environment = os.environ.copy()
    # macOS Perl rejects the inherited C.UTF-8 locale used by some Python
    # runtimes. The upstream wrappers rely on Perl even for path resolution.
    environment.update({"LC_ALL": "C", "LANG": "C"})
    subprocess.run(
        [
            str(prime_wrapper),
            "-i",
            str(input_path),
            "-o",
            str(output_path),
            "-a",
            ",".join(alleles),
            "-mix",
            str(mix_wrapper),
        ],
        cwd=cwd,
        env=environment,
        check=True,
        text=True,
    )


def parse_prime(path: Path) -> list[dict[str, str]]:
    lines = [line for line in path.read_text().splitlines() if line and not line.startswith("#")]
    if not lines or not lines[0].startswith("Peptide\t"):
        raise RuntimeError("PRIME output header not found")
    return list(csv.DictReader(lines, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/benchmark.csv"))
    parser.add_argument("--source-dir", type=Path, default=Path("predictors/prime/source"))
    parser.add_argument("--mix-dir", type=Path, default=Path("predictors/prime/vendor/mixmhcpred"))
    parser.add_argument(
        "--output", type=Path, default=Path("results/raw_predictions/prime-2.0.csv")
    )
    args = parser.parse_args()
    source_dir = args.source_dir.absolute()
    mix_dir = args.mix_dir.absolute()
    verify_revision(source_dir, REVISION, "PRIME")
    verify_revision(mix_dir, MIX_REVISION, "MixMHCpred")

    rows = read_csv(args.input)
    required = {"record_id", "peptide", "hla"}
    missing = required - set(rows[0] if rows else [])
    if missing:
        raise ValueError(f"missing input columns: {sorted(missing)}")
    mapping = {
        line.split()[0]
        for line in (source_dir / "lib/alleles_mapping.txt").read_text().splitlines()
        if line.strip()
    }
    eligible = [
        row for row in rows if simple_hla(row["hla"]) in mapping and 8 <= len(row["peptide"]) <= 14
    ]
    alleles = sorted({simple_hla(row["hla"]) for row in eligible})
    by_id: dict[str, dict[str, str]] = {}
    if eligible:
        with tempfile.TemporaryDirectory(prefix="neorepro-prime-") as temporary:
            work = Path(temporary)
            prime_wrapper, mix_wrapper, prime_stage = stage_sources(source_dir, mix_dir, work)
            peptide_file = work / "peptides.txt"
            peptide_file.write_text("\n".join(row["peptide"] for row in eligible) + "\n")
            output_file = work / "prime.tsv"
            run_prime(
                prime_wrapper,
                mix_wrapper,
                peptide_file,
                output_file,
                alleles,
                prime_stage,
            )
            predictions = parse_prime(output_file)
            if len(predictions) != len(eligible):
                raise RuntimeError("PRIME output row count differs from eligible input")
            for source, prediction in zip(eligible, predictions):
                if prediction["Peptide"] != source["peptide"]:
                    raise RuntimeError("PRIME changed input row order")
                allele = simple_hla(source["hla"])
                by_id[source["record_id"]] = {
                    "score": scalar(prediction[f"Score_{allele}"]),
                    "prime_rank": scalar(prediction[f"%Rank_{allele}"]),
                    "binding_rank": scalar(prediction[f"%RankBinding_{allele}"]),
                }

    output_rows = []
    for row in rows:
        allele = simple_hla(row["hla"])
        values = by_id.get(row["record_id"], {})
        if allele not in mapping:
            status = "unsupported_hla"
        elif not 8 <= len(row["peptide"]) <= 14:
            status = "unsupported_length"
        elif values.get("score"):
            status = "predicted"
        else:
            status = "invalid_output"
        output_rows.append(
            {
                "record_id": row["record_id"],
                "predictor": "PRIME",
                "predictor_version": VERSION,
                "task": "immunogenicity",
                "score": values.get("score", ""),
                "score_direction": "higher",
                "status": status,
                "prime_percent_rank": values.get("prime_rank", ""),
                "mixmhcpred_percent_rank": values.get("binding_rank", ""),
                "allele": allele,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    predicted = sum(row["status"] == "predicted" for row in output_rows)
    print(f"PRIME {VERSION}: {predicted}/{len(output_rows)} rows predicted -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
