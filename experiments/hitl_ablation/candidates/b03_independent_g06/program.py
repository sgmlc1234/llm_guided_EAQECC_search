import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def get_S(L):
        orthogonal_to = [E._J(v, n) for v in L]
        return E.nullspace(orthogonal_to, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        d_val = res.get("d")
        d_penalty = 0
        if d_val is not None:
            d_penalty = max(0, target["d"] - d_val) * 100
        return 5000 * abs(res["c"] - c) + res["offending"] * 10 + d_penalty

    def get_random_L():
        while True:
            L = []
            for _ in range(l_rank):
                L.append(int(rng.integers(1, 1 << (2 * n))))
            if len(E.gf2_basis(L)) == l_rank:
                return L

    L = get_random_L()
    S = get_S(L)
    best_obj = 10**9
    if len(S) == s:
        res = E.evaluate(S)
        best_obj = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k and res.get("d", 0) >= target["d"]:
            return S

    temp = 30.0
    fails = 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(l_rank))
        if rng.random() < 0.3:
            candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate_L[idx] ^= delta

        if len(E.gf2_basis(candidate_L)) != l_rank:
            fails += 1
            if fails > 200:
                L = get_random_L()
                fails = 0
            continue

        cand_S = get_S(candidate_L)
        if len(cand_S) != s:
            continue

        res = E.evaluate(cand_S)
        new_obj = objective(res)

        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k and res.get("d", 0) >= target["d"]:
            return cand_S

        delta = new_obj - best_obj
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = candidate_L
            best_obj = new_obj
            fails = 0
        else:
            fails += 1
            if fails > 500:
                L = get_random_L()
                best_obj = 10**9
                fails = 0
                temp = 30.0

    return None