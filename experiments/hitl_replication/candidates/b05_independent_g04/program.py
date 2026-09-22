import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_random_L():
        while True:
            candidate = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l)]
            if len(E.gf2_basis(candidate)) == l:
                return candidate

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur = objective(E.evaluate(S))

    temp = 30.0
    fails = 0

    while E.remaining:
        temp = max(0.1, temp * 0.995)
        if fails > 500:
            L = get_random_L()
            S = E.nullspace([E._J(v, n) for v in L], 2 * n)
            cur = objective(E.evaluate(S))
            fails = 0
            temp = 30.0
            continue

        candidate_L = list(L)
        idx = int(rng.integers(l))
        candidate_L[idx] ^= random_pauli()
        if len(E.gf2_basis(candidate_L)) != l:
            fails += 1
            continue

        S_cand = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        res_cand = E.evaluate(S_cand)
        new_obj = objective(res_cand)

        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1

    return None