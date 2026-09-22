import math

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    dim_L = 2 * n - s

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return list(E.nullspace(rows, 2 * n))

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # Primary: minimize c mismatch, secondary: minimize offending generators
        # tertiary: maximize distance
        val = 10000 * abs(res["c"] - c) + 100 * res["offending"]
        if res.get("d") is not None:
            val -= res["d"]
        return val

    def random_element():
        return int(rng.integers(0, 1 << (2 * n)))

    while E.remaining:
        # Initialize L with linearly independent vectors
        L = []
        while len(L) < dim_L:
            cand = random_element()
            if len(E.gf2_basis(L + [cand])) == len(L) + 1:
                L.append(cand)

        S = get_S(L)
        cur_res = E.evaluate(S)
        cur_obj = objective(cur_res)

        temp, fails = 50.0, 0
        while fails < 2000 and E.remaining:
            temp = max(0.01, temp * 0.998)
            candidate_L = list(L)
            idx = int(rng.integers(dim_L))
            
            # Mutate: either replace, or perturb with small weight Pauli
            if rng.random() < 0.3:
                candidate_L[idx] = random_element()
            else:
                # XOR with another element or a random single-qubit Pauli
                q = int(rng.integers(n))
                p = int(rng.integers(1, 4)) << (2 * q)
                candidate_L[idx] ^= p

            if len(E.gf2_basis(candidate_L)) != dim_L:
                fails += 1
                continue

            cand_S = get_S(candidate_L)
            res = E.evaluate(cand_S)
            new_obj = objective(res)
            delta = new_obj - cur_obj

            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur_obj = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None