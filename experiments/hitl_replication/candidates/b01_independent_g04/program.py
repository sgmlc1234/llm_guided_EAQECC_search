import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_rank = n + k - c

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

    def get_valid_L():
        while True:
            candidate = [int(rng.integers(1, 1 << (2 * n))) for _ in range(L_rank)]
            if len(E.gf2_basis(candidate)) == L_rank:
                return candidate

    while E.remaining:
        L = get_valid_L()
        J_L = [E._J(v, n) for v in L]
        S = E.nullspace(J_L, 2 * n)
        if len(S) != s:
            continue
        cur = objective(E.evaluate(S))

        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(L_rank))
            candidate_L[idx] ^= random_pauli()
            if len(E.gf2_basis(candidate_L)) != L_rank:
                fails += 1
                continue

            J_L_cand = [E._J(v, n) for v in candidate_L]
            candidate_S = E.nullspace(J_L_cand, 2 * n)
            if len(candidate_S) != s:
                fails += 1
                continue

            new_obj = objective(E.evaluate(candidate_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None