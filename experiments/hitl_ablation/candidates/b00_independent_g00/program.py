import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_len = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_L_basis():
        while True:
            cand = [int(rng.integers(1, 1 << (2 * n))) for _ in range(L_len)]
            if len(E.gf2_basis(cand)) == L_len:
                return cand

    def L_to_S(L):
        dual_inputs = [E._J(v, n) for v in L]
        return E.nullspace(dual_inputs, 2 * n)

    while E.remaining:
        L = get_L_basis()
        S = L_to_S(L)
        if len(S) != s:
            continue
        cur = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(L_len))
            if rng.random() < 0.5:
                candidate_L[idx] ^= random_pauli()
            else:
                other_idx = int(rng.integers(L_len))
                if other_idx != idx:
                    candidate_L[idx] ^= candidate_L[other_idx]
            
            if len(E.gf2_basis(candidate_L)) != L_len:
                fails += 1
                continue
                
            candidate_S = L_to_S(candidate_L)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(candidate_S)
            new_obj = objective(res)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None