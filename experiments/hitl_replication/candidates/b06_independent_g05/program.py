import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_rank = n + k - c
    s_rank = n - k + c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Initialize L
        L = list(E.random_stabilizer(n, l_rank, rng))
        S = get_S(L)
        if len(S) != s_rank:
            continue
        cur = objective(E.evaluate(S))

        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            candidate_L[int(rng.integers(l_rank))] ^= random_pauli()
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
            
            candidate_S = get_S(candidate_L)
            if len(candidate_S) != s_rank:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(candidate_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None