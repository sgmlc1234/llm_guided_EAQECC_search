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

    def random_vector(weight=None):
        v = 0
        if weight is None:
            weight = int(rng.integers(1, 4))
        qubits = rng.choice(n, size=weight, replace=False)
        for q in qubits:
            v |= int(rng.integers(1, 4)) << (2 * int(q))
        return v

    best_L = None
    best_obj = 10**9

    while E.remaining:
        # Generate initial valid basis L
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
        if cur < best_obj:
            best_obj = cur
            best_L = list(L)

        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.01, temp * 0.995)
            
            # More frequent backtracking to the best known L
            if fails > 0 and fails % 150 == 0 and best_L is not None:
                L = list(best_L)
                cur = best_obj

            idx = int(rng.integers(l))
            old_v = L[idx]
            
            r = rng.random()
            if r < 0.4:
                # Small perturbation: 1 qubit mutation
                L[idx] ^= random_vector(weight=1)
            elif r < 0.7:
                # Medium perturbation
                L[idx] ^= random_vector()
            else:
                # Mix with another basis element
                other = int(rng.integers(l))
                if other != idx:
                    L[idx] ^= L[other]
                else:
                    L[idx] ^= random_vector(weight=1)
                
            if len(E.gf2_basis(L)) != l:
                L[idx] = old_v
                fails += 1
                continue
                
            S = get_S(L)
            res = E.evaluate(S)
            new_obj = objective(res)
            
            if new_obj < best_obj:
                best_obj = new_obj
                best_L = list(L)

            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_v
                fails += 1
                
    return None