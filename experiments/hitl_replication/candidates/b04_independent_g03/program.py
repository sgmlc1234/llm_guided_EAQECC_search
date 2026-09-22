import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = n + k - c

    def get_S(L):
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    while E.remaining:
        L = []
        while len(L) < l_size:
            v = random_vector()
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if cur == 0:
            return S
        
        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(l_size))
            old_val = L[idx]
            
            if rng.random() < 0.3:
                new_val = random_vector()
            else:
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                new_val = old_val ^ delta
                
            if new_val == 0:
                fails += 1
                continue
                
            candidate_L = list(L)
            candidate_L[idx] = new_val
            if len(E.gf2_basis(candidate_L)) != l_size:
                fails += 1
                continue
                
            S_cand = get_S(candidate_L)
            new_res = E.evaluate(S_cand)
            new_obj = objective(new_res)
            
            if new_obj == 0:
                return S_cand
                
            delta_val = new_obj - cur
            if delta_val <= 0 or rng.random() < math.exp(-delta_val / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta_val < 0 else fails + 1
            else:
                fails += 1
                
    return None