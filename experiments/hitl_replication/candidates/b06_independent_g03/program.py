import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_size = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        # prioritize target c and zero offending
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    # Initialize random L of size L_size with independent vectors
    def random_L():
        while True:
            L = []
            for _ in range(L_size):
                val = int(rng.integers(1, 1 << (2 * n)))
                L.append(val)
            if len(E.gf2_basis(L)) == L_size:
                return L

    L = random_L()
    S = get_S(L)
    best_obj = objective(E.evaluate(S))

    temp = 30.0
    fails = 0
    while E.remaining:
        if fails > 200:
            L = random_L()
            S = get_S(L)
            best_obj = objective(E.evaluate(S))
            fails = 0
            temp = 30.0

        temp = max(0.1, temp * 0.995)
        new_L = list(L)
        idx = int(rng.integers(L_size))
        # Mutate one element
        new_L[idx] ^= int(rng.integers(1, 1 << (2 * n)))
        if len(E.gf2_basis(new_L)) != L_size:
            fails += 1
            continue

        new_S = get_S(new_L)
        if len(new_S) != s:
            fails += 1
            continue

        new_obj = objective(E.evaluate(new_S))
        delta = new_obj - best_obj
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = new_L
            best_obj = new_obj
            if delta < 0:
                fails = 0
            else:
                fails += 1
        else:
            fails += 1

    return None