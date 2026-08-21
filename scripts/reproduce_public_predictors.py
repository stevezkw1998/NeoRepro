#!/usr/bin/env python3
"""Cheap, auditable first-pass reproduction sweep for public predictors.

This deliberately stops at installation/import/CLI smoke tests. It never
silently converts an end-to-end workflow into a peptide-HLA benchmark model.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import time
from pathlib import Path

CANDIDATES = {
    "mhcnuggets": "https://github.com/KarchinLab/mhcnuggets.git",
    "neoguider": "https://github.com/XuegongLab/neoguider.git",
    "neofox": "https://github.com/TRON-Bioinformatics/neofox.git",
    "pvactools": "https://github.com/griffithlab/pVACtools.git",
    "seq2neo": "https://github.com/XSLiuLab/Seq2Neo.git",
    "vaxrank": "https://github.com/openvax/vaxrank.git",
    "mhcmatch": "https://github.com/antigenomics/mhcmatch.git",
}
IMPORTS = {"mhcnuggets": "mhcnuggets", "neofox": "neofox", "vaxrank": "vaxrank"}
CLI = {"pvactools": "pvacseq", "vaxrank": "vaxrank"}


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 180):
    t = time.monotonic()
    try:
        p = subprocess.run(
            cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
        )
        return p.returncode, p.stdout, p.stderr, time.monotonic() - t
    except subprocess.TimeoutExpired as e:
        return (
            124,
            e.stdout or "",
            (e.stderr or "") + f"\nTimed out after {timeout}s",
            time.monotonic() - t,
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=sorted(CANDIDATES), default=sorted(CANDIDATES))
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    uv = shutil.which("uv")
    rows = []
    for name in args.only:
        base = root / "predictors" / name
        source = base / "source"
        attempts = base / "attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        if not source.exists():
            rc, out, err, _sec = run(
                ["git", "clone", "--filter=blob:none", CANDIDATES[name], str(source)], root, 300
            )
            (attempts / "clone.stdout.log").write_text(out)
            (attempts / "clone.stderr.log").write_text(err)
        rc, rev, err, _sec = run(["git", "rev-parse", "HEAD"], source)
        revision = rev.strip() if rc == 0 else "unknown"
        license_files = sorted(
            str(p.relative_to(source))
            for p in source.rglob("*")
            if p.is_file()
            and ("license" in p.name.lower() or p.name.lower() in {"copying", "notice"})
        )[:20]
        env = base / ".venv"
        install_rc = 125
        install_out = install_err = "not attempted"
        if uv and source.exists():
            if not env.exists():
                run([uv, "venv", "--python", "3.11", str(env)], root, 180)
            py = str(env / "bin/python")
            install_rc, install_out, install_err, _ = run(
                [uv, "pip", "install", "--python", py, "-e", str(source)], root, 900
            )
        (attempts / "install.stdout.log").write_text(install_out or "")
        (attempts / "install.stderr.log").write_text(install_err or "")
        smoke_rc = 125
        smoke_out = smoke_err = "not attempted"
        if install_rc == 0 and name in IMPORTS:
            smoke_rc, smoke_out, smoke_err, _ = run(
                [str(env / "bin/python"), "-c", f"import {IMPORTS[name]}; print('import ok')"],
                root,
                180,
            )
        elif install_rc == 0 and name in CLI:
            smoke_rc, smoke_out, smoke_err, _ = run(
                [str(env / ("bin/" + CLI[name])), "--help"], root, 180
            )
        (attempts / "smoke.stdout.log").write_text(smoke_out or "")
        (attempts / "smoke.stderr.log").write_text(smoke_err or "")
        receipt = {
            "predictor": name,
            "revision": revision,
            "repo": CANDIDATES[name],
            "install_returncode": install_rc,
            "smoke_returncode": smoke_rc,
            "license_files": license_files,
            "platform": platform.platform(),
            "benchmark_track": "profile_only",
        }
        (attempts / "sweep_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        rows.append((name, revision, install_rc, smoke_rc, ";".join(license_files)))
    print("predictor\trevision\tinstall_rc\tsmoke_rc\tlicense_files")
    for row in rows:
        print("\t".join(map(str, row)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
