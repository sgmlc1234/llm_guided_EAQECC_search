import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # prioritize reaching the correct c first, then minimizing offending
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_random_L():
        while True:
            candidate = [int(rng.integers(0, 1 << (2 * n))) for _ in range(l_rank)]
            if len(E.gf2_basis(candidate)) == l_rank:
                return candidate

    while E.remaining:
        L = get_random_L()
        S_cand = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S_cand) != s:
            continue
        
        cur_res = E.evaluate(S_cand)
        cur_val = objective(cur_res)
        if cur_res.get("offending") == 0 and cur_res.get("c") == c and cur_res.get("k") == k:
            return S_cand
            
        temp = 100.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.99)
            idx = int(rng.integers(0, l_rank))
            # Mutate L by XORing with a random Pauli or replacing
            mut_type = rng.integers(0, 2)
            new_L = list(L)
            if mut_type == 0:
                new_L[idx] ^= int(rng.integers(1, 1 << (2 * n)))
            else:
                new_L[idx] = int(rng.integers(1, 1 << (2 * n)))
                
            if len(E.gf2_basis(new_L)) != l_rank:
                fails += 1
                continue
                
            S_cand = E.nullspace([E._J(v, n) for v in new_L], 2 * n)
            if len(S_cand) != s:
                fails += 1
                continue
                
            res = E.evaluate(S_cand)
            val = objective(res)
            if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
                return S_cand
                
            delta = val - cur_val
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L = new_L
                cur_val = val
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None