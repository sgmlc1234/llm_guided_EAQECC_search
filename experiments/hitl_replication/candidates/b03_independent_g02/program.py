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

    def random_element():
        return int(rng.integers(1, 1 << (2 * n)))

    def get_S(L):
        rows = [E._J(w, n) for w in L]
        return E.nullspace(rows, 2 * n)

    while E.remaining:
        # Generate a valid initial L
        L = []
        while len(L) < l:
            cand = random_element()
            test = L + [cand]
            if len(E.gf2_basis(test)) == len(test):
                L.append(cand)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp = 30.0
        fails = 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(l))
            old_val = L[idx]
            
            # Mutate
            if rng.random() < 0.3:
                L[idx] = random_element()
            else:
                # small mutation
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                L[idx] ^= delta
                
            if len(E.gf2_basis(L)) != l:
                L[idx] = old_val
                fails += 1
                continue
                
            S = get_S(L)
            new_obj = objective(E.evaluate(S))
            delta_val = new_obj - cur
            if delta_val <= 0 or rng.random() < math.exp(-delta_val / temp):
                cur = new_obj
                fails = 0 if delta_val < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
    return None