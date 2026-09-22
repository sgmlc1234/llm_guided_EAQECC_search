import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L_basis):
        # Convert L to S via S = J(L)^perp
        j_L = [E._J(v, n) for v in L_basis]
        return E.nullspace(j_L, 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    # Initialize L as random independent vectors
    while E.remaining:
        # Generate a valid starting L of rank l_rank
        L = []
        while len(L) < l_rank:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = list(L)
            idx = int(rng.integers(l_rank))
            cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != l_rank:
                fails += 1
                continue
                
            cand_S = get_S(cand_L)
            if len(cand_S) != s:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None