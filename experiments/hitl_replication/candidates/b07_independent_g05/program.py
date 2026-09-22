import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    m = n + k - target_c

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 10**9
        off = res["offending"]
        c_diff = abs(res["c"] - target_c)
        d_val = res.get("d")
        d_penalty = 10 * max(0, target["d"] - d_val) if d_val is not None else 100
        return 5000 * c_diff + 100 * off + d_penalty

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    def get_valid_L():
        while True:
            basis = []
            for _ in range(m):
                attempts = 0
                while attempts < 100:
                    cand = random_vector()
                    if len(E.gf2_basis(basis + [cand])) == len(basis) + 1:
                        basis.append(cand)
                        break
                    attempts += 1
            if len(basis) == m:
                return basis

    def L_to_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    best_L = get_valid_L()
    best_S = L_to_S(best_L)
    best_res = E.evaluate(best_S)
    best_obj = objective(best_res)

    while E.remaining:
        # Local search with restarts if stuck
        L = list(best_L)
        obj = best_obj
        temp = 10.0
        no_improvement = 0
        
        while no_improvement < 200 and E.remaining:
            temp = max(0.01, temp * 0.98)
            idx = int(rng.integers(m))
            old_val = L[idx]
            
            # Mutate
            attempts = 0
            while attempts < 50:
                mutant = old_val ^ random_vector()
                test_L = list(L)
                test_L[idx] = mutant
                if len(E.gf2_basis(test_L)) == m:
                    break
                attempts += 1
            else:
                continue
            
            S = L_to_S(test_L)
            res = E.evaluate(S)
            new_obj = objective(res)
            delta = new_obj - obj
            
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L[idx] = mutant
                obj = new_obj
                if obj < best_obj:
                    best_L = list(L)
                    best_obj = obj
                    no_improvement = 0
                else:
                    no_improvement += 1
            else:
                no_improvement += 1
                
        # Restart if objective is still not optimal
        if best_obj > 0 and E.remaining:
            best_L = get_valid_L()
            best_S = L_to_S(best_L)
            best_res = E.evaluate(best_S)
            best_obj = objective(best_res)
            
    return None