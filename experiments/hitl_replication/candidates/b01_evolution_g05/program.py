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

    pop_size = 6
    population = []
    for _ in range(pop_size):
        if not E.remaining:
            break
        L = random_L()
        S = get_S(L)
        res = E.evaluate(S)
        obj = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target["d"]:
            return S
        population.append((obj, L, res))

    if not population:
        return None

    while E.remaining:
        population.sort(key=lambda x: x[0])
        idx_to_mutate = int(rng.integers(0, min(3, len(population))))
        parent_L = population[idx_to_mutate][1]
        
        new_L = list(parent_L)
        mut_idx = int(rng.integers(dim_L))
        
        r = rng.random()
        if r < 0.4:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            for q in qubits:
                new_L[mut_idx] ^= int(rng.integers(1, 4)) << (2 * int(q))
        elif r < 0.7:
            other_idx = int(rng.integers(dim_L))
            if other_idx != mut_idx:
                new_L[mut_idx] ^= parent_L[other_idx]
            new_L[mut_idx] ^= int(rng.integers(1, 4)) << (2 * int(rng.integers(n)))
        else:
            new_L[mut_idx] = random_vector()

        if len(E.gf2_basis(new_L)) != dim_L:
            continue

        new_S = get_S(new_L)
        new_res = E.evaluate(new_S)
        new_obj = objective(new_res)

        if new_res.get("offending") == 0 and new_res.get("c") == c and new_res.get("d", 0) >= target["d"]:
            return new_S

        if new_obj < population[-1][0]:
            population[-1] = (new_obj, new_L, new_res)
            
    return None