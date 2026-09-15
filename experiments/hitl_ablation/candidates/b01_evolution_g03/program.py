import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    s = n - k + target_c
    l_rank = n + k - target_c
    
    def l_to_s(L_basis):
        constraints = [E._J(v, n) for v in L_basis]
        null_basis = E.nullspace(constraints, 2 * n)
        return list(null_basis)

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 10000 * abs(res["c"] - target_c) + res["offending"]

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    while E.remaining:
        # Start with a random stabilizer basis of rank l_rank
        L_basis = list(E.random_stabilizer(n, l_rank, rng))
        S_basis = l_to_s(L_basis)
        if len(S_basis) != s:
            continue
            
        cur_res = E.evaluate(S_basis)
        cur = objective(cur_res)
        if cur_res.get("offending") == 0 and cur_res.get("c") == target_c and cur_res.get("k") == k:
            return S_basis
            
        temp = 20.0
        fails = 0
        
        while fails < 250 and E.remaining:
            temp = max(0.01, temp * 0.98)
            candidate_L = list(L_basis)
            idx = int(rng.integers(l_rank))
            
            # Apply a mutation: either small perturbation or complete replacement of one vector
            if rng.random() < 0.7:
                qubits = rng.choice(n, size=int(rng.choice([1, 2], p=[0.8, 0.2])), replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                candidate_L[idx] ^= delta
            else:
                candidate_L[idx] = random_vector()
                
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
                
            cand_S = l_to_s(candidate_L)
            if len(cand_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(cand_S)
            new_obj = objective(res)
            if res.get("offending") == 0 and res.get("c") == target_c and res.get("k") == k:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L_basis, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None