import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    target_c = target["c"]
    target_d = target["d"]
    s_L = n + k - target_c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - target_c) + res["offending"]
        if res.get("d") is not None:
            val += 100 * max(0, target_d - res["d"])
        return val

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2*n))) for _ in range(s_L)]
            if len(E.gf2_basis(L)) == s_L:
                return L

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2*n)
    cur = objective(E.evaluate(S))
    temp = 30.0
    fails = 0

    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(s_L))
        candidate_L[idx] ^= random_pauli()
        if len(E.gf2_basis(candidate_L)) != s_L:
            fails += 1
            if fails > 450:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2*n)
                cur = objective(E.evaluate(S))
                fails = 0
            continue
        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2*n)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
        else:
            fails += 1
            if fails > 450:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2*n)
                cur = objective(E.evaluate(S))
                fails = 0
    return None