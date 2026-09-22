import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        # Bias towards lower weight mutations to stay local
        wt = int(rng.choice([1, 2, 3], p=[0.5, 0.3, 0.2]))
        wt = min(wt, n)
        qubits = rng.choice(n, size=wt, replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_random_L():
        while True:
            candidate = []
            for _ in range(len_L):
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == len_L:
                return candidate

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur = objective(E.evaluate(S))
    
    best_L = list(L)
    best_obj = cur

    temp, fails, steps = 30.0, 0, 0
    while E.remaining:
        temp = max(0.05, temp * 0.998)
        candidate_L = list(L)
        mut_idx = int(rng.integers(len_L))
        
        # 40% chance of row combination, 60% chance of single-qubit mutation
        if rng.random() < 0.4:
            other_idx = (mut_idx + int(rng.integers(1, len_L))) % len_L
            candidate_L[mut_idx] ^= candidate_L[other_idx]
        else:
            candidate_L[mut_idx] ^= random_pauli()
        
        if candidate_L[mut_idx] == 0 or len(E.gf2_basis(candidate_L)) != len_L:
            fails += 1
            if fails > 150:
                L = list(best_L)
                for _ in range(int(rng.integers(1, 3))):
                    idx = int(rng.integers(len_L))
                    L[idx] ^= random_pauli()
                if len(E.gf2_basis(L)) == len_L:
                    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                    cur = objective(E.evaluate(S))
                fails = 0
            continue

        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        if len(candidate_S) != s:
            continue

        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
            if cur < best_obj:
                best_obj = cur
                best_L = list(L)
                steps = 0
        else:
            fails += 1
            steps += 1
            if fails > 150:
                L = list(best_L)
                for _ in range(int(rng.integers(1, 3))):
                    idx = int(rng.integers(len_L))
                    L[idx] ^= random_pauli()
                if len(E.gf2_basis(L)) == len_L:
                    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                    cur = objective(E.evaluate(S))
                fails = 0

        # Gentle restart on stagnation to escape local minima
        if steps > 2000:
            L = get_random_L()
            S = E.nullspace([E._J(v, n) for v in L], 2 * n)
            cur = objective(E.evaluate(S))
            best_L = list(L)
            best_obj = cur
            steps = 0
            temp = 30.0

    return None