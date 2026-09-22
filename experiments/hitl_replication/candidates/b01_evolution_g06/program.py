import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    dim_L = n + k - c

    def get_S(L):
        eqs = [E._J(v, n) for v in L]
        return E.nullspace(eqs, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 1e9
        c_diff = abs(res["c"] - c)
        off = res["offending"]
        d = res.get("d", 0) or 0
        return c_diff * 10000 + off * 100 - d

    def random_vector():
        val = 0
        for q in range(n):
            val |= int(rng.integers(0, 4)) << (2 * q)
        return val

    def random_L():
        while True:
            candidate = [random_vector() for _ in range(dim_L)]
            if len(E.gf2_basis(candidate)) == dim_L:
                return candidate

    def mutate(parent_L):
        new_L = list(parent_L)
        mut_idx = int(rng.integers(dim_L))
        r = rng.random()
        if r < 0.5:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            for q in qubits:
                new_L[mut_idx] ^= int(rng.integers(1, 4)) << (2 * int(q))
        else:
            new_L[mut_idx] = random_vector()
        return new_L

    best_S = None
    best_obj = 1e9

    while E.remaining:
        L = random_L()
        S = get_S(L)
        res = E.evaluate(S)
        cur_obj = objective(res)
        
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target["d"]:
            return S
        if cur_obj < best_obj:
            best_obj = cur_obj
            best_S = S

        temp = 10.0
        fails = 0
        
        while E.remaining and fails < 150:
            temp = max(0.01, temp * 0.99)
            # Try a few mutations and pick the best one to make high-quality steps
            candidates = []
            for _ in range(3):
                cand_L = mutate(L)
                if len(E.gf2_basis(cand_L)) == dim_L:
                    candidates.append(cand_L)
            
            if not candidates:
                continue
                
            best_cand_L = None
            best_cand_obj = 1e9
            best_cand_res = None
            
            for cand_L in candidates:
                cand_S = get_S(cand_L)
                cand_res = E.evaluate(cand_S)
                cand_obj = objective(cand_res)
                if cand_res.get("offending") == 0 and cand_res.get("c") == c and cand_res.get("d", 0) >= target["d"]:
                    return cand_S
                if cand_obj < best_cand_obj:
                    best_cand_obj = cand_obj
                    best_cand_L = cand_L
                    best_cand_res = cand_res
            
            delta = best_cand_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L = best_cand_L
                cur_obj = best_cand_obj
                fails = 0
                if cur_obj < best_obj:
                    best_obj = cur_obj
                    best_S = get_S(L)
            else:
                fails += 1

    return best_S
