import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    s = n - k + c_target
    l_size = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    # Initialize L as a linearly independent basis of size l_size
    L = []
    while len(L) < l_size:
        v = int(rng.integers(1, 1 << (2 * n)))
        test_L = L + [v]
        if len(E.gf2_basis(test_L)) == len(test_L):
            L.append(v)

    S = get_S(L)
    cur = objective(E.evaluate(S))

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        candidate_L[idx] ^= random_pauli()
        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            if fails > 1000:
                # Restart search with a new random L
                L = []
                while len(L) < l_size:
                    v = int(rng.integers(1, 1 << (2 * n)))
                    test_L = L + [v]
                    if len(E.gf2_basis(test_L)) == len(test_L):
                        L.append(v)
                S = get_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
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