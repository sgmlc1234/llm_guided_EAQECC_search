import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    m = n + k - c

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(m)]
            if len(E.gf2_basis(L)) == m:
                return L

    L = random_L()
    S = get_S(L)
    cur = objective(E.evaluate(S))

    temp = 30.0
    fails = 0
    while E.remaining and fails < 2000:
        temp = max(0.1, temp * 0.995)
        idx = int(rng.integers(m))
        old_val = L[idx]
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        
        L[idx] ^= delta
        if len(E.gf2_basis(L)) != m:
            L[idx] = old_val
            fails += 1
            continue

        cand_S = get_S(L)
        res = E.evaluate(cand_S)
        new_obj = objective(res)
        delta_obj = new_obj - cur
        if delta_obj <= 0 or rng.random() < math.exp(-delta_obj / temp):
            cur = new_obj
            fails = 0 if delta_obj < 0 else fails + 1
        else:
            L[idx] = old_val
            fails += 1

    return None