import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k_target = target["k"]
    c_target = target["c"]
    d_target = target["d"]
    
    # s is the size of S, l_size is the size of L
    l_size = n + k_target - c_target
    s_size = n - k_target + c_target

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 1e9
        # Primary: match target c and 0 offending
        penalty = 5000 * abs(res.get("c", 0) - c_target) + res.get("offending", 999)
        # Secondary: maximize distance d towards d_target
        d_val = res.get("d")
        if d_val is None:
            penalty += 1000
        else:
            penalty += 100 * max(0, d_target - d_val)
        return penalty

    def random_vector():
        # Generate a random binary vector of length 2n represented as an integer
        val = 0
        for i in range(2 * n):
            if rng.integers(2):
                val |= (1 << i)
        return val

    # Generate initial L of full rank l_size
    def get_random_L():
        while True:
            candidate_L = [random_vector() for _ in range(l_size)]
            if len(E.gf2_basis(candidate_L)) == l_size:
                return candidate_L

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    best_res = E.evaluate(S)
    cur = objective(best_res)

    fails = 0
    temp = 10.0

    while E.remaining:
        # Mutate L
        temp = max(0.01, temp * 0.999)
        idx = int(rng.integers(l_size))
        old_val = L[idx]
        
        # Apply a small perturbation or replace completely
        if rng.random() < 0.3:
            L[idx] = random_vector()
        else:
            # XOR with a random Pauli element (1-2 active qubits)
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            L[idx] ^= delta

        if len(E.gf2_basis(L)) != l_size:
            # Restore
            L[idx] = old_val
            fails += 1
            continue

        # Convert L to S and evaluate
        S_cand = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S_cand)
        new_obj = objective(res)

        if res.get("offending") == 0 and res.get("c") == c_target and res.get("d", 0) >= d_target:
            return S_cand

        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            cur = new_obj
            fails = 0
        else:
            # Restore
            L[idx] = old_val
            fails += 1

        # Periodic restart to avoid local minima
        if fails > 1000:
            L = get_random_L()
            S = E.nullspace([E._J(v, n) for v in L], 2 * n)
            best_res = E.evaluate(S)
            cur = objective(best_res)
            fails = 0
            temp = 10.0

    return None