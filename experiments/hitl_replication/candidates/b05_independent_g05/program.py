import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_size = n + k - c
    s_size = n - k + c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        val = 0
        for i in range(2 * n):
            if rng.random() < 0.2:
                val |= (1 << i)
        if val == 0:
            val = int(rng.integers(1, 1 << (2 * n)))
        return val

    def get_L_basis():
        while True:
            basis = [random_vector() for _ in range(l_size)]
            if len(E.gf2_basis(basis)) == l_size:
                return basis

    initial_state = E.incumbent
    initial_measurement = E.incumbent_parameters

    if initial_state is not None:
        # Convert S to L
        L = E.nullspace([E._J(v, n) for v in initial_state], 2 * n)
        if len(L) > l_size:
            L = L[:l_size]
        elif len(L) < l_size:
            L = get_L_basis()
        cur = objective(initial_measurement)
    else:
        L = get_L_basis()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur = objective(E.evaluate(S))

    temp = 30.0
    fails = 0
    while E.remaining and fails < 3000:
        temp = max(0.01, temp * 0.998)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        
        # Mutation: either slight perturbation or completely random replace
        if rng.random() < 0.2:
            candidate_L[idx] = random_vector()
        else:
            # Flip a few bits
            num_flips = int(rng.integers(1, 4))
            for _ in range(num_flips):
                candidate_L[idx] ^= (1 << int(rng.integers(2 * n)))

        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            continue

        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        if len(candidate_S) != s_size:
            continue

        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1

        if cur == 0:
            break

    return None