import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - target["c"]) + res["offending"]
        if res.get("d") is not None:
            val += 100 * max(0, target["d"] - res["d"])
        return val

    def get_random_L():
        while True:
            candidate = []
            for _ in range(l):
                v = 0
                while v == 0:
                    v = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(v)
            if len(E.gf2_basis(candidate)) == l:
                return candidate

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur_res = E.evaluate(S)
    cur_obj = objective(cur_res)
    best_S = S if cur_obj < 10**9 else None
    
    temp = 100.0
    fails = 0

    while E.remaining:
        temp = max(0.1, temp * 0.999)
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

        if L[idx] == 0 or len(E.gf2_basis(L)) != l:
            L[idx] = old_val
            fails += 1
            if fails > 1000:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                cur_res = E.evaluate(S)
                cur_obj = objective(cur_res)
                fails = 0
            continue

        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        obj = objective(res)

        delta_obj = obj - cur_obj
        if delta_obj <= 0 or rng.random() < math.exp(-delta_obj / temp):
            cur_obj = obj
            fails = 0
            if obj < 5000:
                best_S = S
        else:
            L[idx] = old_val
            fails += 1

    return best_S
