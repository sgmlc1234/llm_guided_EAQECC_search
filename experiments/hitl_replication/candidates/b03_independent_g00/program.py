import math
import numpy as np

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    s = n - k + c_target
    l_size = n + k - c_target
    
    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def random_independent_L():
        L = []
        while len(L) < l_size:
            v = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)
        return L

    L = random_independent_L()
    cur = objective(E.evaluate(get_S(L)))
    
    temp = 30.0
    fails = 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        cand_L = list(L)
        idx = int(rng.integers(l_size))
        if rng.random() < 0.5:
            cand_L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            cand_L[idx] ^= delta
            
        if len(E.gf2_basis(cand_L)) != l_size:
            continue
            
        cand_S = get_S(cand_L)
        new_obj = objective(E.evaluate(cand_S))
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = cand_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            if fails > 1000:
                L = random_independent_L()
                cur = objective(E.evaluate(get_S(L)))
                fails = 0
                temp = 30.0
    return None