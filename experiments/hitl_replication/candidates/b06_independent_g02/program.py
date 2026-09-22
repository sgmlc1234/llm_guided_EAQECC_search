import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    rl = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    # Try to initialize L from incumbent if available
    init_L = None
    if E.incumbent is not None:
        S_inc = E.incumbent
        L_inc = E.nullspace([E._J(v, n) for v in S_inc], 2 * n)
        if len(L_inc) == rl:
            init_L = list(L_inc)

    while E.remaining:
        if init_L is not None:
            L = init_L
            init_L = None
        else:
            # Generate random independent L of size rl
            L = []
            while len(L) < rl:
                v = int(rng.integers(1, 1 << (2 * n)))
                if len(E.gf2_basis(L + [v])) == len(L) + 1:
                    L.append(v)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = list(L)
            idx = int(rng.integers(rl))
            cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != rl:
                fails += 1
                continue
                
            cand_S = get_S(cand_L)
            if len(cand_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(cand_S)
            new_obj = objective(res)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None