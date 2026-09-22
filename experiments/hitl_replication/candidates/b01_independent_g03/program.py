import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        dual_inputs = [E._J(v, n) for v in L]
        return E.nullspace(dual_inputs, 2 * n)

    while E.remaining:
        # Initialize L
        L = []
        while len(L) < l:
            v = int(rng.integers(1, 1 << (2 * n)))
            temp_L = L + [v]
            if len(E.gf2_basis(temp_L)) == len(temp_L):
                L.append(v)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 2000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != l:
                fails += 1
                continue
                
            candidate_S = get_S(candidate_L)
            new_obj = objective(E.evaluate(candidate_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:                fails += 1
    return None