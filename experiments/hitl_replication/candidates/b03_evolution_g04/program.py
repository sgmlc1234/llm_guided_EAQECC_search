import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 1000 * abs(res.get("c", 0) - c) + res.get("offending", 0)

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

    fails = 0
    while E.remaining:
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        
        if rng.random() < 0.25:
            candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
        else:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate_L[idx] ^= delta

        if len(E.gf2_basis(candidate_L)) != l_size:
            continue
            
        candidate_S = get_S(candidate_L)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        
        if new_obj <= cur:
            if new_obj < cur:
                fails = 0
            else:
                fails += 1
            L = candidate_L
            cur = new_obj
        else:
            fails += 1
            
        if fails >= 350:
            L = random_L()
            S = get_S(L)
            cur = objective(E.evaluate(S))
            fails = 0

    return None