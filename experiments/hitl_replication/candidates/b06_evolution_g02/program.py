import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l = n + k - c
    s = n - k + c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        dist_gap = max(0, target["d"] - res.get("d", 0)) if res.get("d") is not None else target["d"]
        return 10000 * abs(res["c"] - c) + 1000 * res["offending"] + 100 * dist_gap

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return list(E.nullspace(rows, 2 * n))

    def random_vector():
        v = 0
        # Favor sparse but highly structured mutations: 1 to 3 qubits
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        for q in qubits:
            v |= int(rng.integers(1, 4)) << (2 * int(q))
        return v

    while E.remaining:
        L = []
        while len(L) < l and E.remaining:
            v = random_vector()
            cand = L + [v]
            if len(E.gf2_basis(cand)) == len(cand):
                L.append(v)
        if len(L) < l:
            break

        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        
        temp, fails = 30.0, 0
        while fails < 1200 and E.remaining:
            temp = max(0.01, temp * 0.995)
            idx = int(rng.integers(l))
            old_v = L[idx]
            
            r = rng.random()
            if r < 0.2:
                L[idx] = random_vector()
            elif r < 0.6:
                # Mutate by adding a small perturbation
                L[idx] ^= random_vector()
            else:
                # Mix with another basis element
                other = int(rng.integers(l))
                if other != idx:
                    L[idx] ^= L[other]
                else:
                    L[idx] ^= random_vector()
                
            if len(E.gf2_basis(L)) != l:
                L[idx] = old_v
                fails += 1
                continue
                
            S = get_S(L)
            res = E.evaluate(S)
            new_obj = objective(res)
            delta = new_obj - cur
            
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_v
                fails += 1
                
    return None