#!/usr/bin/env python3
"""Idempotently set up pinned predictor sources, environments, models, and binaries."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

REVISIONS = {
    "bigmhc": "9d84a3b4da77c9253ac90ff8cb629274003b90fd",
    "prime": "ec1aa020089d62e9193ad377ddda9c93eed7f5b1",
    "mixmhcpred": "f64bb4548082768c70a1cfb5a4442d5e6ea04591",
}


def execute(command: list[str], root: Path, environment: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=root, env=environment, check=True)


def revision(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def clone_or_verify(root: Path, path: Path, url: str, tag: str, expected_revision: str) -> None:
    if path.exists():
        observed = revision(path)
        if observed != expected_revision:
            raise RuntimeError(f"{path} is {observed}, expected {expected_revision}")
        print(f"verified existing source {path} at {observed}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    execute(["git", "clone", "--branch", tag, "--depth", "1", url, str(path)], root)
    observed = revision(path)
    if observed != expected_revision:
        raise RuntimeError(f"cloned {path} at {observed}, expected {expected_revision}")


def setup_mhcflurry(root: Path, uv: str) -> None:
    environment_dir = root / "predictors/mhcflurry/.venv"
    if not environment_dir.exists():
        execute([uv, "venv", "--python", "3.11", str(environment_dir)], root)
    execute(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(environment_dir / "bin/python"),
            "mhcflurry==2.2.1",
        ],
        root,
    )
    models = root / "predictors/mhcflurry/vendor/2.2.0/models_class1_presentation/models"
    if models.exists():
        print(f"verified existing MHCflurry models at {models}")
        return
    environment = os.environ.copy()
    environment.update(
        {
            "MHCFLURRY_DATA_DIR": str(root / "predictors/mhcflurry/vendor"),
            "MHCFLURRY_DOWNLOADS_CURRENT_RELEASE": "2.2.0",
        }
    )
    execute(
        [
            str(environment_dir / "bin/mhcflurry-downloads"),
            "fetch",
            "models_class1_presentation",
            "--release",
            "2.2.0",
        ],
        root,
        environment,
    )


def setup_bigmhc(root: Path, uv: str) -> None:
    source = root / "predictors/bigmhc/source"
    clone_or_verify(
        root,
        source,
        "https://github.com/KarchinLab/bigmhc.git",
        "v1.0",
        REVISIONS["bigmhc"],
    )
    environment_dir = root / "predictors/bigmhc/.venv"
    if not environment_dir.exists():
        execute([uv, "venv", "--python", "3.9", str(environment_dir)], root)
    python = str(environment_dir / "bin/python")
    execute(
        [uv, "pip", "install", "--python", python, "torch==1.13.0", "pandas==1.4.4"],
        root,
    )
    execute(
        [
            uv,
            "pip",
            "install",
            "--python",
            python,
            "numpy==1.21.5",
            "scipy==1.7.3",
            "scikit-learn==1.0.2",
            "psutil==5.9.8",
        ],
        root,
    )


def setup_prime(root: Path) -> None:
    prime = root / "predictors/prime/source"
    mix = root / "predictors/prime/vendor/mixmhcpred"
    clone_or_verify(
        root,
        prime,
        "https://github.com/GfellerLab/PRIME.git",
        "v2.0",
        REVISIONS["prime"],
    )
    clone_or_verify(
        root,
        mix,
        "https://github.com/GfellerLab/MixMHCpred.git",
        "v2.2",
        REVISIONS["mixmhcpred"],
    )
    compiler = shutil.which("c++")
    if not compiler:
        raise RuntimeError("a C++ compiler is required for PRIME and MixMHCpred")
    binaries = [
        (prime / "lib/PRIME.cc", prime / "lib/PRIME.x"),
        (mix / "lib/MixMHCpred.cc", mix / "lib/MixMHCpred.x"),
    ]
    for source, output in binaries:
        if output.exists():
            print(f"verified existing binary {output}")
        else:
            execute([compiler, "-O3", str(source), "-o", str(output)], root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictors",
        nargs="+",
        choices=("mhcflurry", "bigmhc", "prime"),
        default=("mhcflurry", "bigmhc", "prime"),
    )
    parser.add_argument("--accept-academic-licenses", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("uv is required to create the pinned environments")
    restricted = {"bigmhc", "prime"} & set(args.predictors)
    if restricted and not args.accept_academic_licenses:
        raise SystemExit(
            "BigMHC, PRIME, and MixMHCpred have academic/non-commercial terms; "
            "review docs/licenses and pass --accept-academic-licenses to continue"
        )
    for predictor in args.predictors:
        if predictor == "mhcflurry":
            setup_mhcflurry(root, uv)
        elif predictor == "bigmhc":
            setup_bigmhc(root, uv)
        else:
            setup_prime(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
