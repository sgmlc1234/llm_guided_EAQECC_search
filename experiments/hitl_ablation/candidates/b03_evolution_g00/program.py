import math
import numpy as np

def search(target, max_evals):
    n, k, c, target_d = target["n"], target["k"], target["c"], target["d"]
    # rank of L is n + k - c
    r = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c) + 100 * res["offending"]
        if res.get("d") is not None:
            val += 10 * max(0, target_d - res["d"])
        return val

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    # Initialize L
    while E.remaining:
        L = []
        while len(L) < r:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target_d:
            return S

        temp, fails = 40.0, 0
        while fails < 1200 and E.remaining:
            temp = max(0.1, temp * 0.996)
            cand_L = list(L)
            idx = int(rng.integers(r))
            if rng.random() < 0.3:
                # Mix with another element
                other = int(rng.integers(r))
                if other != idx:
                    cand_L[idx] ^= cand_L[other]
            cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != r:
                fails += 1
                continue
                
            cand_S = get_S(cand_L)
            cand_res = E.evaluate(cand_S)
            new_obj = objective(cand_res)
            
            if cand_res.get("offending") == 0 and cand_res.get("c") == c and cand_res.get("d", 0) >= target_d:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None