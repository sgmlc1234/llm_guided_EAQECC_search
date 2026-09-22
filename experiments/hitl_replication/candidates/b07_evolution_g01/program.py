import math

def search(target, max_evals):
    n = target["n"]
    target_c = target["c"]
    target_d = target["d"]
    target_k = target["k"]
    num_L = n + target_k - target_c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        c_diff = abs(res["c"] - target_c)
        off = res["offending"]
        d = res.get("d")
        d_score = max(0, target_d - d) if d is not None else 100
        return 5000 * c_diff + 100 * off + d_score

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(num_L)]
            if len(E.gf2_basis(L)) == num_L:
                return L

    def mutate_L(L):
        for _ in range(20):
            L_new = list(L)
            idx = int(rng.integers(num_L))
            choice = rng.integers(4)
            if choice == 0:
                L_new[idx] = int(rng.integers(1, 1 << (2 * n)))
            elif choice == 1:
                qubit = int(rng.integers(n))
                delta = int(rng.integers(1, 4)) << (2 * qubit)
                L_new[idx] ^= delta
            elif choice == 2:
                qubits = rng.choice(n, size=2, replace=False)
                delta = (int(rng.integers(1, 4)) << (2 * int(qubits[0]))) | (int(rng.integers(1, 4)) << (2 * int(qubits[1])))
                L_new[idx] ^= delta
            else:
                other = int(rng.integers(num_L))
                if other != idx:
                    L_new[idx] ^= L_new[other]
            if len(E.gf2_basis(L_new)) == num_L:
                return L_new
        return L

    while E.remaining:
        L = get_random_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        cur = objective(res)
        
        temp = 20.0
        fails = 0
        while fails < 150 and E.remaining:
            temp = max(0.05, temp * 0.98)
            L_cand = mutate_L(L)
            S_cand = E.nullspace([E._J(v, n) for v in L_cand], 2 * n)
            res_cand = E.evaluate(S_cand)
            new_obj = objective(res_cand)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = L_cand, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None