import math
import numpy as np

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    l_dim = n + k - c_target
    s_dim = n - k + c_target

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 10**9
        off = res["offending"]
        c_val = res["c"]
        d_val = res.get("d")
        d_err = max(0, target["d"] - d_val) if d_val is not None else target["d"]
        return 10000 * off + 1000 * abs(c_val - c_target) + d_err

    def get_independent_L():
        while True:
            candidate = []
            for _ in range(l_dim):
                val = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == l_dim:
                return candidate

    while E.remaining:
        L = get_independent_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != s_dim:
            continue
        res = E.evaluate(S)
        cur_obj = objective(res)
        
        fails = 0
        temp = 10.0
        while fails < 200 and E.remaining:
            temp = max(0.01, temp * 0.98)
            new_L = list(L)
            idx = int(rng.integers(l_dim))
            # Mutate one element of L
            for _ in range(10):
                v = int(rng.integers(1, 1 << (2 * n)))
                new_L[idx] = v
                if len(E.gf2_basis(new_L)) == l_dim:
                    break
            else:
                continue
            
            new_S = E.nullspace([E._J(v, n) for v in new_L], 2 * n)
            if len(new_S) != s_dim:
                fails += 1
                continue
            
            new_res = E.evaluate(new_S)
            new_obj = objective(new_res)
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = new_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None