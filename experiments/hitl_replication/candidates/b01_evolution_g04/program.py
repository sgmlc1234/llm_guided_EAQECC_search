import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    dim_L = n + k - c

    def get_S(L):
        eqs = [E._J(v, n) for v in L]
        return E.nullspace(eqs, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 1e9
        # Primary objective: match target c and minimize offending. Secondary: maximize d
        c_diff = abs(res["c"] - c)
        off = res["offending"]
        d = res.get("d", 0) or 0
        return c_diff * 10000 + off * 100 - d

    def random_vector():
        val = 0
        for q in range(n):
            val |= int(rng.integers(0, 4)) << (2 * q)
        return val

    def random_L():
        while True:
            candidate = [random_vector() for _ in range(dim_L)]
            if len(E.gf2_basis(candidate)) == dim_L:
                return candidate

    best_S = None
    best_obj = 1e9

    while E.remaining:
        # Start a new trajectory
        L = random_L()
        S = get_S(L)
        res = E.evaluate(S)
        cur_obj = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target["d"]:
            return S

        fails = 0
        temp = 8.0
        
        while E.remaining and fails < 120:
            new_L = list(L)
            idx = int(rng.integers(dim_L))
            
            # Diverse mutation strategies
            r = rng.random()
            if r < 0.6:
                # 1 or 2 qubit local flip
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                for q in qubits:
                    new_L[idx] ^= int(rng.integers(1, 4)) << (2 * int(q))
            elif r < 0.9:
                # Add a sparse noise vector
                v = 0
                for _ in range(int(rng.integers(1, 3))):
                    v |= int(rng.integers(1, 4)) << (2 * int(rng.integers(n)))
                new_L[idx] ^= v
            else:
                # Complete replacement of one basis element
                new_L[idx] = random_vector()

            if len(E.gf2_basis(new_L)) != dim_L:
                continue

            new_S = get_S(new_L)
            new_res = E.evaluate(new_S)
            new_obj = objective(new_res)

            if new_res.get("offending") == 0 and new_res.get("c") == c and new_res.get("d", 0) >= target["d"]:
                return new_S

            delta = new_obj - cur_obj
            if delta <= 0 or (temp > 0.05 and rng.random() < math.exp(-delta / temp)):
                L = new_L
                cur_obj = new_obj
                fails = 0
            else:
                fails += 1
            
            temp *= 0.98

    return None
