#!/usr/bin/env python3
"""FULL-refutation SAT for [[n,1,d;c]]_q, prime q, FREE radical (RREF).

Generalizes sat_qutrit_free_radical.py to any prime q with a leaner
shift encoding: per shift vector t (Gray-ordered over F_q^j) and qudit,
the x- and z-shift digits are chained SEPARATELY (5-state tables), and
class-cells likewise split into digits. slack = n-d must be 1.

Usage: sat_free_radical_fq.py q n c d [--timeout SEC] [--out DIR] [--proof]
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
from helpers_eaqecc_fq import Fq, evaluate_L  # noqa: E402


class CNF:
    def __init__(self):
        self.n = 0
        self.cl = []

    def var(self):
        self.n += 1
        return self.n

    def add(self, c):
        self.cl.append(c)

    def one_hot(self, k):
        vs = [self.var() for _ in range(k)]
        self.add(vs)
        for i in range(k):
            for jj in range(i + 1, k):
                self.add([-vs[i], -vs[jj]])
        return vs


def gray_vecs(q, j):
    if j == 0:
        return [()]
    prev = gray_vecs(q, j - 1)
    out = []
    for ci in range(q):
        block = prev if ci % 2 == 0 else prev[::-1]
        out += [(ci,) + v for v in block]
    return out


def main():
    q, n, c, d = (int(x) for x in sys.argv[1:5])
    timeout = 0
    if "--timeout" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout") + 1])
    # --out DIR keeps the CNF (and, with --proof, a DRAT certificate) under
    # DIR/<tag>.cnf|.drat instead of a temporary file.
    out_dir = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    want_proof = "--proof" in sys.argv
    F = Fq(q)
    j = n - 1 - c
    N2 = 2 * n
    slack = n - d
    assert slack in (1, 2), "slack must be 1 or 2"
    cnf = CNF()

    R = [[cnf.one_hot(q) for _ in range(N2)] for _ in range(j)]
    A = [cnf.one_hot(q) for _ in range(N2)]
    B = [cnf.one_hot(q) for _ in range(N2)]

    # RREF for R
    P = [[cnf.var() for _ in range(N2)] for _ in range(j)]
    for i in range(j):
        cnf.add(P[i])
        for u in range(N2):
            for v in range(u + 1, N2):
                cnf.add([-P[i][u], -P[i][v]])
    for i in range(j - 1):
        for u in range(N2):
            for v in range(u + 1):
                cnf.add([-P[i][u], -P[i + 1][v]])
    for i in range(j):
        for col in range(N2):
            cnf.add([-P[i][col], R[i][col][1]])
            for left in range(col):
                cnf.add([-P[i][col], R[i][left][0]])
            for i2 in range(j):
                if i2 != i:
                    cnf.add([-P[i][col], R[i2][col][0]])

    MUL = F.MUL
    ADD = F.ADD
    NEG = F.NEG

    def sympl_chain(U, V, want_zero):
        st = cnf.one_hot(q)
        cnf.add([st[0]])
        for qq in range(n):
            new = cnf.one_hot(q)
            for s in range(q):
                for xu, zu, xv, zv in itertools.product(range(q), repeat=4):
                    t = ADD[MUL[xu][zv], NEG[MUL[zu][xv]]]
                    cnf.add([-st[s], -U[2 * qq][xu], -U[2 * qq + 1][zu],
                             -V[2 * qq][xv], -V[2 * qq + 1][zv],
                             new[ADD[s][t]]])
            st = new
        cnf.add([st[0]] if want_zero else [-st[0]])

    for i in range(j):
        for i2 in range(i + 1, j):
            sympl_chain(R[i], R[i2], True)
        sympl_chain(A, R[i], True)
        sympl_chain(B, R[i], True)
    sympl_chain(A, B, False)

    # class digit cells: for each support class rep, per qudit, x and z
    CLASSES = [(1, 0)] + [(r, 1) for r in range(q)]
    CD = []  # CD[ci][qq] = (xdigits one-hot, zdigits one-hot)
    for (al, be) in CLASSES:
        row = []
        for qq in range(n):
            xd = cnf.one_hot(q)
            zd = cnf.one_hot(q)
            for av, bv in itertools.product(range(q), repeat=2):
                xval = ADD[MUL[al][av]][MUL[be][bv]]
                cnf.add([-A[2 * qq][av], -B[2 * qq][bv], xd[xval]])
                zval = ADD[MUL[al][av]][MUL[be][bv]]
                cnf.add([-A[2 * qq + 1][av], -B[2 * qq + 1][bv], zd[zval]])
            row.append((xd, zd))
        CD.append(row)

    # shift digit chains along Gray order
    tvecs = gray_vecs(q, j)
    Sx = {tvecs[0]: [None] * n}
    Sz = {tvecs[0]: [None] * n}
    prev = tvecs[0]
    for tv in tvecs[1:]:
        diff = [i for i in range(j) if tv[i] != prev[i]]
        assert len(diff) == 1
        i = diff[0]
        delta = ADD[tv[i]][NEG[prev[i]]]
        rowx, rowz = [], []
        for qq in range(n):
            xs = cnf.one_hot(q)
            zs = cnf.one_hot(q)
            px, pz = Sx[prev][qq], Sz[prev][qq]
            for rv in range(q):
                dxi = MUL[delta][rv]
                if px is None:
                    cnf.add([-R[i][2 * qq][rv], xs[dxi]])
                else:
                    for pv in range(q):
                        cnf.add([-px[pv], -R[i][2 * qq][rv],
                                 xs[ADD[pv][dxi]]])
                if pz is None:
                    cnf.add([-R[i][2 * qq + 1][rv], zs[dxi]])
                else:
                    for pv in range(q):
                        cnf.add([-pz[pv], -R[i][2 * qq + 1][rv],
                                 zs[ADD[pv][dxi]]])
            rowx.append(xs)
            rowz.append(zs)
        Sx[tv] = rowx
        Sz[tv] = rowz
        prev = tv

    # non-acting literals + at-most-1 per (class, shift)
    for ci in range(len(CLASSES)):
        for tv in tvecs:
            lits = []
            for qq in range(n):
                xd, zd = CD[ci][qq]
                xs, zs = Sx[tv][qq], Sz[tv][qq]
                if xs is None:
                    e = cnf.var()
                    cnf.add([-xd[0], -zd[0], e])
                    lits.append(e)
                else:
                    e = cnf.var()
                    # non-acting iff class x = -shift x AND class z = -shift z
                    for v in range(q):
                        for w in range(q):
                            cnf.add([-xd[v], -xs[NEG[v]], -zd[w],
                                     -zs[NEG[w]], e])
                    lits.append(e)
            if slack == 1:
                for u in range(len(lits)):
                    for v in range(u + 1, len(lits)):
                        cnf.add([-lits[u], -lits[v]])
            else:  # Sinz sequential at-most-slack
                k = slack
                s = [[cnf.var() for _ in range(k)]
                     for _ in range(len(lits))]
                cnf.add([-lits[0], s[0][0]])
                for jj in range(1, k):
                    cnf.add([-s[0][jj]])
                for idx in range(1, len(lits)):
                    cnf.add([-lits[idx], s[idx][0]])
                    cnf.add([-s[idx - 1][0], s[idx][0]])
                    for jj in range(1, k):
                        cnf.add([-lits[idx], -s[idx - 1][jj - 1],
                                 s[idx][jj]])
                        cnf.add([-s[idx - 1][jj], s[idx][jj]])
                    cnf.add([-lits[idx], -s[idx - 1][k - 1]])

    tag = f"q{q}_n{n}_k1_c{c}_d{d}"
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
        print(f"UNSAT: no F_{q}-linear [[{n},1,{d};{c}]]_{q} EAQECC exists "
              f"(free radical, complete)")
        sys.exit(20)
    assert p.returncode == 10, (p.returncode, p.stderr[-200:])
    model = set()
    for line in p.stdout.splitlines():
        if line.startswith("v "):
            model.update(int(x) for x in line[2:].split() if x != "0")

    def dec(row):
        return np.array([next(v for v in range(q) if row[t][v] in model)
                         for t in range(N2)])

    L = [dec(R[i]) for i in range(j)] + [dec(A), dec(B)]
    r = evaluate_L(F, n, L, d)
    print("SAT; independent evaluator check:", r)
    import json
    wdir = out_dir or Path(".")
    json.dump({"target": {"n": n, "k": 1, "c": c, "d": d, "q": q},
               "L_basis": [[int(x) for x in row] for row in L],
               "verified": {kk: int(vv) for kk, vv in r.items()},
               "provenance": "free-radical RREF SAT"},
              open(wdir / f"WITNESS{q}_n{n}_k1_c{c}_d{d}.json", "w"))
    sys.exit(10)


if __name__ == "__main__":
    main()
