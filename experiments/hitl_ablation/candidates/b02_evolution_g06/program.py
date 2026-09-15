import math
import numpy as np

def search(target, max_evals):
    n = target[
        "n"
    ]  
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
        d_penalty = (
            1000 * max(0, d_target - d_val)
            if d_val is not None
            else 1000 * d_target
        )
        return 5000 * c_diff + off + d_penalty

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
        L = []
        while len(L) < l_rank:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)

        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp = 20.0
        fails = 0

        while fails < 300 and E.remaining:
            temp = max(0.01, temp * 0.99)
            candidate_L = list(L)
            idx = int(rng.integers(l_rank))

            r = rng.random()
            if r < 0.3:
                candidate_L[idx] = random_pauli()
            elif r < 0.6:
                candidate_L[idx] ^= random_pauli()
            else:
                other = int(rng.integers(l_rank))
                if other != idx:
                    candidate_L[idx] ^= candidate_L[other]
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

    return E.incumbent
