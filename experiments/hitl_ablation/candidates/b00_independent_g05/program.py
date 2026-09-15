import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    dim_L = n + k - c
    
    def l_to_s(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target["c"]) + res["offending"]

    while E.remaining:
        L = []
        while len(L) < dim_L:
            v = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)
        
        S = l_to_s(L)
        if len(S) != s:
            continue
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == target["c"]:
            return S
            
        temp = 30.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(dim_L))
            old_v = L[idx]
            if rng.random() < 0.2:
                new_v = int(rng.integers(1, 1 << (2 * n)))
            else: 
                qubit = int(rng.integers(n))
                pauli = int(rng.integers(1, 4))
                new_v = old_v ^ (pauli << (2 * qubit))
            
            if new_v == 0:
                continue
                
            candidate_L = list(L)
            candidate_L[idx] = new_v
            
            if len(E.gf2_basis(candidate_L)) != dim_L:
                fails += 1
                continue
                
            candidate_S = l_to_s(candidate_L)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(candidate_S)
            if res.get("offending") == 0 and res.get("c") == target["c"]:
                return candidate_S
                
            new_obj = objective(res)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None