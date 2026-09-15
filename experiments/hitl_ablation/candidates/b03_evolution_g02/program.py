import math
import numpy as np

def search(target, max_evals):
    n, k, c, target_d = target["n"], target["k"], target["c"], target["d"]
    r = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 10000 * abs(res["c"] - c) + 1000 * res["offending"]
        d = res.get("d")
        if d is not None:
            val += 100 * max(0, target_d - d)
        else:
            val += 500
        return val

    def mutate(L_copy):
        idx = int(rng.integers(r))
        p = rng.random()
        if p < 0.6:
            # 1-qubit flip
            q = int(rng.integers(n))
            L_copy[idx] ^= int(rng.integers(1, 4)) << (2 * q)
        elif p < 0.85:
            # Linear combination
            other = int(rng.integers(r))
            if other != idx:
                L_copy[idx] ^= L_copy[other]
        else:
            # 2-qubit flip
            qubits = rng.choice(n, size=2, replace=False)
            for q in qubits:
                L_copy[idx] ^= int(rng.integers(1, 4)) << (2 * int(q))

    def get_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    while E.remaining:
        # Initialize L
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

        temp = 40.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.2, temp * 0.996)
            cand_L = list(L)
            mutate(cand_L)
            
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