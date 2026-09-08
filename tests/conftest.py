"""Fixtures: a private copy of the archive that a test may corrupt.

The auditor reads data from --root and code from its own directory, so a
test copies artifacts/ + MANIFEST.sha256 into a temporary root, damages it
in one specific way, and asserts the auditor notices. These are the
negative controls: an auditor that only ever says PASS proves nothing.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "reproduce_eaqecc.py"


@pytest.fixture
def archive(tmp_path):
    root = tmp_path / "root"
    shutil.copytree(ROOT / "artifacts", root / "artifacts",
                    ignore=shutil.ignore_patterns("reproduce_eaqecc", ".DS_Store"))
    shutil.copy(ROOT / "MANIFEST.sha256", root / "MANIFEST.sha256")
    return root


def run_auditor(root, *args, env=None):
    """Run the auditor against `root`; return (exit code, parsed report)."""
    out = root / "report"
    proc = subprocess.run(
        [sys.executable, str(AUDITOR), "--root", str(root), "--out", str(out), *args],
        capture_output=True, text=True, env=env, timeout=1800)
    rep = out / "reproduction_report.json"
    report = json.loads(rep.read_text()) if rep.exists() else {"claims": {}}
    return proc.returncode, report, proc.stdout + proc.stderr


@pytest.fixture
def auditor():
    return run_auditor
