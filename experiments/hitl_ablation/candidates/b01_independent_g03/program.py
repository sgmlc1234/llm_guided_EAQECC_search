import math

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    d_target = target["d"]
    s = n - k + c_target
    m = 2 * n - s  # Dimension of L

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        dist = res.get("d")
        dist_penalty = max(0, d_target - dist) if dist is not None else d_target
        return 10000 * abs(res["c"] - c_target) + 100 * res["offending"] + dist_penalty

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        # Symplectic orthogonal complement of L
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    while E.remaining:
        # Generate initial linearly independent L
        L = []
        while len(L) < m:
            cand = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [cand]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(cand)
        
        S = get_S(L)
        res = E.evaluate(S)
        cur = objective(res)
        
        # Check if we hit a solution right away
        if res and res.get("offending") == 0 and res.get("c") == c_target and res.get("d", 0) >= d_target:
            return S

        temp = 50.0
        fails = 0
        while fails < 1500 and E.remaining:
            temp = max(0.05, temp * 0.995)
            idx = int(rng.integers(m))
            cand_val = L[idx] ^ random_pauli()
            if cand_val == 0:
                fails += 1
                continue
            
            candidate_L = list(L)
            candidate_L[idx] = cand_val
            if len(E.gf2_basis(candidate_L)) != m:
                fails += 1
                continue
            
            cand_S = get_S(candidate_L)
            cand_res = E.evaluate(cand_S)
            new_obj = objective(cand_res)
            
            if cand_res and cand_res.get("offending") == 0 and cand_res.get("c") == c_target and cand_res.get("d", 0) >= d_target:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None