import math
import numpy as np

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    l_dim = n + k - c_target
    
    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def generate_random_L():
        while True:
            candidate = []
            for _ in range(l_dim):
                val = 0
                for q in range(n):
                    val |= int(rng.integers(0, 4)) << (2 * q)
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == l_dim:
                return candidate

    def mutate(L):
        candidate = list(L)
        idx = int(rng.integers(l_dim))
        # Randomly choose mutation: small perturbation or complete replacement
        if rng.random() < 0.7:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate[idx] ^= delta
        else:
            # completely random vector
            val = 0
            for q in range(n):
                val |= int(rng.integers(0, 4)) << (2 * q)
            candidate[idx] = val
        return candidate

    while E.remaining:
        L = generate_random_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != n - k + c_target:
            continue
        
        res = E.evaluate(S)
        cur = objective(res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = mutate(L)
            if len(E.gf2_basis(cand_L)) != l_dim:
                fails += 1
                continue
                
            cand_S = E.nullspace([E._J(v, n) for v in cand_L], 2 * n)
            if len(cand_S) != n - k + c_target:
                fails += 1
                continue
                
            new_res = E.evaluate(cand_S)
            new_obj = objective(new_res)
            
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None