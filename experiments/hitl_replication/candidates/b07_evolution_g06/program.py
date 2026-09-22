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

    def random_low_weight():
        w = 1 if rng.random() < 0.6 else 2
        v = 0
        for _ in range(w):
            q = int(rng.integers(n))
            v ^= int(rng.integers(1, 4)) << (2 * q)
        return v

    def mutate_L(L):
        for _ in range(10):
            L_new = list(L)
            idx = int(rng.integers(num_L))
            r = rng.random()
            if r < 0.5:
                L_new[idx] ^= random_low_weight()
            elif r < 0.8:
                other = int(rng.integers(num_L))
                if other != idx:
                    L_new[idx] ^= L_new[other]
            else:
                L_new[idx] = int(rng.integers(1, 1 << (2 * n)))
            if len(E.gf2_basis(L_new)) == num_L:
                return L_new
        return L

    population = []
    max_pop = 6

    while E.remaining:
        if len(population) < 2 or rng.random() < 0.2:
            L = get_random_L()
        else:
            # Select from population with tournament selection or simple choice
            base = rng.choice(population)
            L = mutate_L(base[1])
            
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        cur_obj = objective(res)
        
        # Maintain population sorted by objective
        population.append((cur_obj, L))
        population.sort(key=lambda x: x[0])
        if len(population) > max_pop:
            population.pop()

        # Local search around current
        fails = 0
        temp = 20.0
        while fails < 120 and E.remaining:
            temp = max(0.05, temp * 0.98)
            L_cand = mutate_L(L)
            S_cand = E.nullspace([E._J(v, n) for v in L_cand], 2 * n)
            res_cand = E.evaluate(S_cand)
            new_obj = objective(res_cand)

            # Add to population
            population.append((new_obj, L_cand))
            population.sort(key=lambda x: x[0])
            if len(population) > max_pop:
                population.pop()

            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = L_cand, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None