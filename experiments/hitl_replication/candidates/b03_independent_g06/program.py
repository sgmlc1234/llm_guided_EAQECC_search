import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_size = n + k - c

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

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
        # Initialize L with random independent elements
        L = []
        while len(L) < L_size:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 2000 and E.remaining:
            temp = max(0.05, temp * 0.995)
            cand_L = list(L)
            idx = int(rng.integers(L_size))
            if rng.random() < 0.3:
                # Mix with another row
                other = int(rng.integers(L_size))
                if other != idx:
                    cand_L[idx] ^= cand_L[other]
            else:
                # Mutate with a random local Pauli
                cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != L_size:
                fails += 1
                continue
            
            cand_S = get_S(cand_L)
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None