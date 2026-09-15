import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    r = n + k - c  # Rank of L is 4 for the training targets
    
    def get_S(L):
        # Convert L to S via symplectic dual
        # S = nullspace(J(L))
        eqs = [E._J(v, n) for v in L]
        return E.nullspace(eqs, 2 * n)
    
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

    # Initialize L as a independent set of size r
    # We can start by generating random vectors and checking independence
    def generate_random_L():
        while True:
            candidate = []
            for _ in range(r):
                # Generate a non-zero random vector
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == r:
                return candidate

    while E.remaining:
        L = generate_random_L()
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
            return S

        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(r))
            old_val = L[idx]
            
            # Mutate L[idx]
            mutant_val = old_val ^ random_pauli()
            if mutant_val == 0:
                fails += 1
                continue
                
            L[idx] = mutant_val
            if len(E.gf2_basis(L)) != r:
                L[idx] = old_val
                fails += 1
                continue
                
            S = get_S(L)
            res = E.evaluate(S)
            new_obj = objective(res)
            
            if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
                return S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else: 
                L[idx] = old_val
                fails += 1
                
    return None