import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    r_L = n + k - c

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def get_L_basis():
        while True:
            candidate = [random_vector() for _ in range(r_L)]
            if len(E.gf2_basis(candidate)) == r_L:
                return candidate

    def L_to_S(L):
        j_L = [E._J(v, n) for v in L]
        return E.nullspace(j_L, 2 * n)

    initial_state = E.incumbent
    best_L = None
    best_val = 10**9

    while E.remaining:
        L = get_L_basis()
        S = L_to_S(L)
        res = E.evaluate(S)
        val = objective(res)
        if val < best_val:
            best_val, best_L = val, list(L)
        
        temp = 30.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.99)
            new_L = list(best_L)
            idx = int(rng.integers(r_L))
            # Mutate with a random Pauli
            qubit = int(rng.integers(n))
            pauli = int(rng.integers(1, 4)) << (2 * qubit)
            new_L[idx] ^= pauli
            
            if len(E.gf2_basis(new_L)) != r_L:
                fails += 1
                continue
            
            new_S = L_to_S(new_L)
            new_res = E.evaluate(new_S)
            new_val = objective(new_res)
            
            delta = new_val - best_val
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                best_L, best_val = new_L, new_val
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None