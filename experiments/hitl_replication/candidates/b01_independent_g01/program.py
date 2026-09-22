import math

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c_target = target["c"]
    s = n - k + c_target
    l_size = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    while E.remaining:
        # Initialize L with linearly independent vectors
        L = []
        while len(L) < l_size:
            val = int(rng.integers(1, 1 << (2 * n)))
            if len(E.gf2_basis(L + [val])) == len(L) + 1:
                L.append(val)

        S = get_S(L)
        cur = objective(E.evaluate(S))
        temp = 30.0
        fails = 0

        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(l_size))

            # Apply local or global mutation
            if rng.random() < 0.7:
                qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
                delta_val = 0
                for q in qubits:
                    delta_val |= int(rng.integers(1, 4)) << (2 * int(q))
                candidate_L[idx] ^= delta_val
            else:
                candidate_L[idx] = int(rng.integers(1, 1 << (2 * n)))

            if len(E.gf2_basis(candidate_L)) != l_size:
                fails += 1
                continue

            S_cand = get_S(candidate_L)
            res_cand = E.evaluate(S_cand)
            new_obj = objective(res_cand)

            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L = candidate_L
                cur = new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None