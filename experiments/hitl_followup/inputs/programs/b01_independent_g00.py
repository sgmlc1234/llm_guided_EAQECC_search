import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2*n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        L = []
        while len(L) < len_L:
            cand = int(rng.integers(1, 1 << (2*n)))
            test_L = L + [cand]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(cand)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
            if res.get("d") is not None and res["d"] >= target["d"]:
                return S
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(len_L))
            mutated_L = list(L)
            mutated_L[idx] ^= random_pauli()
            if len(E.gf2_basis(mutated_L)) != len_L:
                fails += 1
                continue
            
            S_cand = get_S(mutated_L)
            res_cand = E.evaluate(S_cand)
            new_obj = objective(res_cand)
            
            if res_cand.get("offending") == 0 and res_cand.get("c") == c and res_cand.get("k") == k:
                if res_cand.get("d") is not None and res_cand["d"] >= target["d"]:
                    return S_cand

            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = mutated_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None