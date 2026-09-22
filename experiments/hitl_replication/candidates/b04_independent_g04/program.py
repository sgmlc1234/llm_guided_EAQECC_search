"""Search in the dual space L of size n+k-c and convert candidate L to S."""

import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    # L_size = n + k - c
    l_size = n + k - c
    s_size = n - k + c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        # Convert L to S via symplectic dual
        # J_L has shape [l_size]
        J_L = [E._J(v, n) for v in L]
        S_all = E.nullspace(J_L, 2 * n)
        # S_all may have rank 2*n - len(L) = 2*n - (n+k-c) = n-k+c = s_size
        # Ensure we return a basis of exactly s_size elements
        basis = E.gf2_basis(S_all)
        if len(basis) < s_size:
            # Pad with independent generators if needed, but usually nullspace matches exactly
            return basis
        return basis[:s_size]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Generate a random independent basis for L of size l_size
        # E.random_stabilizer(n, l_size, rng) produces isotropic, but L is not necessarily isotropic.
        # Let's generate random Paulis and keep them independent.
        L = []
        while len(L) < l_size:
            candidate_vec = int(rng.integers(0, 1 << (2 * n)))
            if len(E.gf2_basis(L + [candidate_vec])) == len(L) + 1:
                L.append(candidate_vec)

        S = get_S(L)
        if len(S) < s_size:
            continue
        cur = objective(E.evaluate(S))

        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            # Mutate L
            idx = int(rng.integers(l_size))
            mutated_val = L[idx] ^ random_pauli()
            candidate_L = list(L)
            candidate_L[idx] = mutated_val
            
            if len(E.gf2_basis(candidate_L)) != l_size:
                fails += 1
                continue
            
            candidate_S = get_S(candidate_L)
            if len(candidate_S) != s_size:
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