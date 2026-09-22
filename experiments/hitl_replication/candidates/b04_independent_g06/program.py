import math
import numpy as np

def search(target, max_evals):
    n, k, c, target_d = target["n"], target["k"], target["c"], target["d"]
    L_len = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        c_diff = abs(res["c"] - c)
        off = res["offending"]
        d_val = res.get("d")
        d_diff = max(0, target_d - d_val) if d_val is not None else target_d
        return 10000 * c_diff + 500 * off + d_diff

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Generate a random independent L
        while E.remaining:
            state = [int(rng.integers(1, 1 << (2 * n))) for _ in range(L_len)]
            if len(E.gf2_basis(state)) == L_len:
                break
        if not E.remaining:
            break

        S = E.nullspace([E._J(v, n) for v in state], 2 * n)
        cur = objective(E.evaluate(S))
        temp, fails = 40.0, 0

        while fails < 600 and E.remaining:
            temp = max(0.05, temp * 0.995)
            candidate = list(state)
            idx = int(rng.integers(L_len))
            candidate[idx] ^= random_pauli()
            if len(E.gf2_basis(candidate)) != L_len:
                fails += 1
                continue

            S_cand = E.nullspace([E._J(v, n) for v in candidate], 2 * n)
            new_obj = objective(E.evaluate(S_cand))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                state, cur = candidate, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None