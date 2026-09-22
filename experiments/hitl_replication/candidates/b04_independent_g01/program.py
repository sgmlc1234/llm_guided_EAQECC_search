import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    def get_independent_L():
        while True:
            basis = []
            for _ in range(l_rank):
                for _ in range(50):
                    v = random_vector()
                    if len(E.gf2_basis(basis + [v])) == len(basis) + 1:
                        basis.append(v)
                        break
                else:
                    break
            if len(basis) == l_rank:
                return basis

    while E.remaining:
        L = get_independent_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != s:
            continue
        res = E.evaluate(S)
        cur = objective(res)
        if cur == 0 and res.get("d", 0) >= target["d"]:
            return S
            
        temp = 30.0
        fails = 0
        while fails < 500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(l_rank))
            old_v = L[idx]
            
            num_flips = int(rng.integers(1, 4))
            new_v = old_v
            for _ in range(num_flips):
                bit = int(rng.integers(2 * n))
                new_v ^= (1 << bit)
                
            if new_v == 0:
                fails += 1
                continue
                
            candidate_L = list(L)
            candidate_L[idx] = new_v
            
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
                
            candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(candidate_S)
            new_obj = objective(res)
            if new_obj == 0 and res.get("d", 0) >= target["d"]:
                return candidate_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L = candidate_L
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None