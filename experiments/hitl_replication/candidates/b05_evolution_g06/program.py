import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    r = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 10000 * abs(res["c"] - c) + 100 * res["offending"]
        d_val = res.get("d")
        if d_val is not None:
            val += max(0, target["d"] - d_val) * 10
        return val

    def random_vector():
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    while E.remaining:
        L = []
        while len(L) < r:
            v = random_vector()
            temp = L + [v]
            if len(E.gf2_basis(temp)) == len(temp):
                L.append(v)
        
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != s:
            continue
        
        cur_obj = objective(E.evaluate(S))
        temp, fails = 20.0, 0
        
        while fails < 250 and E.remaining:
            temp = max(0.05, temp * 0.99)
            
            idx = int(rng.integers(r))
            old_val = L[idx]
            
            if rng.random() < 0.15:
                # Add another basis vector
                other = int(rng.integers(r))
                if other != idx:
                    L[idx] ^= L[other]
            else:
                # Local qubit mutation
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
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
                
            new_obj = objective(E.evaluate(cand_S))
            diff = new_obj - cur_obj
            if diff <= 0 or rng.random() < math.exp(-diff / temp):
                cur_obj = new_obj
                fails = 0 if diff < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
    return None