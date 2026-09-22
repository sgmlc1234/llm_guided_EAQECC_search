import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_size = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target["c"]) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_random_L():
        while True:
            candidate = []
            for _ in range(L_size):
                candidate.append(int(rng.integers(0, 1 << (2 * n))))
            if len(E.gf2_basis(candidate)) == L_size:
                return candidate

    initial_S = E.incumbent
    if initial_S is not None and len(initial_S) == s:
        try:
            L = E.nullspace([E._J(v, n) for v in initial_S], 2*n)
            if len(L) != L_size:
                L = get_random_L()
        except Exception:
            L = get_random_L()
    else:
        L = get_random_L()

    S = E.nullspace([E._J(v, n) for v in L], 2*n)
    cur = objective(E.evaluate(S))

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(L_size))
        if rng.random() < 0.7:
            candidate_L[idx] ^= random_pauli()
        else:
            candidate_L[idx] = int(rng.integers(0, 1 << (2 * n)))
        
        if len(E.gf2_basis(candidate_L)) != L_size:
            fails += 1
            if fails > 1000:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2*n)
                cur = objective(E.evaluate(S))
                fails = 0
            continue

        S_cand = E.nullspace([E._J(v, n) for v in candidate_L], 2*n)
        new_obj = objective(E.evaluate(S_cand))
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
        else:
            fails += 1
            if fails > 1000:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2*n)
                cur = objective(E.evaluate(S))
                fails = 0
    return None