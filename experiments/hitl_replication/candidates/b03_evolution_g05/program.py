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

    def mutate(L, depth=1):
        candidate = list(L)
        for _ in range(depth):
            idx = int(rng.integers(l_size))
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            candidate[idx] ^= delta
        return candidate

    best_L = random_L()
    best_obj = objective(E.evaluate(get_S(best_L)))
    
    L = list(best_L)
    cur = best_obj

    temp = 30.0
    fails = 0
    soft_restarts = 0

    while E.remaining:
        temp = max(0.05, temp * 0.995)
        candidate_L = mutate(L, depth=1 if rng.random() < 0.8 else 2)
        if len(E.gf2_basis(candidate_L)) != l_size:
            continue
            
        candidate_S = get_S(candidate_L)
        res = E.evaluate(candidate_S)
        new_obj = objective(res)
        
        delta = new_obj - cur
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L = candidate_L
            cur = new_obj
            if new_obj < best_obj:
                best_obj = new_obj
                best_L = list(candidate_L)
                fails = 0
                soft_restarts = 0
            else:
                fails += 1
        else:
            fails += 1
            
        if fails >= 250:
            if soft_restarts < 5:
                L = mutate(best_L, depth=3)
                if len(E.gf2_basis(L)) == l_size:
                    cur = objective(E.evaluate(get_S(L)))
                    soft_restarts += 1
                    fails = 0
                    temp = 20.0
            else:
                L = random_L()
                cur = objective(E.evaluate(get_S(L)))
                soft_restarts = 0
                fails = 0
                temp = 30.0

    return None