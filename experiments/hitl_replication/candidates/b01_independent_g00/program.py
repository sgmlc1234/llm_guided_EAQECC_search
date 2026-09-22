import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    s = n - k + target_c
    l = n + k - target_c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target_c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        L = []
        while len(L) < l:
            v = int(rng.integers(1, 1 << (2 * n)))
            if len(E.gf2_basis(L + [v])) == len(L) + 1:
                L.append(v)
        
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate = list(L)
            idx = int(rng.integers(l))
            if rng.random() < 0.2:
                candidate[idx] = int(rng.integers(1, 1 << (2 * n)))
            else:
                candidate[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate)) != l:
                fails += 1
                continue
                
            S_cand = E.nullspace([E._J(v, n) for v in candidate], 2 * n)
            new_val = objective(E.evaluate(S_cand))
            delta = new_val - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate, new_val
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None