import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    m = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    while E.remaining:
        L = []
        while len(L) < m:
            v = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [v]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(v)

        J_L = [E._J(x, n) for x in L]
        S = E.nullspace(J_L, 2 * n)
        res = E.evaluate(S)
        cur_obj = objective(res)

        temp = 30.0
        fails = 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(m))
            old_val = L[idx]

            if rng.random() < 0.5:
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                new_val = old_val ^ delta
            else:
                new_val = int(rng.integers(1, 1 << (2 * n)))

            L_candidate = list(L)
            L_candidate[idx] = new_val

            if len(E.gf2_basis(L_candidate)) != m:
                continue

            J_L = [E._J(x, n) for x in L_candidate]
            S_cand = E.nullspace(J_L, 2 * n)
            res_cand = E.evaluate(S_cand)
            cand_obj = objective(res_cand)

            delta_obj = cand_obj - cur_obj
            if delta_obj <= 0 or rng.random() < math.exp(-delta_obj / temp):
                L = L_candidate
                cur_obj = cand_obj
                if delta_obj < 0:
                    fails = 0
                else:
                    fails += 1
            else:
                fails += 1
    return None