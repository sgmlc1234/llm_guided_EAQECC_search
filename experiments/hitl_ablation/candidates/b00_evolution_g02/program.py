import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    r_L = n + k - c
    s = n - k + c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c) + 10 * res["offending"]
        d = res.get("d")
        if d is not None:
            val -= d
        return val

    def get_S(L):
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    def random_vector():
        val = 0
        while val == 0:
            for i in range(n):
                val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def mutate_vector(v):
        v_new = v
        num_muts = int(rng.choice([1, 2], p=[0.7, 0.3]))
        for _ in range(num_muts):
            q = int(rng.integers(0, n))
            op = int(rng.integers(1, 4))
            v_new ^= (op << (2 * q))
        return v_new

    def init_L():
        while True:
            candidate_L = [random_vector() for _ in range(r_L)]
            if len(E.gf2_basis(candidate_L)) == r_L:
                return candidate_L

    L = init_L()
    S = get_S(L)
    best_res = E.evaluate(S)
    best_obj = objective(best_res)

    temp = 20.0
    fails = 0

    while E.remaining:
        if fails > 300:
            L = init_L()
            S = get_S(L)
            best_res = E.evaluate(S)
            best_obj = objective(best_res)
            temp = 20.0
            fails = 0
            continue

        new_L = list(L)
        mut_idx = int(rng.integers(r_L))
        if rng.random() < 0.15:
            new_L[mut_idx] = random_vector()
        else:
            new_L[mut_idx] = mutate_vector(new_L[mut_idx])

        if len(E.gf2_basis(new_L)) != r_L:
            fails += 1
            continue

        new_S = get_S(new_L)
        if len(new_S) != s:
            continue

        res = E.evaluate(new_S)
        obj = objective(res)

        delta = obj - best_obj
        temp = max(0.01, temp * 0.996)
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = new_L
            best_obj = obj
            if delta < 0:
                fails = 0
            else:
                fails += 1
        else:
            fails += 1

    return None