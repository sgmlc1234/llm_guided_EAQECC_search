import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    l = n + k - target_c
    s = n - k + target_c

    def L_to_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target_c) + res["offending"]

    def get_random_L():
        while True:
            L = []
            for _ in range(l):
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                L.append(val)
            if len(E.gf2_basis(L)) == l:
                return L

    L = get_random_L()
    S = L_to_S(L)
    cur = objective(E.evaluate(S))

    temp = 30.0
    fails = 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        idx = int(rng.integers(l))
        old_val = L[idx]
        
        if rng.random() < 0.2:
            L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            L[idx] ^= delta

        if len(E.gf2_basis(L)) != l:
            L[idx] = old_val
            fails += 1
            if fails > 1000:
                L = get_random_L()
                S = L_to_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
            continue

        S_cand = L_to_S(L)
        if len(S_cand) != s:
            L[idx] = old_val
            continue

        new_res = E.evaluate(S_cand)
        new_obj = objective(new_res)
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            cur = new_obj
            fails = 0
        else:
            L[idx] = old_val
            fails += 1
            if fails > 1000:
                L = get_random_L()
                S = L_to_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
    return None