import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    dim_L = 2 * n - s  # which is n + k - c, equals 4 for training cases

    def get_S(L):
        # Convert L to S using the nullspace of J(L)
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

    # Initialize L as a random linearly independent set of size dim_L
    def random_L():
        while True:
            candidate = []
            for _ in range(dim_L):
                candidate.append(int(rng.integers(1, 1 << (2 * n))))
            if len(E.gf2_basis(candidate)) == dim_L:
                return candidate

    best_L = None
    best_val = 10**9

    while E.remaining:
        L = random_L()
        S = get_S(L)
        if len(S) != s:
            continue
        res = E.evaluate(S)
        cur = objective(res)
        if cur < best_val:
            best_val = cur
            best_L = list(L)

        temp = 30.0
        fails = 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = list(L)
            idx = int(rng.integers(dim_L))
            cand_L[idx] ^= random_pauli()
            if len(E.gf2_basis(cand_L)) != dim_L:
                fails += 1
                continue
            cand_S = get_S(cand_L)
            if len(cand_S) != s:
                fails += 1
                continue
            new_res = E.evaluate(cand_S)
            new_obj = objective(new_res)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
                if cur < best_val:
                    best_val = cur
                    best_L = list(L)
            else:
                fails += 1

    return None