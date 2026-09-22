import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    req_d = target.get("d", 0)
    s = n - k + c
    len_L = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c) + 100 * res["offending"]
        if "d" in res and res["d"] is not None:
            val += 10 * max(0, req_d - res["d"])
        return val

    def random_pauli():
        wt = int(rng.choice([1, 2, 3, n], p=[0.5, 0.3, 0.15, 0.05]))
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

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        mut_idx = int(rng.integers(len_L))
        
        mtype = rng.choice(["replace", "add", "combine"], p=[0.4, 0.4, 0.2])
        if mtype == "replace":
            candidate_L[mut_idx] = random_pauli()
        elif mtype == "add":
            candidate_L[mut_idx] ^= random_pauli()
        else:
            other_idx = (mut_idx + int(rng.integers(1, len_L))) % len_L
            candidate_L[mut_idx] ^= candidate_L[other_idx]
        
        if candidate_L[mut_idx] == 0 or len(E.gf2_basis(candidate_L)) != len_L:
            fails += 1
            if fails > 80:
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
        else: 
            fails += 1
            if fails > 80:
                L = list(best_L)
                for _ in range(int(rng.integers(1, 3))):
                    idx = int(rng.integers(len_L))
                    L[idx] ^= random_pauli()
                if len(E.gf2_basis(L)) == len_L:
                    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                    cur = objective(E.evaluate(S))
                fails = 0

    return None