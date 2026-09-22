#!/usr/bin/env python3
"""Pinned-radical SA over F_4 for the gamma_4 campaign:
targets [[n,1,n-1;c]]_4, radical pinned to j = n-1-c Z-pairs (z=(1,1)).
Fast vectorized span evaluation. Usage: sa_gamma4.py n c [seconds]
"""

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
from helpers_eaqecc_fq import Fq, evaluate_L, vecq, fq_rank  # noqa: E402

F = Fq(4)
Q = 4


def span_weights_offending(L_basis, n, d_target):
    """All q^m span elements; returns (min logical wt, #offending, sig_ok
    ingredients): vectorized."""
    m = len(L_basis)
    B = np.array(L_basis, dtype=np.int64)
    span = np.zeros((1, 2 * n), dtype=np.int64)
    for i in range(m):
        blocks = [F.ADD[span, F.MUL[s, B[i]][None, :]] for s in range(Q)]
        span = np.concatenate(blocks, axis=0)
    # gram pairing per element to detect radical members
    gram = np.array([[F.sform(u, v, n) for v in L_basis] for u in L_basis],
                    dtype=np.int64)
    # coefficient array parallel to span construction
    coeffs = np.zeros((1, m), dtype=np.int64)
    for i in range(m):
        blocks = []
        for s in range(Q):
            cc = coeffs.copy()
            cc[:, i] = s
            blocks.append(cc)
        coeffs = np.concatenate(blocks, axis=0)
    pair = np.zeros((len(coeffs), m), dtype=np.int64)
    for idx in range(m):
        acc = np.zeros(len(coeffs), dtype=np.int64)
        for jdx in range(m):
            acc = F.ADD[acc, F.MUL[coeffs[:, jdx], gram[jdx][idx]]]
        pair[:, idx] = acc
    logical = pair.any(axis=1)
    acted = (span[:, 0::2] != 0) | (span[:, 1::2] != 0)
    w = acted.sum(axis=1)
    lw = w[logical]
    if not len(lw):
        return None, 10**9
    return int(lw.min()), int((lw < d_target).sum())


def main():
    n, c = int(sys.argv[1]), int(sys.argv[2])
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
    d = n - 1
    j = n - 1 - c
    assert 2 * j <= n, "pin needs n >= 2j"
    rhos = []
    for i in range(j):
        p = [(0, 0)] * n
        p[2 * i], p[2 * i + 1] = (0, 1), (0, 1)
        rhos.append(vecq(p, n))
    rng = np.random.default_rng(400 + n * 10 + c)
    t0 = time.time()

    def obj(a, b):
        L = rhos + [a, b]
        if fq_rank(F, L) < j + 2:
            return 10**9
        # signature: need <a,b> != 0 (then c,k automatic given pin)
        if F.sform(a, b, n) == 0:
            return 10**9
        _, off = span_weights_offending(L, n, d)
        return off

    best = (10**9, None)
    restarts = 0
    while time.time() - t0 < budget and best[0] > 0:
        restarts += 1
        a = rng.integers(0, Q, size=2 * n)
        b = rng.integers(0, Q, size=2 * n)
        cur = obj(a, b)
        temp, fails = 12.0, 0
        while fails < 400 and time.time() - t0 < budget:
            temp = max(0.05, temp * 0.995)
            na, nb = a.copy(), b.copy()
            tgt = na if rng.random() < 0.5 else nb
            for _ in range(1 + int(rng.integers(3))):
                tgt[int(rng.integers(2 * n))] = int(rng.integers(Q))
            o2 = obj(na, nb)
            dlt = o2 - cur
            if dlt <= 0 or rng.random() < np.exp(-min(dlt, 50) / temp):
                a, b, cur = na, nb, o2
                fails = 0 if dlt < 0 else fails + 1
                if cur < best[0]:
                    best = (cur, (a.copy(), b.copy()))
                if cur == 0:
                    break
            else:
                fails += 1
    if best[0] == 0:
        a, b = best[1]
        L = rhos + [a, b]
        r = evaluate_L(F, n, L, d)
        assert (r["k"] == 1 and r["c"] == c and r["d"] == d
                and r["offending"] == 0), r
        os.makedirs("artifacts/gamma4", exist_ok=True)
        path = f"artifacts/gamma4/SOLUTION4_n{n}_k1_c{c}_d{d}.json"
        json.dump({"target": {"n": n, "k": 1, "c": c, "d": d, "q": 4},
                   "L_basis": [[int(x) for x in row] for row in L],
                   "verified": {kk: int(vv) for kk, vv in r.items()}},
                  open(path, "w"))
        print(f"[[{n},1,{d};{c}]]_4 FOUND & verified ({restarts} restarts)")
    else:
        print(f"[[{n},1,{d};{c}]]_4 not found (best off={best[0]}, "
              f"{restarts} restarts)")


if __name__ == "__main__":
    main()
