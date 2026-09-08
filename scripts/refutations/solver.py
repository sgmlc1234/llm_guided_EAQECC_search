"""Locate and run a SAT solver. Shared by the three encoders.

Order: $CADICAL_PATH, then `cadical` on PATH. Nothing is compiled in, so a
reader whose solver lives elsewhere sets one variable. CaDiCaL's exit
convention is kept throughout the refutation scripts: 20 UNSAT, 10 SAT.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_solver() -> Path:
    env = os.environ.get("CADICAL_PATH")
    if env and Path(env).exists():
        return Path(env)
    w = shutil.which("cadical")
    if w:
        return Path(w)
    sys.exit("no SAT solver: set CADICAL_PATH or put `cadical` on PATH "
             "(https://github.com/arminbiere/cadical)")


def run_solver(cnf: Path, proof: Path | None = None,
               timeout: float | None = None) -> subprocess.CompletedProcess:
    """Decide `cnf`; with `proof`, write a text DRAT certificate there."""
    cmd = [str(find_solver()), "-q"]
    if proof is not None:
        cmd += ["--no-binary", str(cnf), str(proof)]
    else:
        cmd += [str(cnf)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def solver_version() -> str:
    try:
        return subprocess.run([str(find_solver()), "--version"],
                              capture_output=True, text=True, timeout=30
                              ).stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        return "unknown"
