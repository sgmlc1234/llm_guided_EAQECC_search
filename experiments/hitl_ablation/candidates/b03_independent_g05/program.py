import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    dim_L = 2 * n - s  # this is 4 for the training cases

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        # prioritize getting offending = 0, then matching c, then maximizing d
        penalty_c = 10000 * abs(res["c"] - c)
        penalty_off = 1000 * res["offending"]
        d = res.get("d")
        bonus_d = (target["d"] - d) * 100 if d is not None else 1000
        return penalty_c + penalty_off + bonus_d

    def get_L_rank(L):
        return len(E.gf2_basis(L))

    def L_to_S(L):
        # Convert L to S via symplectic orthogonal complement
        # J(v) swaps X and Z bits. E.nullspace computes binary orthogonality.
        orth = [E._J(v, n) for v in L]
        return E.nullspace(orth, 2 * n)

    # Initialize L
    L = []
    while len(L) < dim_L:
        cand = int(rng.integers(1, 1 << (2 * n)))
        test_L = L + [cand]
        if get_L_rank(test_L) == len(test_L):
            L.append(cand)

    S = L_to_S(L)
    cur_res = E.evaluate(S)
    cur_obj = objective(cur_res)

    temp = 50.0
    fails = 0

    while E.remaining:
        temp = max(0.01, temp * 0.998)
        # Mutate L
        idx = int(rng.integers(dim_L))
        old_val = L[idx]
        
        # Try a few mutations until we find one that maintains rank and improves or is accepted
        for _ in range(10):
            # mutate by adding a small perturbation or random Pauli
            mutation = int(rng.integers(1, 1 << (2 * n)))
            new_val = old_val ^ mutation
            if new_val == 0:
                continue
            
            cand_L = list(L)
            cand_L[idx] = new_val
            if get_L_rank(cand_L) != dim_L:
                continue
                
            cand_S = L_to_S(cand_L)
            if len(cand_S) != s:
                continue
                
            res = E.evaluate(cand_S)
            obj = objective(res)
            
            delta = obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L = cand_L
                cur_obj = obj
                fails = 0
                break
        else:
            fails += 1
            if fails > 300:
                # Restart with a new random L
                L = []
                while len(L) < dim_L:
                    cand = int(rng.integers(1, 1 << (2 * n)))
                    test_L = L + [cand]
                    if get_L_rank(test_L) == len(test_L):
                        L.append(cand)
                S = L_to_S(L)
                cur_obj = objective(E.evaluate(S))
                temp = 50.0
                fails = 0

    return None