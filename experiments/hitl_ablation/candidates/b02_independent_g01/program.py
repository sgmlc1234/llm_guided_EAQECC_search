import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    L_len = 2 * n - s

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

    # Generate a valid initial L of rank L_len
    while True:
        L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(L_len)]
        if len(E.gf2_basis(L)) == L_len:
            break

    S = E.nullspace([E._J(v, n) for v in L], 2 * n)
    cur = objective(E.evaluate(S))

    temp, fails = 30.0, 0
    while E.remaining and fails < 3000:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(L_len))
        if rng.random() < 0.5:
            candidate_L[idx] = random_pauli()
        else:
            candidate_L[idx] ^= random_pauli()

        if len(E.gf2_basis(candidate_L)) != L_len:
            fails += 1
            continue

        candidate_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
        if len(candidate_S) != s:
            fails += 1
            continue

        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1

    return None