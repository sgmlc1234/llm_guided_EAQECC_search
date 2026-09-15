import math
import numpy as np

def search(target, max_evals):
    n, k, c, target_d = target["n"], target["k"], target["c"], target["d"]
    r = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 10000 * abs(res["c"] - c) + 500 * res["offending"]
        d = res.get("d")
        if d is None:
            val += 200
        else:
            val += 10 * max(0, target_d - d)
        return val

    def random_pauli():
        # Weighted selection: prefer single-qubit perturbations, occasionally 2 or 3 qubits
        p = rng.random()
        if p < 0.6:
            num_qubits = 1
        elif p < 0.9:
            num_qubits = 2
        else:
            num_qubits = 3
        qubits = rng.choice(n, size=min(n, num_qubits), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    best_L = None
    best_obj = 10**9

    while E.remaining:
        # Initialize L
        L = []
        while len(L) < r:
            candidate = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [candidate]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(candidate)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target_d:
            return S

        if cur < best_obj:
            best_obj = cur
            best_L = list(L)

        temp = 50.0
        fails = 0
        
        while fails < 600 and E.remaining:
            temp = max(0.05, temp * 0.995)
            cand_L = list(L)
            
            # Soft restart/backtracking mechanism to prevent getting stuck
            if fails > 120 and best_L is not None and rng.random() < 0.2:
                cand_L = list(best_L)
                # Apply a slight perturbation
                for _ in range(rng.integers(1, 3)):
                    idx = int(rng.integers(r))
                    cand_L[idx] ^= random_pauli()
            else:
                idx = int(rng.integers(r))
                if rng.random() < 0.4:
                    # Linear combination mutation
                    other = int(rng.integers(r))
                    if other != idx:
                        cand_L[idx] ^= cand_L[other]
                cand_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(cand_L)) != r:
                fails += 1
                continue
                
            cand_S = get_S(cand_L)
            cand_res = E.evaluate(cand_S)
            new_obj = objective(cand_res)
            
            if cand_res.get("offending") == 0 and cand_res.get("c") == c and cand_res.get("d", 0) >= target_d:
                return cand_S
                
            if new_obj < best_obj:
                best_obj = new_obj
                best_L = list(cand_L)
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None