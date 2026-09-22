import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    s = n - k + target_c
    dim_L = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target_c) + res["offending"]

    def get_S_from_L(L_basis):
        eqs = [E._J(v, n) for v in L_basis]
        return E.nullspace(eqs, 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Start by generating a random stabilizer S of rank s
        S = list(E.random_stabilizer(n, s, rng))
        # Its symplectic dual L has dimension dim_L
        L_eqs = [E._J(v, n) for v in S]
        L_basis = E.nullspace(L_eqs, 2 * n)
        if len(L_basis) != dim_L:
            continue

        res = E.evaluate(S)
        cur_obj = objective(res)
        
        temp = 30.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            # Mutate L
            candidate_L = list(L_basis)
            idx = int(rng.integers(dim_L))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != dim_L:
                fails += 1
                continue
            
            candidate_S = get_S_from_L(candidate_L)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(candidate_S)
            new_obj = objective(res)
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L_basis, cur_obj = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None