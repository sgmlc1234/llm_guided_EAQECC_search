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
        return 10000 * c_diff + 200 * off + d_score

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
                qubit = int(rng.integers(n))
                delta = int(rng.integers(1, 4)) << (2 * qubit)
                L_new[idx] ^= delta
            elif choice == 2:
                other = int(rng.integers(num_L))
                if other != idx:
                    L_new[idx] ^= L_new[other]
            else:
                # Small perturbation on up to 2 qubits
                for _ in range(rng.integers(1, 3)):
                    qubit = int(rng.integers(n))
                    delta = int(rng.integers(1, 4)) << (2 * qubit)
                    L_new[idx] ^= delta
            if len(E.gf2_basis(L_new)) == num_L:
                return L_new
        return L

    # Maintain a pool of best solutions to avoid getting stuck
    pool_size = 4
    pool = []
    
    while len(pool) < pool_size and E.remaining:
        L = get_random_L()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        obj = objective(res)
        pool.append((obj, L))
    
    pool.sort(key=lambda x: x[0])

    while E.remaining:
        # Select one from the pool with bias towards better candidates
        parent_idx = int(rng.choice(len(pool), p=[0.4, 0.3, 0.2, 0.1][:len(pool)]))
        parent_obj, parent_L = pool[parent_idx]
        
        L_cand = mutate_L(parent_L)
        S_cand = E.nullspace([E._J(v, n) for v in L_cand], 2 * n)
        res_cand = E.evaluate(S_cand)
        new_obj = objective(res_cand)
        
        if new_obj < parent_obj:
            pool[parent_idx] = (new_obj, L_cand)
            pool.sort(key=lambda x: x[0])
        elif rng.random() < 0.15:
            # Accept slightly worse candidates to explore
            pool[parent_idx] = (new_obj, L_cand)
            pool.sort(key=lambda x: x[0])
            
        # Periodic restart of the worst element to maintain diversity
        if rng.random() < 0.05 and len(pool) == pool_size:
            pool[-1] = (objective(E.evaluate(E.nullspace([E._J(v, n) for v in get_random_L()], 2 * n))), get_random_L())
            pool.sort(key=lambda x: x[0])
            
    return None