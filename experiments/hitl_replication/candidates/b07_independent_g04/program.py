import math

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    s = n - k + c_target
    r_L = 2 * n - s

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        dist = res.get("d")
        dist_val = dist if dist is not None else 0
        return 10000 * abs(res["c"] - c_target) + 100 * res["offending"] - dist_val

    def random_vector():
        while True:
            v = int(rng.integers(1, 1 << (2 * n)))
            if v > 0:
                return v

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    best_state = None
    best_score = 10**10

    while E.remaining:
        # Initialize L with r_L linearly independent vectors
        L = []
        while len(L) < r_L:
            v = random_vector()
            cand = L + [v]
            if len(E.gf2_basis(cand)) == len(cand):
                L.append(v)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur_score = objective(res)
        
        fails = 0
        temp = 100.0
        while fails < 1000 and E.remaining:
            temp = max(0.01, temp * 0.99)
            # Mutate L
            idx = int(rng.integers(r_L))
            old_v = L[idx]
            
            # Either replace with random or add another vector or add a small noise
            mut_type = rng.integers(3)
            if mut_type == 0:
                new_v = random_vector()
            elif mut_type == 1:
                other_idx = (idx + int(rng.integers(1, r_L))) % r_L
                new_v = old_v ^ L[other_idx]
            else:
                noise = 1 << int(rng.integers(2 * n))
                new_v = old_v ^ noise
            
            if new_v == 0:
                continue
                
            L[idx] = new_v
            if len(E.gf2_basis(L)) != r_L:
                L[idx] = old_v
                fails += 1
                continue
                
            cand_S = get_S(L)
            cand_res = E.evaluate(cand_S)
            cand_score = objective(cand_res)
            
            delta = cand_score - cur_score
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur_score = cand_score
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_v
                fails += 1

    return None