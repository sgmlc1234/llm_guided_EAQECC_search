import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        # Generate a random integer representing a Pauli on n qubits
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def mutate(L):
        L_new = list(L)
        idx = int(rng.integers(l_size))
        # Mutate by either replacing or adding a random Pauli
        if rng.random() < 0.3:
            L_new[idx] = random_vector()
        else:
            # Add a random sparse Pauli
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            L_new[idx] ^= delta
        return L_new

    def L_to_S(L):
        # Symplectic dual computation
        # E._J(v, n) swaps X and Z components of v
        eqs = [E._J(v, n) for v in L]
        return E.nullspace(eqs, 2 * n)

    best_L = None
    best_val = 10**9

    # Restart loop
    while E.remaining:
        # Initialize a valid random basis L of size l_size
        L = []
        while len(L) < l_size:
            candidate = random_vector()
            temp = L + [candidate]
            if len(E.gf2_basis(temp)) == len(temp):
                L.append(candidate)
        
        S = L_to_S(L)
        cur_val = objective(E.evaluate(S))
        if cur_val < best_val:
            best_val = cur_val
            best_L = list(L)

        temp = 30.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = mutate(L)
            if len(E.gf2_basis(cand_L)) != l_size:
                fails += 1
                continue
            
            cand_S = L_to_S(cand_L)
            new_val = objective(E.evaluate(cand_S))
            delta = new_val - cur_val
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_val = cand_L, new_val
                fails = 0 if delta < 0 else fails + 1
                if cur_val < best_val:
                    best_val = cur_val
                    best_L = list(L)
            else:
                fails += 1
                
    return None