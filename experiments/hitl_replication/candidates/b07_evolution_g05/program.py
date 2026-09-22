import math

def search(target, max_evals):
    n = target["n"]
    target_c = target["c"]
    target_k = target["k"]
    target_d = target["d"]
    num_L = n + target_k - target_c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        c_diff = abs(res["c"] - target_c)
        off = res["offending"]
        d = res.get("d")
        d_score = max(0, target_d - d) if d is not None else 100
        return 10000 * c_diff + 100 * off + d_score

    def get_random_L():
        while True:
            L = [int(rng.integers(1, 1 << (2 * n))) for _ in range(num_L)]
            if len(E.gf2_basis(L)) == num_L:
                return L

    def mutate_L(L):
        for _ in range(15):
            L_new = list(L)
            idx = int(rng.integers(num_L))
            choice = rng.integers(4)
            if choice == 0:
                L_new[idx] = int(rng.integers(1, 1 << (2 * n)))
            elif choice == 1:
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                delta = 0
                for q in qubits:
                    delta |= int(rng.integers(1, 4)) << (2 * int(q))
                L_new[idx] ^= delta
            elif choice == 2:
                other = int(rng.integers(num_L))
                if other != idx:
                    L_new[idx] ^= L_new[other]
            else:
                # Swap two generators or shuffle
                other = int(rng.integers(num_L))
                L_new[idx], L_new[other] = L_new[other], L_new[idx]
            if len(E.gf2_basis(L_new)) == num_L:
                return L_new
        return L

    best_L = None
    best_obj = 10**9

    while E.remaining:
        L = get_random_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        cur = objective(res)
        if cur < best_obj:
            best_obj = cur
            best_L = list(L)

        temp = 30.0
        fails = 0
        while fails < 250 and E.remaining:
            temp = max(0.1, temp * 0.995)
            L_cand = mutate_L(L)
            S_cand = E.nullspace([E._J(v, n) for v in L_cand], 2 * n)
            res_cand = E.evaluate(S_cand)
            new_obj = objective(res_cand)
            
            if new_obj < best_obj:
                best_obj = new_obj
                best_L = list(L_cand)

            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = L_cand, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

        # Soft restart using mutated version of the overall best found so far
        if best_L is not None and rng.random() < 0.7:
            L = mutate_L(best_L)
    return None