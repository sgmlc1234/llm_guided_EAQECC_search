import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = 2 * n - s  # for these targets, len_L = 4

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

    # Generate a random independent basis L of size len_L
    def get_random_L():
        while True:
            candidate = []
            for _ in range(len_L):
                # random non-zero vector
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                candidate.append(val)
            if len(E.gf2_basis(candidate)) == len_L:
                return candidate

    L = get_random_L()
    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur = objective(E.evaluate(S))

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.998)
        # Mutate L
        candidate_L = list(L)
        mut_idx = int(rng.integers(len_L))
        if rng.random() < 0.4:
            # XOR with another element in L
            other_idx = (mut_idx + int(rng.integers(1, len_L))) % len_L
            candidate_L[mut_idx] ^= candidate_L[other_idx]
        else:
            # XOR with random Pauli
            candidate_L[mut_idx] ^= random_pauli()
        
        if candidate_L[mut_idx] == 0 or len(E.gf2_basis(candidate_L)) != len_L:
            fails += 1
            if fails > 200:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                cur = objective(E.evaluate(S))
                fails = 0
            continue

        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        if len(candidate_S) != s:
            continue

        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur

        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
        else:
            fails += 1
            if fails > 200:
                L = get_random_L()
                S = E.nullspace([E._J(v, n) for v in L], 2 * n)
                cur = objective(E.evaluate(S))
                fails = 0

    return None