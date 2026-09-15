import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def l_to_s(L_basis):
        # L is of rank l_rank = 2n - s
        # S is the symplectic dual of L: S = {v : sform(v, w) = 0 for all w in L}
        # sform(v, w) = v . _J(w) in GF(2).
        # So S is the nullspace of [_J(w) for w in L]
        swapped = [E._J(w, n) for w in L_basis]
        return E.nullspace(swapped, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_random_L():
        # Generate a random independent set L of size l_rank
        # Symmetrically, we can sample standard stabilizers
        return list(E.random_stabilizer(n, l_rank, rng))

    # We will search by mutating the basis L of rank l_rank throughout the search.
    while E.remaining:
        L = get_random_L()
        S_cand = l_to_s(L)
        if len(S_cand) != s:
            continue
        res = E.evaluate(S_cand)
        cur = objective(res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            # Mutate L
            idx = int(rng.integers(l_rank))
            candidate_L = list(L)
            # Apply a random small Pauli error
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate_L[idx] ^= delta
            
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
            
            S_cand = l_to_s(candidate_L)
            if len(S_cand) != s:
                fails += 1
                continue
                
            new_res = E.evaluate(S_cand)
            new_obj = objective(new_res)
            delta_obj = new_obj - cur
            if delta_obj <= 0 or rng.random() < math.exp(-delta_obj / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta_obj < 0 else fails + 1
            else:
                fails += 1
    return None