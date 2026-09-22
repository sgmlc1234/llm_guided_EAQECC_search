import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    l_size = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, min(4, n + 1))), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_independent_v(L_other):
        basis_other = E.gf2_basis(L_other)
        while True:
            v = int(rng.integers(1, 1 << (2 * n)))
            if len(E.gf2_basis(basis_other + [v])) == len(basis_other) + 1:
                return v

    def init_L():
        L = []
        for _ in range(l_size):
            L.append(get_independent_v(L))
        return L

    best_overall_obj = 10**9
    
    while E.remaining:
        L = init_L()
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        if cur < best_overall_obj:
            best_overall_obj = cur

        temp = 20.0
        no_improve = 0
        
        while E.remaining and no_improve < 150:
            temp = max(0.05, temp * 0.98)
            idx = int(rng.integers(l_size))
            old_val = L[idx]
            L_other = [L[i] for i in range(l_size) if i != idx]
            basis_other = E.gf2_basis(L_other)

            # Mutate and guarantee independence
            for _ in range(50):
                if rng.random() < 0.3:
                    cand = int(rng.integers(1, 1 << (2 * n)))
                else:
                    cand = old_val ^ random_pauli()
                if len(E.gf2_basis(basis_other + [cand])) == len(basis_other) + 1:
                    L[idx] = cand
                    break
            else:
                continue

            S = get_S(L)
            res = E.evaluate(S)
            new_obj = objective(res)

            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                if new_obj < cur:
                    no_improve = 0
                else:
                    no_improve += 1
                cur = new_obj
                if cur < best_overall_obj:
                    best_overall_obj = cur
            else:
                L[idx] = old_val
                no_improve += 1

    return None