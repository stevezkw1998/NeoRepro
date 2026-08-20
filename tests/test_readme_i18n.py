from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_localized_readmes_are_current_and_structurally_safe() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/readme_i18n.py", "check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
