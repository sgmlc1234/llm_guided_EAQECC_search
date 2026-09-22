import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    # Size of L is n + k - c
    len_L = n + k - c

    def get_S(L):
        # Convert L to S via symplectic dual nullspace
        J_L = [E._J(v, n) for v in L]
        S = E.nullspace(J_L, 2 * n)
        return S

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

    # Initialize L as a independent set of size len_L
    # We can start by generating a random stabilizer of size len_L
    # and then mutating it.
    while E.remaining:
        # Construct initial L
        L = list(E.random_stabilizer(n, len_L, rng))
        S = get_S(L)
        if len(S) != s:
            # Fallback if nullspace size is incorrect
            continue
        
        cur_obj = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            # Mutate one element in L
            idx = int(rng.integers(len_L))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != len_L:
                fails += 1
                continue
                
            candidate_S = get_S(candidate_L)
            if len(candidate_S) != s:
                fails += 1
                continue
                
            res = E.evaluate(candidate_S)
            new_obj = objective(res)
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
                if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
                    if res.get("d") is not None and res["d"] >= target["d"]:
                        return candidate_S
            else:
                fails += 1
    return None