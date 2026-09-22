import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    m = n + k - c  # Rank of L, which is 4 for these training cells

    def L_to_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

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
        # Initialize L as a random independent set of size m
        L = []
        while len(L) < m:
            v = int(rng.integers(1, 1 << (2 * n)))
            candidate = L + [v]
            if len(E.gf2_basis(candidate)) == len(candidate):
                L.append(v)
        
        S = L_to_S(L)
        cur = objective(E.evaluate(S))
        temp = 30.0
        fails = 0
        
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(m))
            old_val = L[idx]
            
            # Mutate: either a completely new random vector or a small perturbation
            if rng.random() < 0.3:
                new_val = int(rng.integers(1, 1 << (2 * n)))
            else:
                new_val = old_val ^ random_pauli()
            
            L[idx] = new_val
            if len(E.gf2_basis(L)) != m:
                L[idx] = old_val
                fails += 1
                continue
                
            S = L_to_S(L)
            new_obj = objective(E.evaluate(S))
            delta = new_obj - cur
            
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
    return None