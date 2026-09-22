import math
import numpy as np

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    l_size = n + k - c_target  # for training targets, this is 4
    s_size = n - k + c_target

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def get_S(L):
        # Convert L to S using the symplectic relation
        # E.nullspace finds binary kernel of the input rows.
        # Since E._J swaps X and Z, nullspace on E._J(v) finds the symplectic complement.
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    def generate_valid_L():
        while True:
            L = [random_vector() for _ in range(l_size)]
            if len(E.gf2_basis(L)) == l_size:
                return L

    # Try to resume or start fresh
    L = generate_valid_L()
    S = get_S(L)
    cur = objective(E.evaluate(S)) if S and len(S) == s_size else 10**9

    temp = 30.0
    fails = 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        if fails > 500:
            L = generate_valid_L()
            S = get_S(L)
            cur = objective(E.evaluate(S)) if S and len(S) == s_size else 10**9
            fails = 0
            continue

        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        candidate_L[idx] ^= random_vector()
        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            continue

        candidate_S = get_S(candidate_L)
        if not candidate_S or len(candidate_S) != s_size:
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

    return None
