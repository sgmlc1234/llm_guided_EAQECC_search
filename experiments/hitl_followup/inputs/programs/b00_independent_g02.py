import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    rl = n + k - c  # Rank of L, which is 4 for these targets
    rs = n - k + c  # Rank of S

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_s_from_l(L):
        # Convert L to S using E.nullspace([E._J(v, n) for v in L], 2*n)
        j_L = [E._J(v, n) for v in L]
        S = E.nullspace(j_L, 2 * n)
        return S

    while E.remaining:
        # Generate a random initial linearly independent L of size rl
        L = []
        while len(L) < rl:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_s_from_l(L)
        if len(S) != rs:
            continue
        
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 2000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = list(L)
            # Mutate one element of L
            idx = int(rng.integers(rl))
            cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != rl:
                fails += 1
                continue
                
            cand_S = get_s_from_l(cand_L)
            if len(cand_S) != rs:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None