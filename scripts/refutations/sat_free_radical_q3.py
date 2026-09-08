#!/usr/bin/env python3
"""FULL refutation SAT for qutrit targets [[n,1,d;c]]_3 with FREE radical.

Encodes L = <a, b, rho_1..rho_j> (j = n-1-c) where the rho rows are
UNKNOWN, constrained to reduced row echelon form (unique per subspace:
complete and duplicate-free over all radical candidates), totally
isotropic, and commuting with a, b; a,b hyperbolic. Every element of
L \\ rad must have weight >= d. UNSAT => no [[n,1,d;c]]_3 exists, full stop.

Encoding notes:
 - all F_3 digits one-hot;
 - RREF: pivot indicator P[i][col] (one-hot over 2n columns), strictly
   increasing pivots, leading 1, zeros left of pivot, pivot columns clear
   in other rows;
 - isotropy / commutation via mod-3 state chains with product tables;
 - radical shift-cells S[t][q] for all t in F_3^j defined incrementally
   along a Gray sequence over t-vectors (one rho-contribution per step);
 - class-cells C[cls][q] for cls in {a, b, a+b, a+2b};
 - non-acting literal E[cls][t][q] <=> C[cls][q] == -S[t][q];
   at-most-(n-d) of {E[cls][t][q]}_q for every (cls, t).

Usage: sat_free_radical_q3.py n c d [--timeout SEC] [--out DIR] [--proof]
Exit status: 20 UNSAT, 10 SAT (CaDiCaL convention).
"""

import itertools
import subprocess
import sys
import tempfile

import numpy as np

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from solver import run_solver  # noqa: E402
from helpers_eaqecc_f3 import evaluate_L  # noqa: E402

CLASSES = [(1, 0), (0, 1), (1, 1), (1, 2)]


class CNF:
    def __init__(self):
        self.n = 0
        self.cl = []

    def var(self):
        self.n += 1
        return self.n

    def add(self, c):
        self.cl.append(c)

    def one_hot(self, k=3):
        vs = [self.var() for _ in range(k)]
        self.add(vs)
        for i in range(k):
            for jj in range(i + 1, k):
                self.add([-vs[i], -vs[jj]])
        return vs


def gray_tvecs(j):
    """Reflected ternary Gray sequence over F_3^j: starts at 0, adjacent
    vectors differ in exactly one coordinate (by +-1)."""
    if j == 0:
        return [()]
    prev = gray_tvecs(j - 1)
    out = []
    for ci in range(3):
        block = prev if ci % 2 == 0 else prev[::-1]
        out += [(ci,) + v for v in block]
    assert len(out) == 3 ** j
    return out


