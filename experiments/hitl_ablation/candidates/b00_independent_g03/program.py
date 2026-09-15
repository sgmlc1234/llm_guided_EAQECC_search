import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = 2 * n - s  # n + k - c
    
    # Target: c = target["c"], offending = 0
    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        # Penalize difference from target c, and offending generators
        return 1000 * abs(res["c"] - c) + res["offending"]

    def get_S_from_L(L):
        # Symplectic dual: S = nullspace of J(L)
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    # To initialize L:
    # S has size s. S_perp (the symplectic dual) has size 2*n - s = len_L.
    # We can generate a random stabilizer of size s, and find its dual, or generate directly.
    # Let's start with a random stabilizer S, compute its dual as our initial L.
    
    while E.remaining:
        # Generate initial independent L
        while True:
            S_init = E.random_stabilizer(n, s, rng)
            J_S = [E._J(v, n) for v in S_init]
            L = E.nullspace(J_S, 2 * n)
            if len(L) == len_L and len(E.gf2_basis(L)) == len_L:
                break
        
        S_cand = get_S_from_L(L)
        cur_obj = objective(E.evaluate(S_cand))
        
        temp, fails = 30.0, 0
        while fails < 1200 and E.remaining:
            temp = max(0.05, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(len_L))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != len_L:
                fails += 1
                continue
                
            S_cand = get_S_from_L(candidate_L)
            if len(S_cand) != s or len(E.gf2_basis(S_cand)) != s:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(S_cand))
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None