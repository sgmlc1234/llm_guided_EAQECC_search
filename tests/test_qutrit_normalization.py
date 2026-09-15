"""Check the normalized encoding against its archived CNF and a known code."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENCODER = ROOT / "scripts/refutations/sat_free_radical_q3.py"


def generate(tmp_path, n, c, d, normalize=True):
    fake = tmp_path / "generation_only_solver"
    fake.write_text("#!/bin/sh\nexit 20\n")
    fake.chmod(0o755)
    command = [sys.executable, str(ENCODER), str(n), str(c), str(d), "--out", str(tmp_path)]
    if normalize:
        command.append("--coordinate-normalize")
    result = subprocess.run(command, env=dict(os.environ, CADICAL_PATH=str(fake)),
                            capture_output=True, text=True, timeout=30)
    return result, tmp_path / f"q3_n{n}_k1_c{c}_d{d}.cnf"


def test_normalized_cnf_reproduces_certificate_input(tmp_path):
    result, cnf = generate(tmp_path, 10, 4, 9)
    assert result.returncode == 20, result.stdout + result.stderr
    archived = ROOT / "artifacts/refutations/q3_n10_k1_c4_d9.cnf"
    assert hashlib.sha256(cnf.read_bytes()).digest() == hashlib.sha256(archived.read_bytes()).digest()


def test_normalization_rejects_outside_lemma_scope(tmp_path):
    result, _ = generate(tmp_path, 5, 2, 4)  # radical dimension two
    assert result.returncode != 20
    assert "requires j>2" in result.stderr


def test_known_qutrit_witness_is_not_excluded(tmp_path):
    solver = os.environ.get("CADICAL_PATH") or shutil.which("cadical")
    if not solver:
        pytest.skip("known-witness CNF control needs a SAT solver")
    result, cnf = generate(tmp_path, 10, 5, 9)
    assert result.returncode == 20, result.stderr
    witness = json.loads((ROOT / "artifacts/witnesses/q3/SOLUTION3_n10_k1_c5_d9.json").read_text())
    # This archived witness already has an RREF Z-only radical in its first four rows.
    basis = witness["L_basis"]
    units = [1 + 3 * (20 * row + coordinate) + value
             for row, vector in enumerate(basis) for coordinate, value in enumerate(vector)]
    lines = cnf.read_text().splitlines()
    header = lines[0].split()
    header[3] = str(int(header[3]) + len(units))
    cnf.write_text(" ".join(header) + "\n" + "\n".join(lines[1:]) + "\n"
                   + "".join(f"{u} 0\n" for u in units))
    checked = subprocess.run([solver, "-q", str(cnf)], capture_output=True, text=True, timeout=30)
    assert checked.returncode == 10, checked.stdout + checked.stderr
