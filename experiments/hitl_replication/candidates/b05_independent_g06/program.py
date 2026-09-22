import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    r_L = n + k - c

    def get_S(L):
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2*n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_L():
        L = []
        while len(L) < r_L:
            v = int(rng.integers(1, 1 << (2*n)))
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)
        return L

    best_L = random_L()
    S = get_S(best_L)
    best_obj = 10**9
    if len(S) == s:
        best_obj = objective(E.evaluate(S))

    temp = 10.0
    fails = 0
    while E.remaining:
        candidate_L = list(best_L)
        idx = int(rng.integers(r_L))
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        
        candidate_L[idx] ^= delta
        if len(E.gf2_basis(candidate_L)) != r_L:
            continue
        
        cand_S = get_S(candidate_L)
        if len(cand_S) != s:
            continue
            
        res = E.evaluate(cand_S)
        cand_obj = objective(res)
        
        if cand_obj <= best_obj or rng.random() < math.exp((best_obj - cand_obj) / temp):
            best_L = candidate_L
            best_obj = cand_obj
            fails = 0
        else:
            fails += 1
            
        temp = max(0.01, temp * 0.999)
        if fails > 500:
            best_L = random_L()
            S = get_S(best_L)
            if len(S) == s:
                best_obj = objective(E.evaluate(S))
            else:
                best_obj = 10**9
            temp = 10.0
            fails = 0
    return None