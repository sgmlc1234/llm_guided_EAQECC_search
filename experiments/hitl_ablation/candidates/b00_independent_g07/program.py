import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    L_rank = n + k - c
    
    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res.get("c", 0) - c) + res.get("offending", 0)

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    L = []
    while len(L) < L_rank:
        v = random_vector()
        test_L = L + [v]
        if len(E.gf2_basis(test_L)) == len(test_L):
            L.append(v)
            
    S = E.nullspace([E._J(v, n) for v in L], 2*n)
    res = E.evaluate(S)
    cur = objective(res)
    
    best_L = list(L)
    best_cur = cur
    temp = 30.0
    fails = 0
    
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate = list(L)
        idx = int(rng.integers(L_rank))
        
        if rng.random() < 0.5:
            candidate[idx] ^= int(rng.integers(1, 1 << (2 * n)))
        else:
            other_idx = int(rng.integers(L_rank))
            if other_idx != idx:
                candidate[idx] ^= candidate[other_idx]
                candidate[idx] ^= int(rng.integers(1, 4)) << int(2 * rng.integers(n))
                
        if len(E.gf2_basis(candidate)) != L_rank:
            continue
            
        S_cand = E.nullspace([E._J(v, n) for v in candidate], 2*n)
        res_cand = E.evaluate(S_cand)
        new_obj = objective(res_cand)
        
        if res_cand.get("offending") == 0 and res_cand.get("c") == c and res_cand.get("k") == k:
            if res_cand.get("d", 0) is not None and res_cand.get("d", 0) >= target["d"]:
                return S_cand
                
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = candidate
            cur = new_obj
            if cur < best_cur:
                best_cur = cur
                best_L = list(L)
            fails = 0
        else:
            fails += 1
            if fails > 500:
                L = list(best_L)
                for _ in range(int(rng.integers(1, 3))):
                    midx = int(rng.integers(L_rank))
                    L[midx] ^= int(rng.integers(1, 1 << (2 * n)))
                if len(E.gf2_basis(L)) != L_rank:
                    L = []
                    while len(L) < L_rank:
                        v = random_vector()
                        test_L = L + [v]
                        if len(E.gf2_basis(test_L)) == len(test_L):
                            L.append(v)
                S = E.nullspace([E._J(v, n) for v in L], 2*n)
                cur = objective(E.evaluate(S))
                fails = 0
                temp = 30.0
                
    return None