import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_size = n + k - c

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

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def generate_random_L():
        while True:
            L = []
            for _ in range(L_size):
                val = int(rng.integers(1, 1 << (2 * n)))
                L.append(val)
            if len(E.gf2_basis(L)) == L_size:
                return L

    best_state = None
    best_val = 10**9

    while E.remaining:
        L = generate_random_L()
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if cur < best_val:
            best_val = cur
            best_state = list(L)

        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            candidate_L[int(rng.integers(L_size))] ^= random_pauli()
            if len(E.gf2_basis(candidate_L)) != L_size:
                fails += 1
                continue
            
            cand_S = get_S(candidate_L)
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
                if cur < best_val:
                    best_val = cur
                    best_state = list(L)
            else:
                fails += 1

    return None