import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = 2 * n - s

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

    def random_L():
        while True:
            candidate = [int(rng.integers(1, 1 << (2 * n))) for _ in range(l_size)]
            if len(E.gf2_basis(candidate)) == l_size:
                return candidate

    L = random_L()
    S = get_S(L)
    cur = objective(E.evaluate(S))

    temp, fails = 30.0, 0
    while fails < 1500 and E.remaining:
        temp = max(0.1, temp * 0.995)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        candidate_L[idx] ^= random_pauli()
        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            continue
        
        candidate_S = get_S(candidate_L)
        new_obj = objective(E.evaluate(candidate_S))
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
        if fails >= 1500:
            L = random_L()
            S = get_S(L)
            cur = objective(E.evaluate(S))
            fails = 0

    return None