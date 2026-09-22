import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    s = n - k + c_target
    r_L = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def random_L():
        while True:
            candidate = []
            for _ in range(r_L):
                val = 0
                for q in range(n):
                    val |= int(rng.integers(0, 4)) << (2 * q)
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == r_L:
                return candidate

    L = random_L()
    S = get_S(L)
    res = E.evaluate(S)
    cur = objective(res)

    temp = 30.0
    fails = 0
    
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        new_L = list(L)
        idx = int(rng.integers(r_L))
        if rng.random() < 0.5:
            val = 0
            for q in range(n):
                val |= int(rng.integers(0, 4)) << (2 * q)
            new_L[idx] = val
        else:
            other = int(rng.integers(r_L))
            if other != idx:
                new_L[idx] ^= new_L[other]
                val = 0
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                for q in qubits:
                    val |= int(rng.integers(1, 4)) << (2 * int(q))
                new_L[idx] ^= val

        if len(E.gf2_basis(new_L)) != r_L:
            continue
        
        new_S = get_S(new_L)
        if len(new_S) != s:
            continue
            
        new_res = E.evaluate(new_S)
        new_obj = objective(new_res)
        
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = new_L, new_obj
            fails = 0
        else:
            fails += 1
            if fails > 200:
                if E.incumbent is not None:
                    S_inc = E.incumbent
                    L = E.nullspace([E._J(v, n) for v in S_inc], 2 * n)
                    cur = objective(E.incumbent_parameters)
                else:
                    L = random_L()
                    S = get_S(L)
                    cur = objective(E.evaluate(S))
                fails = 0
                temp = 30.0

    return None