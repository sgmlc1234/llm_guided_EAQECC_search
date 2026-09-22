import math

def search(target, max_evals):
    n, k, c_target, d_target = target["n"], target["k"], target["c"], target["d"]
    s = n - k + c_target
    l_size = n + k - c_target

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        val = 5000 * abs(res["c"] - c_target) + 100 * res["offending"]
        if res.get("d") is not None:
            val += max(0, d_target - res["d"]) * 10
        return val

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Generate a random independent L of size l_size
        while E.remaining:
            L = []
            for _ in range(l_size):
                L.append(int(rng.integers(1, 1 << (2 * n))))
            if len(E.gf2_basis(L)) == l_size:
                break
        
        if not E.remaining:
            break
            
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l_size))
            candidate_L[idx] ^= random_pauli()
            if len(E.gf2_basis(candidate_L)) != l_size:
                fails += 1
                continue
            
            cand_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None