import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    r = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    best_S = None
    best_obj = 10**9

    while E.remaining:
        # Initialize L of rank r
        L = []
        while len(L) < r:
            v = random_vector()
            temp = L + [v]
            if len(E.gf2_basis(temp)) == len(temp):
                L.append(v)
        
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != s:
            continue
        
        res = E.evaluate(S)
        cur_obj = objective(res)
        if cur_obj < best_obj:
            best_obj = cur_obj
            best_S = S
        
        temp, fails = 40.0, 0
        
        # Use a smaller fail limit for faster restarts to avoid local minima
        while fails < 350 and E.remaining:
            temp = max(0.05, temp * 0.992)
            # Mutate L
            idx = int(rng.integers(r))
            old_val = L[idx]
            
            # Multi-scale perturbation
            qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            
            L[idx] ^= delta
            if len(E.gf2_basis(L)) != r:
                L[idx] = old_val
                fails += 1
                continue
            
            cand_S = E.nullspace([E._J(v, n) for v in L], 2 * n)
            if len(cand_S) != s:
                L[idx] = old_val
                fails += 1
                continue
                
            eval_res = E.evaluate(cand_S)
            new_obj = objective(eval_res)
            
            if new_obj < best_obj:
                best_obj = new_obj
                best_S = cand_S
                
            diff = new_obj - cur_obj
            if diff <= 0 or rng.random() < math.exp(-diff / temp):
                cur_obj = new_obj
                fails = 0 if diff < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
                
    return best_S
