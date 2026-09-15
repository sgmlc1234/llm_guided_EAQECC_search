import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    r_L = n + k - c
    s = n - k + c

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 1e9
        return res["offending"] * 1000 + abs(res["c"] - c) * 5000

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
        num_muts = int(rng.choice([1, 2, 3], p=[0.7, 0.2, 0.1]))
        for _ in range(num_muts):
            q = int(rng.integers(0, n))
            op = int(rng.integers(1, 4))
            v_new ^= (op << (2 * q))
        return v_new

    def init_L():
        while True:
            candidate = [random_vector() for _ in range(r_L)]
            if len(E.gf2_basis(candidate)) == r_L:
                return candidate

    best_L = init_L()
    best_S = get_S(best_L)
    best_res = E.evaluate(best_S)
    best_obj = objective(best_res)

    L = list(best_L)
    curr_obj = best_obj
    stagnant = 0
    temp = 10.0

    while E.remaining:
        if stagnant > 250:
            # Hard restart with probability 0.5, else soft restart
            if rng.random() < 0.5:
                L = init_L()
            else:
                L = list(best_L)
                for _ in range(int(rng.integers(1, 4))):
                    idx = int(rng.integers(r_L))
                    L[idx] = mutate_vector(L[idx])
            if len(E.gf2_basis(L)) == r_L:
                new_S = get_S(L)
                res = E.evaluate(new_S)
                curr_obj = objective(res)
                if curr_obj < best_obj:
                    best_obj = curr_obj
                    best_L = list(L)
                stagnant = 0
                temp = 10.0
            continue

        new_L = list(L)
        mut_idx = int(rng.integers(r_L))
        if rng.random() < 0.15:
            new_L[mut_idx] = random_vector()
        else:
            new_L[mut_idx] = mutate_vector(new_L[mut_idx])

        if len(E.gf2_basis(new_L)) != r_L:
            stagnant += 1
            continue

        new_S = get_S(new_L)
        res = E.evaluate(new_S)
        obj = objective(res)

        delta = obj - curr_obj
        temp = max(0.01, temp * 0.992)

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = new_L
            curr_obj = obj
            if obj < best_obj:
                best_obj = obj
                best_L = list(new_L)
                stagnant = 0
            else:
                stagnant += 1
        else:
            stagnant += 1

    return None