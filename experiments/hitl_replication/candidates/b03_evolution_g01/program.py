import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c" ] - c) + res["offending"]

    def random_independent_val(basis_exclude):
        while True:
            val = int(rng.integers(1, 1 << (2 * n)))
            if len(E.gf2_basis(basis_exclude + [val])) == len(basis_exclude) + 1:
                return val

    def random_L():
        L = []
        for _ in range(l_size):
            L.append(random_independent_val(L))
        return L

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    L = random_L()
    S = get_S(L)
    cur = objective(E.evaluate(S))
    best_L = list(L)
    best_val = cur

    fails = 0
    temp = 10.0
    
    while E.remaining:
        candidate_L = list(L)
        idx = int(rng.integers(l_size))
        other_basis = [L[i] for i in range(l_size) if i != idx]
        
        if rng.random() < 0.4:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            val = L[idx] ^ delta
            if len(E.gf2_basis(other_basis + [val])) == l_size:
                candidate_L[idx] = val
            else:
                continue
        else:
            candidate_L[idx] = random_independent_val(other_basis)

        candidate_S = get_S(candidate_L)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        
        if new_obj < best_val:
            best_val = new_obj
            best_L = list(candidate_L)
            
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur = candidate_L, new_obj
            fails = 0
        else:
            fails += 1
            
        temp = max(0.05, temp * 0.999)
        
        if fails >= 150:
            if rng.random() < 0.5:
                L = list(best_L)
                cur = best_val
            else:
                L = random_L()
                S = get_S(L)
                cur = objective(E.evaluate(S))
            fails = 0

    return None