import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    d_target = target["d"]
    l_rank = n + k - c_target

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        off = res["offending"]
        c_diff = abs(res["c"] - c_target)
        d_val = res.get("d")
        if d_val is not None:
            d_penalty = 1000 * max(0, d_target - d_val)
        else:
            d_penalty = 1000 * d_target
        return 5000 * c_diff + off + d_penalty

    def random_pauli():
        # Favor smaller perturbations (1 or 2 qubits) to preserve structure
        r = rng.random()
        size = 1 if r < 0.65 else (2 if r < 0.9 else 3)
        size = min(size, n)
        qubits = rng.choice(n, size=size, replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    while E.remaining:
        # Initial construction of a linearly independent L
        L = []
        while len(L) < l_rank:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        best_L = list(L)
        best_obj = cur
        
        temp = 40.0
        fails = 0
        stagnant = 0

        while fails < 800 and E.remaining:
            temp = max(0.05, temp * 0.996)
            candidate_L = list(L)
            idx = int(rng.integers(l_rank))
            
            # Mutate L by either replacing or perturbing a generator
            if rng.random() < 0.4:
                candidate_L[idx] = random_pauli()
            else:
                candidate_L[idx] ^= random_pauli()

            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue

            S_cand = get_S(candidate_L)
            res = E.evaluate(S_cand)
            new_obj = objective(res)
            delta = new_obj - cur

            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                if new_obj < best_obj:
                    best_obj = new_obj
                    best_L = list(candidate_L)
                    stagnant = 0
                else:
                    stagnant += 1
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                stagnant += 1

            # If stuck, occasionally perturbation-jump from the best local minimum
            if stagnant > 120:
                L = list(best_L)
                # Perturb one element randomly to escape local minimum
                pidx = int(rng.integers(l_rank))
                L[pidx] ^= random_pauli()
                if len(E.gf2_basis(L)) == l_rank:
                    S_cand = get_S(L)
                    cur = objective(E.evaluate(S_cand))
                else:
                    L = list(best_L)
                    cur = best_obj
                stagnant = 0
                temp = min(30.0, temp * 1.3)

    return None