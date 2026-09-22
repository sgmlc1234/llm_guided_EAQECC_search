import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    l_size = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        num_qubits = int(rng.choice([1, 2, 3], p=[0.6, 0.3, 0.1]))
        qubits = rng.choice(n, size=min(num_qubits, n), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def init_L():
        L = []
        while len(L) < l_size:
            v = int(rng.integers(1, 1 << (2 * n)))
            candidate = L + [v]
            if len(E.gf2_basis(candidate)) == len(candidate):
                L.append(v)
        return L

    L = init_L()
    S = get_S(L)
    cur = objective(E.evaluate(S))

    temp = 30.0
    fails = 0
    best_L = list(L)
    best_obj = cur

    while E.remaining:
        temp = max(0.01, temp * 0.995)
        idx = int(rng.integers(l_size))
        old_val = L[idx]

        if rng.random() < 0.10:
            L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            L[idx] ^= random_pauli()

        if len(E.gf2_basis(L)) != l_size:
            L[idx] = old_val
            fails += 1
            if fails > 150:
                L = init_L()
                cur = objective(E.evaluate(get_S(L)))
                fails = 0
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
            fails = 0
        else:
            L[idx] = old_val
            fails += 1
            if fails > 150:
                L = init_L()
                cur = objective(E.evaluate(get_S(L)))
                fails = 0

    return None