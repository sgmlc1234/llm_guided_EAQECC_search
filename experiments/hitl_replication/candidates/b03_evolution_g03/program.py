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
    best_L = list(L)
    best_obj = cur

    temp, fails = 30.0, 0
    while E.remaining:
        temp = max(0.1, temp * 0.996)
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        candidate_L[idx] ^= random_pauli()
        
        if len(E.gf2_basis(candidate_L)) != l_size:
            fails += 1
            continue
        
        candidate_S = get_S(candidate_L)
        new_obj = objective(E.evaluate(candidate_S))
        
        if new_obj < best_obj:
            best_obj = new_obj
            best_L = list(candidate_L)
            
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
        if fails >= 400:
            if rng.random() < 0.7:
                L = list(best_L)
                for _ in range(5):
                    mut_L = list(L)
                    mut_L[int(rng.integers(l_size))] ^= random_pauli()
                    if len(E.gf2_basis(mut_L)) == l_size:
                        L = mut_L
                        break
                cur = objective(E.evaluate(get_S(L)))
            else:
                L = random_L()
                cur = objective(E.evaluate(get_S(L)))
            fails = 0
            temp = 30.0

    return None