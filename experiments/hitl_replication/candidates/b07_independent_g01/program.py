import math
import numpy as np

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    s = n - k + c_target
    l = n + k - c_target

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def random_vector():
        val = 0
        for i in range(2 * n):
            if rng.random() < 0.25:
                val |= (1 << i)
        if val == 0:
            val = int(rng.integers(1, 1 << (2 * n)))
        return val

    while E.remaining:
        # Generate a random linearly independent basis L of size l
        L = []
        while len(L) < l:
            v = random_vector()
            if len(E.gf2_basis(L + [v])) == len(L) + 1:
                L.append(v)
        
        S_gens = get_S(L)
        cur = objective(E.evaluate(S_gens))
        
        temp = 30.0
        fails = 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            # Mutate one vector in L
            idx = int(rng.integers(l))
            old_v = L[idx]
            
            # Apply a mutation: either a small perturbation or a brand new vector
            if rng.random() < 0.5:
                new_v = old_v ^ int(rng.integers(1, 1 << (2 * n)) & ((1 << int(rng.integers(1, 5))) - 1))
            else:
                new_v = random_vector()
                
            if new_v == 0 or new_v == old_v:
                continue
                
            L_cand = list(L)
            L_cand[idx] = new_v
            if len(E.gf2_basis(L_cand)) != l:
                fails += 1
                continue
                
            S_cand = get_S(L_cand)
            new_obj = objective(E.evaluate(S_cand))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = L_cand, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None