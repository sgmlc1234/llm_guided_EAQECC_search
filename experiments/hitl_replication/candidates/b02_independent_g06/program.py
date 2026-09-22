import math

def search(target, max_evals):
    n, k, target_c = target["n"], target["k"], target["c"]
    # Rank of L is n + k - c
    rank_L = n + k - target_c
    
    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target_c) + res["offending"]

    def random_vector():
        # Generate a random binary vector of length 2n represented as an integer
        return int(rng.integers(1, 1 << (2 * n)))

    def mutate_L(L):
        cand = list(L)
        idx = int(rng.integers(len(L)))
        # Either small perturbation or complete replacement
        if rng.random() < 0.7:
            qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
            delta = 0
            for q in qubits:
                delta |= int(rng.integers(1, 4)) << (2 * int(q))
            cand[idx] ^= delta
        else:
            cand[idx] = random_vector()
        return cand

    # Try starting from incumbent if available
    initial_L = None
    if E.incumbent is not None:
        # S is available, construct L as nullspace of J(S)
        S = E.incumbent
        try:
            initial_L = E.nullspace([E._J(v, n) for v in S], 2 * n)[:rank_L]
        except Exception:
            pass

    while E.remaining:
        if initial_L is not None and len(E.gf2_basis(initial_L)) == rank_L:
            L = list(initial_L)
            initial_L = None
        else:
            while True:
                L = [random_vector() for _ in range(rank_L)]
                if len(E.gf2_basis(L)) == rank_L:
                    break
        
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == target_c:
            return S
            
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            cand_L = mutate_L(L)
            if len(E.gf2_basis(cand_L)) != rank_L:
                fails += 1
                continue
            
            cand_S = E.nullspace([E._J(v, n) for v in cand_L], 2 * n)
            res = E.evaluate(cand_S)
            new_obj = objective(res)
            if res.get("offending") == 0 and res.get("c") == target_c:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = cand_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
                
    return None