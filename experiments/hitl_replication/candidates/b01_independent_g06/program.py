import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_size = n + k - c

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    while E.remaining:
        # Initialize L
        L = []
        while len(L) < l_size:
            cand = int(rng.integers(1, 1 << (2 * n)))
            test_L = L + [cand]
            if len(E.gf2_basis(test_L)) == len(test_L):
                L.append(cand)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp, fails = 30.0, 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l_size))
            if rng.random() < 0.5:
                candidate_L[idx] ^= random_pauli()
            else:
                candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
            
            if len(E.gf2_basis(candidate_L)) != l_size:
                fails += 1
                continue
                
            cand_S = get_S(candidate_L)
            new_obj = objective(E.evaluate(cand_S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None