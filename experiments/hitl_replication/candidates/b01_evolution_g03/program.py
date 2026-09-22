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
            return 10**9
        c_diff = abs(res["c"] - c)
        off = res["offending"]
        d = res.get("d")
        d_val = d if d is not None else 0
        # Prefer c == target["c"], then off == 0, then maximize d
        return c_diff * 10000 + off * 1000 - d_val

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

    best_L = random_L()
    best_S = get_S(best_L)
    best_res = E.evaluate(best_S)
    best_obj = objective(best_res)
    
    L = list(best_L)
    cur_obj = best_obj
    
    tabu = set()
    fails = 0
    
    while E.remaining:
        # Select mutation strategy
        new_L = list(L)
        idx = int(rng.integers(dim_L))
        
        r = rng.random()
        if r < 0.4:
            # Local mutation: flip 1 or 2 qubits in one vector
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            for q in qubits:
                new_L[idx] ^= int(rng.integers(1, 4)) << (2 * int(q))
        elif r < 0.8:
            # Add a sparse vector to one of the basis vectors
            v = 0
            for _ in range(int(rng.integers(1, 3))):
                v |= int(rng.integers(1, 4)) << (2 * int(rng.integers(n)))
            new_L[idx] ^= v
        else:
            # Replace one basis vector entirely
            new_L[idx] = random_vector()
            
        if len(E.gf2_basis(new_L)) != dim_L:
            continue
            
        state_key = tuple(sorted(new_L))
        if state_key in tabu:
            continue
            
        new_S = get_S(new_L)
        res = E.evaluate(new_S)
        new_obj = objective(res)
        
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target["d"]:
            return new_S
            
        if new_obj <= cur_obj or rng.random() < math.exp(-(new_obj - cur_obj) / 2.0):
            L = new_L
            cur_obj = new_obj
            tabu.add(state_key)
            if len(tabu) > 1000:
                tabu.clear()
            if new_obj < best_obj:
                best_obj = new_obj
                best_L = list(new_L)
                fails = 0
        else:
            fails += 1
            
        if fails > 120:
            # Backtrack or restart
            if rng.random() < 0.5:
                L = list(best_L)
                cur_obj = best_obj
            else:
                L = random_L()
                S = get_S(L)
                cur_obj = objective(E.evaluate(S))
            fails = 0
            
    return None