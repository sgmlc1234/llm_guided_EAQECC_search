import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    s = n - target["k"] + target["c"]
    L_size = 2 * n - s

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target["c"]) + res["offending"]

    def get_random_L():
        while True:
            candidates = []
            for _ in range(L_size):
                candidates.append(int(rng.integers(1, 1 << (2 * n))))
            if len(E.gf2_basis(candidates)) == L_size:
                return candidates

    L = get_random_L()
    S_gens = E.nullspace([E._J(v, n) for v in L], 2 * n)
    best_obj = 10**9
    if len(S_gens) == s:
        best_obj = objective(E.evaluate(S_gens))

    temp = 10.0
    fails = 0
    while E.remaining:
        temp = max(0.05, temp * 0.999)
        new_L = list(L)
        idx = int(rng.integers(L_size))
        mut_type = rng.integers(3)
        if mut_type == 0:
            new_L[idx] = int(rng.integers(1, 1 << (2 * n)))
        elif mut_type == 1:
            new_L[idx] ^= int(rng.integers(1, 1 << (2 * n)))
        else:
            other = int(rng.integers(L_size))
            if other != idx:
                new_L[idx] ^= new_L[other]
            else:
                new_L[idx] ^= int(rng.integers(1, 1 << (2 * n)))

        if len(E.gf2_basis(new_L)) != L_size:
            continue

        new_S = E.nullspace([E._J(v, n) for v in new_L], 2 * n)
        if len(new_S) != s:
            continue

        new_obj = objective(E.evaluate(new_S))
        delta = new_obj - best_obj
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = new_L
            best_obj = new_obj
            fails = 0
        else:
            fails += 1
            if fails > 500:
                L = get_random_L()
                new_S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                if len(new_S) == s:
                    best_obj = objective(E.evaluate(new_S))
                else:
                    best_obj = 10**9
                fails = 0
                temp = 10.0
    return None