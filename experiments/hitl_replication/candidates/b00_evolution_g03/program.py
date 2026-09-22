import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    target_c = target["c"]
    target_d = target["d"]
    s_L = n + k - target_c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - target_c) + res["offending"]
        if res.get("d") is not None:
            val += 100 * max(0, target_d - res["d"])
        return val

    def random_pauli():
        # Often make 1-qubit mutations to preserve locality, occasionally 2-qubit
        num_qubits = 1 if rng.random() < 0.7 else 2
        qubits = rng.choice(n, size=num_qubits, replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(s_L)]
            if len(E.gf2_basis(L)) == s_L:
                return L

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur = objective(E.evaluate(S))
    
    best_L = list(L)
    best_obj = cur
    
    temp = 30.0
    fails = 0

    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(s_L))
        candidate_L[idx] ^= random_pauli()
        
        if len(E.gf2_basis(candidate_L)) != s_L:
            fails += 1
            if fails > 300:
                # Restart from best or random
                if rng.random() < 0.5:
                    L = list(best_L)
                    # perturb best
                    for _ in range(2):
                        L[int(rng.integers(s_L))] ^= random_pauli()
                else:
                    L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                cur = objective(E.evaluate(S))
                fails = 0
            continue

        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        
        if res.get("offending") == 0 and res.get("c") == target_c and res.get("d", 0) >= target_d:
            return candidate_S
            
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
            if cur < best_obj:
                best_obj = cur
                best_L = list(L)
        else:
            fails += 1
            if fails > 300:
                if rng.random() < 0.5:
                    L = list(best_L)
                    for _ in range(2):
                        L[int(rng.integers(s_L))] ^= random_pauli()
                else:
                    L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                cur = objective(E.evaluate(S))
                fails = 0
    return None