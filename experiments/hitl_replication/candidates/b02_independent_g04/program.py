import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_rank = n + k - c
    s = n - k + c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Generate a random independent basis L of size l_rank
        # We can start by generating a larger independent set and taking a subset
        L = []
        while len(L) < l_rank:
            cand = int(rng.integers(1, 1 << (2 * n)))
            test = L + [cand]
            if len(E.gf2_basis(test)) == len(test):
                L.append(cand)
        
        # Convert L to S
        dual_gens = [E._J(v, n) for v in L]
        S = list(E.nullspace(dual_gens, 2 * n))
        cur_eval = E.evaluate(S)
        cur = objective(cur_eval)
        if cur_eval.get("offending") == 0 and cur_eval.get("c") == c and cur_eval.get("k") == k:
            return S

        temp, fails = 30.0, 0
        while fails < 2000 and E.remaining:
            temp = max(0.1, temp * 0.998)
            candidate_L = list(L)
            idx = int(rng.integers(l_rank))
            # Mutate L by either XORing a random Pauli or adding another vector
            if rng.random() < 0.5:
                candidate_L[idx] ^= random_pauli()
            else:
                other = int(rng.integers(l_rank))
                if other != idx:
                    candidate_L[idx] ^= candidate_L[other]
                    
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
                
            dual_gens = [E._J(v, n) for v in candidate_L]
            candidate_S = list(E.nullspace(dual_gens, 2 * n))
            if len(candidate_S) != s:
                fails += 1
                continue
                
            new_eval = E.evaluate(candidate_S)
            new_obj = objective(new_eval)
            
            if new_eval.get("offending") == 0 and new_eval.get("c") == c and new_eval.get("k") == k:
                return candidate_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None