import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_rank = n + k - c

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        # Generate a random independent basis L of rank l_rank
        while True:
            L = []
            for _ in range(l_rank):
                # Generate random elements
                qubits = rng.choice(n, size=int(rng.integers(1, n // 2 + 1)), replace=False)
                val = 0
                for q in qubits:
                    val |= int(rng.integers(1, 4)) << (2 * int(q))
                L.append(val)
            if len(E.gf2_basis(L)) == l_rank:
                break
        
        # Convert L to S
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        if len(S) != s:
            continue
        
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l_rank))
            candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != l_rank:
                fails += 1
                continue
                
            cand_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
            if len(cand_S) != s:
                fails += 1
                continue
                
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None