import math
import numpy as np

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    l_rank = n + k - target_c

    def objective(res):
        if res is None or "offending" not in res or "c" not in res:
            return 10**9
        if res["offending"] > 0 or res["c"] != target_c:
            return 5000 * abs(res["c"] - target_c) + res["offending"]
        # Valid code with matching c, try to maximize distance
        d = res.get("d")
        return -d if d is not None else 0

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, min(4, n + 1))), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_independent_L():
        while True:
            L = [random_pauli() for _ in range(l_rank)]
            if len(E.gf2_basis(L)) == l_rank:
                return L

    while E.remaining:
        L = get_independent_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur_obj = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.01, temp * 0.995)
            cand_L = list(L)
            idx = int(rng.integers(l_rank))
            cand_L[idx] = random_pauli()
            if len(E.gf2_basis(cand_L)) != l_rank:
                fails += 1
                continue
            
            cand_S = E.nullspace([E._J(v, n) for v in cand_L], 2 * n)
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None