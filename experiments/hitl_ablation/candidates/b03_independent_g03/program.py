import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    l_size = n + k - c

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res.get("c", 0) - c) + res.get("offending", 999) * 10
        if res.get("c") == c and res.get("offending") == 0:
            d = res.get("d")
            if d is not None:
                val -= d
        return val

    def random_L():
        while True:
            L = []
            for _ in range(l_size):
                v = int(rng.integers(1, 1 << (2 * n)))
                L.append(v)
            if len(E.gf2_basis(L)) == l_size:
                return L

    L = random_L()
    S = get_S(L)
    res = E.evaluate(S)
    cur = objective(res)

    temp = 30.0
    fails = 0

    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        if rng.random() < 0.2:
            candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate_L[idx] ^= delta

        if len(E.gf2_basis(candidate_L)) != l_size:
            continue

        candidate_S = get_S(candidate_L)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)

        delta_val = new_obj - cur
        if delta_val <= 0 or rng.random() < math.exp(-delta_val / temp):
            L, cur = candidate_L, new_obj
            fails = 0
        else:
            fails += 1
            if fails > 200:
                L = random_L()
                S = get_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
                temp = 30.0

    return None