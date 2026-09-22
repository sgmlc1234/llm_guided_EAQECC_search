import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_size = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c) + 100 * res["offending"]
        if res.get("d") is not None:
            val += 10 * max(0, target["d"] - res["d"])
        return val

    def random_vector():
        return int(rng.integers(0, 1 << (2 * n)))

    while E.remaining:
        # Generate a valid initial L
        L = []
        while len(L) < l_size:
            v = random_vector()
            temp = L + [v]
            if len(E.gf2_basis(temp)) == len(temp):
                L.append(v)
        
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur_res = E.evaluate(S)
        cur = objective(cur_res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate = list(L)
            idx = int(rng.integers(l_size))
            if rng.random() < 0.5:
                candidate[idx] ^= random_vector()
            else:
                candidate[idx] = random_vector()
                
            if len(E.gf2_basis(candidate)) != l_size:
                fails += 1
                continue
                
            S_cand = E.nullspace([E._J(v, n) for v in candidate], 2 * n)
            new_res = E.evaluate(S_cand)
            new_obj = objective(new_res)
            
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None