import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    dim_L = n + k - c
    s_target = n - k + c

    def get_S(L):
        # Convert L to S via symplectic dual
        # S consists of vectors u such that sform(u, v) = 0 for all v in L.
        # E.nullspace computes binary orthogonality, and sform(u, v) = u . _J(v)
        eqs = [E._J(v, n) for v in L]
        return E.nullspace(eqs, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # We want c == target_c and offending == 0, and maximize d
        c_penalty = 5000 * abs(res["c"] - c)
        off_penalty = 100 * res["offending"]
        d_score = -res.get("d", 0) if res.get("d") is not None else 0
        return c_penalty + off_penalty + d_score

    def random_vector():
        val = 0
        for q in range(n):
            val |= int(rng.integers(0, 4)) << (2 * q)
        return val

    # Initialize L with dim_L independent vectors
    def random_L():
        while True:
            candidate = [random_vector() for _ in range(dim_L)]
            if len(E.gf2_basis(candidate)) == dim_L:
                return candidate

    L = random_L()
    S = get_S(L)
    cur = objective(E.evaluate(S))

    temp = 10.0
    fails = 0
    while E.remaining:
        temp = max(0.01, temp * 0.999)
        new_L = list(L)
        # Mutate L
        idx = int(rng.integers(dim_L))
        # Either replace with a fully random vector or mutate slightly
        if rng.random() < 0.3:
            new_L[idx] = random_vector()
        else:
            # Mutate active qubits
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            for q in qubits:
                new_L[idx] ^= int(rng.integers(1, 4)) << (2 * int(q))
        
        if len(E.gf2_basis(new_L)) != dim_L:
            fails += 1
            if fails > 200:
                L = random_L()
                S = get_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
            continue

        new_S = get_S(new_L)
        new_obj = objective(E.evaluate(new_S))
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = new_L
            cur = new_obj
            fails = 0
        else:
            fails += 1
            if fails > 500:
                L = random_L()
                S = get_S(L)
                cur = objective(E.evaluate(S))
                fails = 0
                temp = 10.0

    return None