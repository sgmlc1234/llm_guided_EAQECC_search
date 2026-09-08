"""The exact evaluator, on things whose answer is known independently."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "alphaevolve_eaqecc"))
sys.path.insert(0, str(ROOT / "scripts" / "families"))

import helpers_eaqecc as H2  # noqa: E402
from helpers_eaqecc_fq import Fq, evaluate_L  # noqa: E402
import verify_family  # noqa: E402


def test_numpy_floor():
    assert hasattr(np, "bitwise_count"), "NumPy >= 2.0 is required"


@pytest.mark.parametrize("n", [5, 6, 7, 8, 9, 11])
def test_closed_form_family_q2(n):
    """[[n,1,n-1;n-3]]: build L from the closed form, take S = L^perp, and
    let the S-side evaluator recover k=1, c=n-3, d=n-1."""
    L = list(verify_family.family_generators(n))
    S = H2.nullspace([H2._J(v, n) for v in L], 2 * n)
    r = H2.evaluate(n, S, n - 1)
    assert (r["k"], r["c"], r["d"], r["offending"]) == (1, n - 3, n - 1, 0)


def test_first_archived_witness_per_q():
    for q in (2, 3, 4, 5):
        f = sorted((ROOT / "artifacts" / "witnesses" / f"q{q}").glob("*.json"))[0]
        s = json.loads(f.read_text())
        t = s["target"]
        if q == 2:
            r = H2.evaluate(t["n"], s["generators"], t["d"])
        else:
            r = evaluate_L(Fq(q), t["n"], s["L_basis"], t["d"])
        assert (r["k"], r["c"], r["d"], r["offending"]) == (t["k"], t["c"], t["d"], 0), f


def test_evaluator_is_sensitive_to_one_pauli():
    f = sorted((ROOT / "artifacts" / "witnesses" / "q2").glob("*.json"))[0]
    s = json.loads(f.read_text())
    t = s["target"]
    gens = list(s["generators"])
    gens[0] ^= 0b11
    r = H2.evaluate(t["n"], gens, t["d"])
    assert not (r.get("k") == t["k"] and r.get("c") == t["c"]
                and r.get("d") == t["d"] and r.get("offending") == 0)


def test_signature_arithmetic():
    """k = n - s + c and radical dimension s - 2c, on a random stabilizer set."""
    rng = np.random.default_rng(0)
    n, s = 8, 9
    gens = H2.random_stabilizer(n, s, rng)
    r = H2.evaluate(n, gens, 3)
    assert r["s"] == s and r["k"] == n - s + r["c"] and r["iso"] == s - 2 * r["c"]