def main():
    n, c, d = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    timeout = 0
    if "--timeout" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout") + 1])
    # --out DIR keeps the CNF (and, with --proof, a DRAT certificate) under
    # DIR/<tag>.cnf|.drat instead of a temporary file.
    out_dir = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    want_proof = "--proof" in sys.argv
    j = n - 1 - c
    N2 = 2 * n
    cnf = CNF()

    # ---- unknown digits ----
    R = [[cnf.one_hot() for _ in range(N2)] for _ in range(j)]  # rho rows
    A = [cnf.one_hot() for _ in range(N2)]
    B = [cnf.one_hot() for _ in range(N2)]

    # ---- RREF structure for R ----
    P = [[cnf.var() for _ in range(N2)] for _ in range(j)]  # pivot indicators
    for i in range(j):
        cnf.add(P[i])                          # each row has a pivot
        for u in range(N2):
            for v in range(u + 1, N2):
                cnf.add([-P[i][u], -P[i][v]])  # at most one
    for i in range(j - 1):                     # strictly increasing pivots
        for u in range(N2):
            for v in range(u + 1):
                cnf.add([-P[i][u], -P[i + 1][v]])
    for i in range(j):
        for col in range(N2):
            cnf.add([-P[i][col], R[i][col][1]])          # leading entry = 1
            for left in range(col):
                cnf.add([-P[i][col], R[i][left][0]])     # zeros before pivot
            for i2 in range(j):
                if i2 != i:
                    cnf.add([-P[i][col], R[i2][col][0]])  # pivot col clear

    # ---- helper: mod-3 chain for sum of symplectic products <U, V> ----
    def sympl_chain(U, V, want_zero):
        st = cnf.one_hot()
        cnf.add([st[0]])
        for q in range(n):
            new = cnf.one_hot()
            for s in range(3):
                for xu, zu, xv, zv in itertools.product(range(3), repeat=4):
                    t = (xu * zv - zu * xv) % 3
                    cnf.add([-st[s], -U[2 * q][xu], -U[2 * q + 1][zu],
                             -V[2 * q][xv], -V[2 * q + 1][zv],
                             new[(s + t) % 3]])
            st = new
        if want_zero is True:
            cnf.add([st[0]])
        elif want_zero is False:
            cnf.add([-st[0]])

    # isotropy among rhos; commutation of a,b with rhos; hyperbolic a,b
    for i in range(j):
        for i2 in range(i + 1, j):
            sympl_chain(R[i], R[i2], True)
        sympl_chain(A, R[i], True)
        sympl_chain(B, R[i], True)
    sympl_chain(A, B, False)

    # ---- class-cells C[cls][q]: one-hot 9 = 3x+z of (alpha a + beta b) ----
    C = []
    for (al, be) in CLASSES:
        row = []
        for q in range(n):
            cell = cnf.one_hot(9)
            for ax, az, bx, bz in itertools.product(range(3), repeat=4):
                x = (al * ax + be * bx) % 3
                z = (al * az + be * bz) % 3
                cnf.add([-A[2 * q][ax], -A[2 * q + 1][az],
                         -B[2 * q][bx], -B[2 * q + 1][bz],
                         cell[3 * x + z]])
            row.append(cell)
        C.append(row)

    # ---- shift-cells S[t][q] along Gray sequence ----
    tvecs = gray_tvecs(j)
    S = {tvecs[0]: None}  # zero shift: cell (0,0) constant
    prev = tvecs[0]
    Smap = {prev: [None] * n}
    for tv in tvecs[1:]:
        diff = [i for i in range(j) if tv[i] != prev[i]]
        assert len(diff) == 1, (prev, tv)
        i = diff[0]
        delta = (tv[i] - prev[i]) % 3
        row = []
        for q in range(n):
            cell = cnf.one_hot(9)
            pc = Smap[prev][q]
            for rx, rz in itertools.product(range(3), repeat=2):
                dx, dz = (delta * rx) % 3, (delta * rz) % 3
                if pc is None:
                    cnf.add([-R[i][2 * q][rx], -R[i][2 * q + 1][rz],
                             cell[3 * dx + dz]])
                else:
                    for px, pz in itertools.product(range(3), repeat=2):
                        cnf.add([-pc[3 * px + pz],
                                 -R[i][2 * q][rx], -R[i][2 * q + 1][rz],
                                 cell[3 * ((px + dx) % 3) + (pz + dz) % 3]])
            row.append(cell)
        Smap[tv] = row
        prev = tv

    # ---- non-acting literals + at-most-(n-d) ----
    slack = n - d
    assert slack == 1, "encoded for d = n-1"
    for ci in range(len(CLASSES)):
        for tv in tvecs:
            lits = []
            for q in range(n):
                sc = Smap[tv][q]
                if sc is None:
                    lits.append(C[ci][q][0])  # cell == (0,0)
                else:
                    e = cnf.var()
                    for v in range(9):
                        x, z = divmod(v, 3)
                        nv = 3 * ((-x) % 3) + ((-z) % 3)
                        cnf.add([-e, -C[ci][q][v], sc[nv] * 0 + sc[nv]]
                                if False else
                                [-C[ci][q][v], -sc[nv], e])
                    lits.append(e)
            for u in range(len(lits)):
                for v in range(u + 1, len(lits)):
                    cnf.add([-lits[u], -lits[v]])

    tag = f"q3_n{n}_k1_c{c}_d{d}"
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = str(out_dir / f"{tag}.cnf")
        proof = out_dir / f"{tag}.drat" if want_proof else None
    else:
        path = tempfile.NamedTemporaryFile('w', suffix='.cnf', delete=False).name
        proof = None
    with open(path, 'w') as f:
        f.write(f"p cnf {cnf.n} {len(cnf.cl)}\n")
        for cc in cnf.cl:
            f.write(" ".join(map(str, cc)) + " 0\n")
    print(f"CNF: {cnf.n} vars, {len(cnf.cl)} clauses -> {path}", flush=True)
    try:
        p = run_solver(Path(path), proof=proof, timeout=timeout or None)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        sys.exit(1)
    if p.returncode == 20:
        print(f"UNSAT: no [[{n},1,{d};{c}]]_3 EAQECC exists (free radical, "
              f"complete search space)")
        sys.exit(20)
    assert p.returncode == 10, (p.returncode, p.stderr[-300:])
    model = set()
    for line in p.stdout.splitlines():
        if line.startswith("v "):
            model.update(int(x) for x in line[2:].split() if x != "0")

    def dec(row):
        return np.array([next(v for v in range(3) if row[t][v] in model)
                         for t in range(N2)])

    L = [dec(R[i]) for i in range(j)] + [dec(A), dec(B)]
    r = evaluate_L(n, L, d)
    print("SAT; independent evaluator check:", r)
    sys.exit(10)


if __name__ == "__main__":
    main()
