import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_rank = n + k - c  # For both training targets, l_rank is 4

    def get_S(L):
        # Convert L to S using the dual relation
        # S is the symplectic dual of L, so we take nullspace of J(L)
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # Penalize difference in c and non-zero offending count
        return 5000 * abs(res["c"] - c) + res["offending"]

    # Generate initial linearly independent L
    def random_L():
        while True:
            candidate = []
            for _ in range(l_rank):
                # Generate a non-zero random Pauli
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == l_rank:
                return candidate

    L = random_L()
    S = get_S(L)
    best_val = objective(E.evaluate(S))

    while E.remaining:
        # Mutate L
        new_L = list(L)
        idx = int(rng.integers(l_rank))
        
        # Mutation options: replace with a new random Pauli, or modify few bits
        mutation_type = rng.integers(0, 3)
        if mutation_type == 0:
            # Completely new random Pauli
            new_val = int(rng.integers(1, 1 << (2 * n)))
            new_L[idx] = new_val
        elif mutation_type == 1:
            # XOR with another element
            other_idx = (idx + int(rng.integers(1, l_rank))) % l_rank
            new_L[idx] ^= new_L[other_idx]
        else:
            # Mutate active qubits
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            new_L[idx] ^= delta

        if len(E.gf2_basis(new_L)) != l_rank:
            continue

        new_S = get_S(new_L)
        res = E.evaluate(new_S)
        val = objective(res)
        
        if val <= best_val or rng.random() < math.exp((best_val - val) / 50.0):
            L = new_L
            best_val = val
            
        # Periodic restart to avoid local minima
        if rng.random() < 0.01:
            L = random_L()
            best_val = objective(E.evaluate(get_S(L)))

    return None
