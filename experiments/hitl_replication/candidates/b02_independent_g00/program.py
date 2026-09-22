import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_rank = n + k - c
    s_rank = n - k + c

    def get_S(L):
        # Convert L to S via symplectic nullspace
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    # Initialize L of correct rank
    while E.remaining:
        L = []
        while len(L) < l_rank:
            v = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)
        S = get_S(L)
        if len(S) == s_rank:
            cur_eval = E.evaluate(S)
            cur = objective(cur_eval)
            break
    else:
        return None

    temp = 30.0
    fails = 0
    while E.remaining and fails < 3000:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(l_rank))
        
        # Mutate L
        if rng.random() < 0.5:
            candidate_L[idx] ^= random_pauli()
        else:
            other = int(rng.integers(l_rank))
            if other != idx:
                candidate_L[idx] ^= candidate_L[other]
                if rng.random() < 0.5:
                    candidate_L[idx] ^= random_pauli()
            else:
                candidate_L[idx] ^= random_pauli()

        if len(E.gf2_basis(candidate_L)) != l_rank:
            fails += 1
            continue

        candidate_S = get_S(candidate_L)
        if len(candidate_S) != s_rank:
            fails += 1
            continue

        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1

        if cur == 0 and res.get("offending") == 0:
            break

    return None