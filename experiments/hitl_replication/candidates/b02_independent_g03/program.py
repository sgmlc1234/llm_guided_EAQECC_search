import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_len = n + k - c

    def get_S(L):
        # Convert L (symplectic dual) to S (stabilizer basis)
        j_L = [E._J(v, n) for v in L]
        return E.nullspace(j_L, 2 * n)

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

    initial_state = E.incumbent
    initial_measurement = E.incumbent_parameters
    
    while E.remaining:
        if initial_state is not None:
            # Try to reconstruct L from S if possible, but simpler to just restart/generate random L
            # Since we want to search in L-space:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l_len)]
            while len(E.gf2_basis(L)) != l_len:
                L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l_len)]
            initial_state = None
        else:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l_len)]
            while len(E.gf2_basis(L)) != l_len:
                L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l_len)]
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            candidate_L[int(rng.integers(l_len))] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != l_len:
                fails += 1
                continue
                
            cand_S = get_S(candidate_L)
            if len(cand_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(cand_S)
            new_obj = objective(res)
            if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None