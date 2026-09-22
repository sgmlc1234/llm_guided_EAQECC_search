import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    rank_L = n + k - c
    s = n - k + c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target["c"]) + res["offending"]

    def get_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    def get_L(S):
        return E.nullspace([E._J(v, n) for v in S], 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    initial_S = E.incumbent
    if initial_S is not None:
        L = get_L(initial_S)
        cur = objective(E.incumbent_parameters)
    else:
        L = []
        while len(L) < rank_L:
            v = random_pauli()
            if len(E.gf2_basis(L + [v])) == len(L) + 1:
                L.append(v)
        cur = objective(E.evaluate(get_S(L)))

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(rank_L))
        if rng.random() < 0.5:
            candidate_L[idx] = random_pauli()
        else:
            candidate_L[idx] ^= random_pauli()
        
        if len(E.gf2_basis(candidate_L)) != rank_L:
            fails += 1
            continue
            
        candidate_S = get_S(candidate_L)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
        if fails > 1000:
            L = []
            while len(L) < rank_L:
                v = random_pauli()
                if len(E.gf2_basis(L + [v])) == len(L) + 1:
                    L.append(v)
            cur = objective(E.evaluate(get_S(L)))
            temp, fails = 30.0, 0

    return None