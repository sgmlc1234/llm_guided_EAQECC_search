import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    l_rank = n + k - c_target

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # Primary goal: c matches and offending is 0
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    while E.remaining:
        # Generate a valid initial L of rank l_rank
        L = []
        while len(L) < l_rank:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp = 30.0
        fails = 0

        while fails < 1000 and E.remaining:
            temp = max(0.05, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l_rank))
            
            # Mutate: either replace or XOR with random Pauli
            if rng.random() < 0.5:
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
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None