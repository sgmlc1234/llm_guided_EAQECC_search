import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    m = n + k - c  # Rank of L
    s = n - k + c  # Rank of S

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

    while E.remaining:
        # Generate a random initial L of rank m
        while True:
            L = [int(rng.integers(0, 1 << (2 * n))) for _ in range(m)]
            if len(E.gf2_basis(L)) == m:
                break
        
        J_L = [E._J(v, n) for v in L]
        S = E.nullspace(J_L, 2 * n)
        if len(S) != s:
            continue
            
        res = E.evaluate(S)
        cur = objective(res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(m))
            if rng.random() < 0.5:
                candidate_L[idx] ^= random_pauli()
            else:
                candidate_L[idx] = int(rng.integers(0, 1 << (2 * n)))
                
            if len(E.gf2_basis(candidate_L)) != m:
                fails += 1
                continue
                
            candidate_J_L = [E._J(v, n) for v in candidate_L]
            candidate_S = E.nullspace(candidate_J_L, 2 * n)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(candidate_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None