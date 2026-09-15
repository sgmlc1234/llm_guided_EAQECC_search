import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    L_size = n + k - c
    
    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2*n)
        
    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        off = res["offending"]
        c_diff = abs(res["c"] - c)
        d = res.get("d", 0) or 0
        return 10000 * off + 1000 * c_diff + max(0, target["d"] - d)

    def random_vector():
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def get_random_L():
        while True:
            L = [random_vector() for _ in range(L_size)]
            if len(E.gf2_basis(L)) == L_size:
                return L

    best_L = get_random_L()
    best_S = get_S(best_L)
    best_res = E.evaluate(best_S)
    best_obj = objective(best_res)
    
    state_L = list(best_L)
    cur_obj = best_obj
    
    temp = 10.0
    fails = 0
    
    while E.remaining:
        candidate_L = list(state_L)
        idx = int(rng.integers(L_size))
        if rng.random() < 0.3:
            candidate_L[idx] = random_vector()
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate_L[idx] ^= delta
            
        if len(E.gf2_basis(candidate_L)) != L_size:
            continue
            
        cand_S = get_S(candidate_L)
        res = E.evaluate(cand_S)
        obj = objective(res)
        
        if obj < cur_obj or rng.random() < math.exp((cur_obj - obj) / temp):
            state_L = candidate_L
            cur_obj = obj
            if obj < best_obj:
                best_L = list(candidate_L)
                best_obj = obj
                if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target["d"]:
                    return cand_S
        
        temp = max(0.01, temp * 0.999)
        fails += 1
        if fails > 200:
            state_L = get_random_L()
            cand_S = get_S(state_L)
            cur_obj = objective(E.evaluate(cand_S))
            temp = 10.0
            fails = 0
            
    return None