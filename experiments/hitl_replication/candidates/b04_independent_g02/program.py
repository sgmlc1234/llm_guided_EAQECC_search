import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    len_L = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(len_L)]
            if len(E.gf2_basis(L)) == len_L:
                return L

    def L_to_S(L):
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    best_L = get_random_L()
    best_obj = objective(E.evaluate(L_to_S(best_L)))
    temp = 10.0
    fails = 0

    while E.remaining:
        cand_L = list(best_L)
        idx = int(rng.integers(len_L))
        mut = int(rng.integers(1, 1 << (2 * n)))
        if rng.random() < 0.5:
            cand_L[idx] ^= mut
        else:
            cand_L[idx] = mut

        if len(E.gf2_basis(cand_L)) != len_L:
            fails += 1
            continue

        cand_S = L_to_S(cand_L)
        res = E.evaluate(cand_S)
        obj = objective(res)

        if obj < best_obj:
            best_L = list(cand_L)
            best_obj = obj
            fails = 0
        else:
            delta = obj - best_obj
            if delta < 10000 and rng.random() < math.exp(-delta / temp):
                best_L = list(cand_L)
                best_obj = obj
            fails += 1

        temp = max(0.1, temp * 0.995)
        if fails > 200:
            best_L = get_random_L()
            best_obj = objective(E.evaluate(L_to_S(best_L)))
            fails = 0
            temp = 10.0

    return None