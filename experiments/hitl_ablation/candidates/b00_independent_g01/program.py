import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    dim_L = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        # Primary objective: match target c and reduce offending elements to 0
        val = 5000 * abs(res["c"] - c) + res["offending"]
        # Secondary: maximize distance if we have a valid structure
        if res.get("d") is not None:
            val -= 10 * res["d"]
        return val

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_L_basis():
        while True:
            basis = []
            for _ in range(dim_L):
                # Generate independent Pauli
                attempts = 0
                while attempts < 100:
                    cand = int(rng.integers(1, 1 << (2 * n)))
                    test = basis + [cand]
                    if len(E.gf2_basis(test)) == len(test):
                        basis.append(cand)
                        break
                    attempts += 1
            if len(basis) == dim_L:
                return basis

    while E.remaining:
        # Restart with a new random L
        L = get_L_basis()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur_res = E.evaluate(S)
        cur = objective(cur_res)
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            # Mutate one element of L
            idx = int(rng.integers(dim_L))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != dim_L:
                fails += 1
                continue
                
            S_cand = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
            new_res = E.evaluate(S_cand)
            new_obj = objective(new_res)
            
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None