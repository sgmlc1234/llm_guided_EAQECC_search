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
        c_diff = abs(res["c"] - target_c)
        offending = res["offending"]
        d = res.get("d")
        d_val = d if d is not None else 0
        d_diff = max(0, target_d - d_val)
        return c_diff * 10000 + offending * 1000 + d_diff

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2*n))) for _ in range(s_L)]
            if len(E.gf2_basis(L)) == s_L:
                return L

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2*n)
    cur_res = E.evaluate(S)
    cur = objective(cur_res)
    
    best_L = list(L)
    best_obj = cur
    
    no_improve = 0
    temp = 10.0

    while E.remaining:
        temp = max(0.01, temp * 0.995)
        candidate_L = None
        for _ in range(50):
            test_L = list(L)
            idx = int(rng.integers(s_L))
            if rng.random() < 0.3:
                test_L[idx] = int(rng.integers(1, 1 << (2*n)))
            else:
                wt = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
                qubits = rng.choice(n, size=wt, replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                test_L[idx] ^= delta
                
            if len(E.gf2_basis(test_L)) == s_L:
                candidate_L = test_L
                break
                
        if candidate_L is None:
            continue
            
        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2*n)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        
        if new_obj < best_obj:
            best_obj = new_obj
            best_L = list(candidate_L)
            
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            no_improve = 0
        else:
            no_improve += 1
            
        if no_improve > 300:
            if rng.random() < 0.5:
                L = get_random_L()
            else:
                L = list(best_L)
            S = E.nullspace([E._J(v, n) for v in L], 2*n)
            cur = objective(E.evaluate(S))
            no_improve = 0
            temp = 10.0

    return None