"""Seed + evaluation budget fix the search output; wall clock does not enter."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "eaqecc_baselines"))
import run_baseline as RB  # noqa: E402


def _run(arm, seed, max_evals):
    campaign, harvest = RB.build_campaign_dir(RB.TARGET_SETS["residual"])
    try:
        out = campaign / "r.json"
        env = dict(os.environ, TIME_BUDGET_S="240", MAX_EVALS=str(max_evals),
                   EVAL_RNG_SEED=str(seed), HARVEST_DIR=str(harvest))
        subprocess.run([sys.executable, str(campaign / "driver_deterministic.py"),
                        str(RB.ARMS[arm]), str(out)], env=env, check=True,
                       capture_output=True, timeout=600)
        return json.loads(out.read_text())
    finally:
        shutil.rmtree(campaign, ignore_errors=True)


@pytest.mark.parametrize("arm", ["B0", "B2"])
def test_same_seed_same_proposals(arm):
    a, b = _run(arm, 20260814, 400), _run(arm, 20260814, 400)
    assert a["error"] is None, a["error"]
    assert a["candidates"] == b["candidates"]
    # the program checks its own clock between evaluations, so it may
    # overrun the budget by a step -- identically on every machine
    assert a["n_evals"] == b["n_evals"] >= 400


def test_different_seed_different_proposals():
    a, b = _run("B0", 1, 400), _run("B0", 2, 400)
    assert a["candidates"] != b["candidates"]


def test_stored_fingerprint_matches_repo_layout():
    fp = json.loads((ROOT / "scripts" / "eaqecc_baselines" / "search_fingerprint.json").read_text())
    assert set(fp["arms"]) == {"B0", "B1f", "B2"} and fp["max_evals"] == 5000
    assert len(fp["proposals"]) == 12
