#!/usr/bin/env python3
r"""Generalized normal-form SAT sweep over open EAQECC table gaps.

For a target [[n,k,d;c]] (j = n-k-c radical generators), search for
L = S^perp of dim 2k+j in F_2^(2n) with basis in symplectic normal form
  rho_1..rho_j (radical), u_1,v_1,...,u_k,v_k (hyperbolic pairs)
— constant Gram constraints force rank exactly 2k and independence of the
pair part; rho independence is forced by lex-nonzero constraints on a
triangular support pattern. All 2^(2k+j) - 2^j non-radical combinations
must have symplectic weight >= d (Gray-code chaining + Sinz counters).

WLOG (sound under local symplectic x qubit permutation): rho_1 is a
Z-only string supported on a prefix (only applied when j >= 1).
Note for j >= 2 no canonical form is imposed on rho_2.. (search is then
merely redundant, never incomplete).

SAT -> witness, independently re-verified with the campaign evaluator.
UNSAT -> a decision; with --proof also a DRAT certificate that any
conforming checker can replay, which is what turns a decision into a
refutation the reader need not take on trust.

Usage:
    sat_normal_form_q2.py --only 7,1,3,6 --proof --out artifacts/refutations
    sat_normal_form_q2.py [--timeout 120] [--max-dim 11] [--nmax 14]   # sweep
Exit status for --only: 20 UNSAT, 10 SAT, 1 otherwise (CaDiCaL convention).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "alphaevolve_eaqecc"))

import helpers_eaqecc as H  # noqa: E402

from solver import run_solver  # noqa: E402


class CNFBuilder:
    def __init__(self) -> None:
        self.counter = 0
        self.clauses = []

    def new_var(self) -> int:
        self.counter += 1
        return self.counter

    def add(self, clause) -> None:
        self.clauses.append(clause)

    def and_var(self, a: int, b: int) -> int:
        out = self.new_var()
        self.add([-out, a])
        self.add([-out, b])
        self.add([out, -a, -b])
        return out



def require_xor(b, lits, const):
    acc = lits[0]
    for lit in lits[1:]:
        out = b.new_var()
        b.add([-out, acc, lit]); b.add([-out, -acc, -lit])
        b.add([out, -acc, lit]); b.add([out, acc, -lit])
        acc = out
    b.add([acc] if const else [-acc])


def xor2(b, a, c):
    out = b.new_var()
    b.add([-out, a, c]); b.add([-out, -a, -c])
    b.add([out, -a, c]); b.add([out, a, -c])
    return out


def or2(b, a, c):
    out = b.new_var()
    b.add([-out, a, c]); b.add([out, -a]); b.add([out, -c])
    return out


def at_most_k(b, lits, k):
    n = len(lits)
    if k >= n:
        return
    if k < 0:
        b.add([])
        return
    if k == 0:
        for lit in lits:
            b.add([-lit])
        return
    s = [[b.new_var() for _ in range(k)] for _ in range(n)]
    b.add([-lits[0], s[0][0]])
    for j in range(1, k):
        b.add([-s[0][j]])
    for i in range(1, n):
        b.add([-lits[i], s[i][0]])
        b.add([-s[i - 1][0], s[i][0]])
        for j in range(1, k):
            b.add([-lits[i], -s[i - 1][j - 1], s[i][j]])
            b.add([-s[i - 1][j], s[i][j]])
        b.add([-lits[i], -s[i - 1][k - 1]])


def gray_sequence(nbits):
    seq, prev = [], 0
    for i in range(1, 1 << nbits):
        g = i ^ (i >> 1)
        seq.append((g, (g ^ prev).bit_length() - 1))
        prev = g
    return seq


def build(n, k, c, d):
    j = n - k - c
    dim = 2 * k + j
    nbits = 2 * n
    b = CNFBuilder()
    basis = [[b.new_var() for _ in range(nbits)] for _ in range(dim)]
    rads = basis[:j]
    pairs = basis[j:]

    # WLOG rho_1 = Z-prefix (j >= 1)
    if j >= 1:
        r = rads[0]
        for q in range(n):
            b.add([-r[2 * q]])
        for q in range(n - 1):
            b.add([r[2 * q + 1], -r[2 * (q + 1) + 1]])
        b.add([r[1]])
    else:
        # WLOG (j == 0): u_1 = Z-prefix of weight >= d — any non-radical
        # element extends to a hyperbolic basis, and local symplectic ops
        # plus qubit permutations map it to Z^w with prefix support.
        u1 = pairs[0]
        for q in range(n):
            b.add([-u1[2 * q]])
        for q in range(n - 1):
            b.add([u1[2 * q + 1], -u1[2 * (q + 1) + 1]])
        for q in range(d):
            b.add([u1[2 * q + 1]])
    # rho_2..rho_j: independence <=> rho_i differs from every element of
    # span(rho_1..rho_{i-1}) (including 0). Enforce with explicit
    # difference clauses against each subset XOR.
    for i in range(1, j):
        ri = rads[i]
        b.add([lit for lit in ri])  # nonzero
        for m in range(1, 1 << i):
            sel = [rads[t2] for t2 in range(i) if (m >> t2) & 1]
            diff = []
            for t in range(nbits):
                x = sel[0][t]
                for row in sel[1:]:
                    x = xor2(b, x, row[t])
                diff.append(xor2(b, x, ri[t]))
            b.add(diff)  # rho_i != XOR(subset)

    def sform_lits(x, y):
        terms = []
        for q in range(n):
            terms.append(b.and_var(x[2 * q], y[2 * q + 1]))
            terms.append(b.and_var(x[2 * q + 1], y[2 * q]))
        return terms

    for i in range(dim):
        for i2 in range(i + 1, dim):
            # hyperbolic pairing inside `pairs`: (0,1), (2,3), ...
            want = 0
            if i >= j and i2 == i + 1 and (i - j) % 2 == 0:
                want = 1
            require_xor(b, sform_lits(basis[i], basis[i2]), want)

    combo_bits = {1 << i: basis[i] for i in range(dim)}
    prev_bits = None
    for code, flip in gray_sequence(dim):
        if code in combo_bits:
            bits = combo_bits[code]
        else:
            bits = [xor2(b, prev_bits[t], basis[flip][t])
                    for t in range(nbits)]
            combo_bits[code] = bits
        prev_bits = bits

    rad_codes = set()
    for m in range(1 << j):
        rad_codes.add(m)  # radical combos occupy the low j indices
    for code, bits in combo_bits.items():
        if code in rad_codes:
            continue
        acted = [or2(b, bits[2 * q], bits[2 * q + 1]) for q in range(n)]
        at_most_k(b, [-x for x in acted], n - d)
    return b, basis


def write_cnf(b, path: Path) -> None:
    with path.open("w") as f:
        f.write(f"p cnf {b.counter} {len(b.clauses)}\n")
        for cl in b.clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")


def solve_target(t, timeout, workdir, proof: Path | None = None):
    """Build the CNF for one target and decide it. With `proof`, ask the
    solver for a DRAT certificate so an UNSAT answer is checkable."""
    n, k, c, d = t["n"], t["k"], t["c"], t["d"]
    b, basis = build(n, k, c, d)
    cnf = workdir / f"ea_{n}_{k}_{c}_d{d}.cnf"
    write_cnf(b, cnf)
    t0 = time.time()
    try:
        proc = run_solver(cnf, proof=proof, timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "seconds": time.time() - t0}
    dt = time.time() - t0
    if rc == 20:
        return {"status": "UNSAT" if proof else "UNSAT_no_proof",
                "seconds": dt, "vars": b.counter, "clauses": len(b.clauses)}
    if rc != 10:
        return {"status": f"rc={rc}", "seconds": dt}
    model = set()
    for line in proc.stdout.splitlines():
        if line.startswith("v "):
            model.update(int(x) for x in line[2:].split() if x != "0")
    gens_L = []
    for row in basis:
        v = 0
        for t2, lit in enumerate(row):
            if lit in model:
                v |= 1 << t2
        gens_L.append(v)
    S = H.nullspace([H._J(v, n) for v in gens_L], 2 * n)
    r = H.evaluate(n, S, d)
    ok = ("error" not in r and r["k"] == k and r["c"] == c
          and r["d"] is not None and r["d"] >= d and r["offending"] == 0)
    return {"status": "SAT", "seconds": dt, "L_basis": gens_L,
            "S_generators": [int(g) for g in S],
            "verified": {kk: r.get(kk) for kk in
                         ("s", "c", "iso", "k", "d", "offending")},
            "verification_ok": bool(ok)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--max-dim", type=int, default=11)
    ap.add_argument("--nmax", type=int, default=14)
    ap.add_argument("--out", default=str(ROOT / "artifacts" / "sat_sweep"),
                    help="where results (and, with --keep, CNF/DRAT) go")
    ap.add_argument("--only", default=None,
                    help="single target 'n,k,c,d' (skips table scan)")
    ap.add_argument("--proof", action="store_true",
                    help="ask the solver for a DRAT proof (single target)")
    ap.add_argument("--snapshot", default=None,
                    help="dated snapshot to sweep (default: newest present)")
    args = ap.parse_args()

    if args.only:
        n, k, c, d = map(int, args.only.split(","))
        t = {"n": n, "k": k, "c": c, "d": d, "dl": d - 1,
             "j": n - k - c, "dim": 2 * k + (n - k - c)}
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        tag = f"q2_n{n}_k{k}_c{c}_d{d}"
        proof = (out / f"{tag}.drat") if args.proof else None
        res = solve_target(t, args.timeout, out, proof=proof)
        (out / f"ea_{n}_{k}_{c}_d{d}.cnf").replace(out / f"{tag}.cnf")
        key = f"[[{n},{k},{d};{c}]]"
        print(key, res["status"], f"{res['seconds']:.1f}s",
              res.get("verification_ok", ""))
        if res.get("status") == "SAT" and res.get("verification_ok"):
            sol = out / f"SOLUTION_n{n}_k{k}_c{c}_d{d}.json"
            sol.write_text(json.dumps(
                {"target": t, "generators": res["S_generators"],
                 "verified": res["verified"],
                 "provenance": "normal-form SAT"}))
            print("witness written", sol)
        (out / f"{tag}.json").write_text(json.dumps(
            {k2: v for k2, v in res.items() if k2 != "L_basis"}, default=int))
        sys.exit(20 if res["status"].startswith("UNSAT") else
                 10 if res["status"] == "SAT" else 1)

    snaps = sorted(d for d in (ROOT / "artifacts" / "codetables_snapshots").iterdir()
                   if d.is_dir() and (d / "qubit.json").exists())
    snap = (ROOT / "artifacts" / "codetables_snapshots" / args.snapshot
            if args.snapshot else snaps[-1])
    qubit = json.load(open(snap / "qubit.json"))
    harvest = ROOT / "artifacts" / "witnesses" / "q2"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    targets = []
    for e in qubit:
        if e["q"] != 2 or e["dl"] >= e["du"] or e["k"] < 1:
            continue
        n, kk, c = e["n"], e["k"], e["c"]
        j = n - kk - c
        if not (0 <= j <= 2) or n > args.nmax:
            continue
        if 2 * kk + j > args.max_dim:
            continue
        sol = harvest / f"SOLUTION_n{n}_k{kk}_c{c}_d{e['du']}.json"
        if sol.exists():
            continue
        targets.append({"n": n, "k": kk, "c": c, "d": e["du"],
                        "dl": e["dl"], "j": j, "dim": 2 * kk + j})
    targets.sort(key=lambda t: (t["dim"], t["n"]))
    print(f"{len(targets)} sweep targets (j<=2, dimL<={args.max_dim}, "
          f"n<={args.nmax})")

    results = {}
    closed = []
    with tempfile.TemporaryDirectory() as tmp:
        for t in targets:
            key = f"[[{t['n']},{t['k']},{t['d']};{t['c']}]]"
            res = solve_target(t, args.timeout, Path(tmp))
            results[key] = {**t, **{k2: v for k2, v in res.items()
                                    if k2 != "L_basis"}}
            line = f"{key:>18} j={t['j']} dimL={t['dim']}: {res['status']}" \
                   f" ({res['seconds']:.1f}s)"
            if res["status"] == "SAT":
                line += f" verified_ok={res['verification_ok']}"
                if res["verification_ok"]:
                    closed.append(key)
                    sol = harvest / (f"SOLUTION_n{t['n']}_k{t['k']}_"
                                     f"c{t['c']}_d{t['d']}.json")
                    sol.write_text(json.dumps(
                        {"target": t,
                         "generators": res["S_generators"],
                         "verified": res["verified"],
                         "provenance": "normal-form SAT sweep"}))
            print(line, flush=True)
    (out / "sweep_results.json").write_text(json.dumps(results, indent=1))
    print(f"\nCLOSED {len(closed)} new entries: {closed}")


if __name__ == "__main__":
    main()
