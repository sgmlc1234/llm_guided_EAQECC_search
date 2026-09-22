import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    m = n + k - c

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
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    # Initialize L with m linearly independent random vectors
    while E.remaining:
        L = []
        for _ in range(m):
            while True:
                v = int(rng.integers(1, 1 << (2 * n)))
                test_L = L + [v]
                if len(E.gf2_basis(test_L)) == len(test_L):
                    L.append(v)
                    break
        
        S = get_S(L)
        cur_obj = objective(E.evaluate(S))
        if cur_obj == 0:
            return S

        temp, fails = 30.0, 0
        while fails < 2000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(m))
            candidate_L = list(L)
            if rng.random() < 0.2:
                candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))
            else:
                candidate_L[idx] ^= random_pauli()
            
            if len(E.gf2_basis(candidate_L)) != m:
                fails += 1
                continue
                
            cand_S = get_S(candidate_L)
            new_obj = objective(E.evaluate(cand_S))
            if new_obj == 0:
                return cand_S
                
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None