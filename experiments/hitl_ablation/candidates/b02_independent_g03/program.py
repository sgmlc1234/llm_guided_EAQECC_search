import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    rank_L = n + k - c
    
    def get_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)
        
    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        val = 0
        for q in range(n):
            val |= int(rng.integers(0, 4)) << (2 * q)
        return val

    def generate_independent_L():
        while True:
            L = []
            for _ in range(rank_L):
                L.append(random_vector())
            if len(E.gf2_basis(L)) == rank_L:
                return L

    best_L = generate_independent_L()
    best_S = get_S(best_L)
    best_obj = objective(E.evaluate(best_S))

    temp = 30.0
    fails = 0
    
    while E.remaining:
        if fails > 200:
            # Restart
            best_L = generate_independent_L()
            best_S = get_S(best_L)
            best_obj = objective(E.evaluate(best_S))
            fails = 0
            temp = 30.0
            
        temp = max(0.1, temp * 0.995)
        candidate_L = list(best_L)
        idx = int(rng.integers(rank_L))
        # Mutate one element of L
        candidate_L[idx] ^= random_vector()
        
        if len(E.gf2_basis(candidate_L)) != rank_L:
            fails += 1
            continue
            
        cand_S = get_S(candidate_L)
        res = E.evaluate(cand_S)
        new_obj = objective(res)
        
        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
            return cand_S
            
        delta = new_obj - best_obj
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            best_L, best_obj = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
    return None