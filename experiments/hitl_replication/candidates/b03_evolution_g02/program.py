import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    target_d = target.get("d", 0)
    s = n - k + c
    l_size = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c) + 10 * res["offending"]
        if res["offending"] == 0 and res.get("d") is not None:
            val += 100 * max(0, target_d - res["d"])
        return val

    def random_pauli(w):
        qubits = rng.choice(n, size=min(n, w), replace=False)
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
    best_L = list(L)
    best_val = cur

    temp, fails = 20.0, 0
    while E.remaining:
        temp = max(0.05, temp * 0.996)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        
        if rng.random() < 0.7:
            w = int(rng.choice([1, 2, 3], p=[0.5, 0.35, 0.15]))
            candidate_L[idx] ^= random_pauli(w)
        else:
            other_basis = [L[i] for i in range(l_size) if i != idx]
            while True:
                val = int(rng.integers(1, 1 << (2 * n)))
                if len(E.gf2_basis(other_basis + [val])) == l_size:
                    candidate_L[idx] = val
                    break

        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            continue
        
        candidate_S = get_S(candidate_L)
        new_obj = objective(E.evaluate(candidate_S))
        
        if new_obj < best_val:
            best_val = new_obj
            best_L = list(candidate_L)
            
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
        if fails >= 250:
            if rng.random() < 0.6:
                L = list(best_L)
                cur = best_val
            else:
                L = random_L()
                cur = objective(E.evaluate(get_S(L)))
            fails = 0
            temp = 20.0

    return None