import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    l_len = n + k - c
    s_len = n - k + c

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

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    while E.remaining:
        # Generate a random independent basis L of size l_len
        L = []
        while len(L) < l_len:
            v = int(rng.integers(1, 1 << (2 * n)))
            test = L + [v]
            if len(E.gf2_basis(test)) == len(test):
                L.append(v)
        
        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp = 30.0
        fails = 0
        
        while fails < 1000 and E.remaining:
            temp = max(0.1, temp * 0.995)
            idx = int(rng.integers(l_len))
            old_val = L[idx]
            
            # Mutate L[idx]
            if rng.random() < 0.5:
                L[idx] ^= random_pauli()
            else:
                L[idx] = int(rng.integers(1, 1 << (2 * n)))
                
            if len(E.gf2_basis(L)) != l_len:
                L[idx] = old_val
                fails += 1
                continue
                
            S = get_S(L)
            new_obj = objective(E.evaluate(S))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
    return None