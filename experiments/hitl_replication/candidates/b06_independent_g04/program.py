import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    l_len = 2 * n - s

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c) + res["offending"]

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def random_vector():
        val = 0
        for i in range(n):
            val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def generate_random_L():
        basis = []
        while len(basis) < l_len:
            v = random_vector()
            temp = basis + [v]
            if len(E.gf2_basis(temp)) == len(temp):
                basis.append(v)
        return basis

    while E.remaining:
        L = generate_random_L()
        S = get_S(L)
        cur_obj = objective(E.evaluate(S))
        
        temp, fails = 30.0, 0
        while fails < 1000 and E.remaining:
            temp = max(0.05, temp * 0.995)
            idx = int(rng.integers(l_len))
            old_val = L[idx]
            
            # Mutate: either replace completely or XOR with a random Pauli
            if rng.random() < 0.5:
                L[idx] = random_vector()
            else:
                L[idx] ^= random_vector()
                
            if len(E.gf2_basis(L)) != l_len:
                L[idx] = old_val
                fails += 1
                continue
                
            S = get_S(L)
            new_obj = objective(E.evaluate(S))
            delta = new_obj - cur_obj
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                cur_obj = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                L[idx] = old_val
                fails += 1
    return None