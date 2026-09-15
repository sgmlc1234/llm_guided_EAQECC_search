import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = n + k - c

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

    def get_S(L):
        # Apply Symplectic map to L for nullspace calculation
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    while E.remaining:
        # Generate a random initial independent L of size len_L
        L = []
        while len(L) < len_L:
            candidate_vec = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate_vec]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate_vec)

        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0

        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(len_L))
            candidate_L[idx] ^= random_pauli()

            if len(E.gf2_basis(candidate_L)) != len_L:
                fails += 1
                continue

            candidate_S = get_S(candidate_L)
            new_obj = objective(E.evaluate(candidate_S))
            delta = new_obj - cur

            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None