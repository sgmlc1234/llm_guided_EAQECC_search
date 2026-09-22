import math

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    dL = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_vector():
        return int(rng.integers(1, 1 << (2 * n)))

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def get_random_L():
        while True:
            L = [random_vector() for _ in range(dL)]
            if len(E.gf2_basis(L)) == dL:
                return L

    best_L = None
    best_obj = 10**9

    # Try to load from incumbent if available
    inc = E.incumbent
    if inc is not None:
        # Construct L from S
        rows = [E._J(v, n) for v in inc]
        best_L = E.nullspace(rows, 2 * n)
        best_obj = objective(E.incumbent_parameters)

    if best_L is None or len(best_L) != dL:
        best_L = get_random_L()
        best_obj = objective(E.evaluate(get_S(best_L)))

    L = list(best_L)
    cur_obj = best_obj
    temp = 30.0
    fails = 0

    while E.remaining:
        temp = max(0.05, temp * 0.999)
        idx = int(rng.integers(dL))
        old_val = L[idx]
        
        # Mutation: either mutate a few bits or replace entirely
        if rng.random() < 0.5:
            L[idx] ^= random_vector() & ((1 << (2 * n)) - 1)
        else:
            L[idx] = random_vector()

        if len(E.gf2_basis(L)) != dL:
            L[idx] = old_val
            fails += 1
            if fails > 500:
                L = get_random_L()
                cur_obj = objective(E.evaluate(get_S(L)))
                fails = 0
            continue

        S = get_S(L)
        res = E.evaluate(S)
        new_obj = objective(res)
        
        delta = new_obj - cur_obj
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            cur_obj = new_obj
            fails = 0
            if cur_obj < best_obj:
                best_obj = cur_obj
                best_L = list(L)
        else:
            L[idx] = old_val
            fails += 1

        if fails > 1000:
            L = get_random_L()
            cur_obj = objective(E.evaluate(get_S(L)))
            fails = 0
            temp = 30.0

    return None