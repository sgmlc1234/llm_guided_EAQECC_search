import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return list(E.nullspace(rows, 2 * n))

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    while E.remaining:
        # Generate a valid initial L of rank l
        L = []
        while len(L) < l:
            v = random_vector()
            cand = L + [v]
            if len(E.gf2_basis(cand)) == len(cand):
                L.append(v)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(l))
            old_v = L[idx]
            
            # Mutate: either completely random or small perturbation
            if rng.random() < 0.5:
                L[idx] = random_vector()
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