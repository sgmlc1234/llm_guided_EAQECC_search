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
        return 5000 * abs(res["c"] - target_c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.choice([1, 2], p=[0.8, 0.2])), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        L_basis = list(E.random_stabilizer(n, l_rank, rng))
        S_basis = l_to_s(L_basis)
        if len(S_basis) < s:
            while len(S_basis) < s:
                S_basis.append(rng.integers(1, 1 << (2 * n)))
                S_basis = E.gf2_basis(S_basis)
        elif len(S_basis) > s:
            S_basis = S_basis[:s]
            
        cur_res = E.evaluate(S_basis)
        cur = objective(cur_res)
        if cur_res.get("offending") == 0 and cur_res.get("c") == target_c and cur_res.get("k") == k:
            return S_basis
            
        temp, fails = 30.0, 0
        while fails < 1200 and E.remaining:
            temp = max(0.05, temp * 0.996)
            candidate_L = list(L_basis)
            idx = int(rng.integers(l_rank))
            
            if rng.random() < 0.15:
                candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
            else:
                candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
                
            cand_S = l_to_s(candidate_L)
            if len(cand_S) < s:
                while len(cand_S) < s:
                    cand_S.append(rng.integers(1, 1 << (2 * n)))
                    cand_S = E.gf2_basis(cand_S)
            elif len(cand_S) > s:
                cand_S = cand_S[:s]
                
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