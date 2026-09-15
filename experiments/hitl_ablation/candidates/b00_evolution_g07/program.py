import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    r_L = n + k - c
    s = n - k + c
    target_d = target["d"]

    def symp_weight(v):
        w = 0
        for i in range(n):
            if (v >> (2 * i)) & 3:
                w += 1
        return w

    def get_S(L):
        J_L = [E._J(v, n) for v in L]
        return E.nullspace(J_L, 2 * n)

    def random_vector():
        val = 0
        while val == 0:
            for i in range(n):
                val |= int(rng.integers(0, 4)) << (2 * i)
        return val

    def mutate_vector(v):
        v_new = v
        num_muts = int(rng.choice([1, 2, 3], p=[0.7, 0.2, 0.1]))
        for _ in range(num_muts):
            q = int(rng.integers(0, n))
            op = int(rng.integers(1, 4))
            v_new ^= (op << (2 * q))
        return v_new

    def init_L():
        while True:
            candidate = [random_vector() for _ in range(r_L)]
            if len(E.gf2_basis(candidate)) == r_L:
                return candidate

    def analyze_L(L):
        # Compute the span of J(L)
        JL = [E._J(v, n) for v in L]
        span_JL = [0]
        for v in JL:
            span_JL += [x ^ v for x in span_JL]
        
        # Identify radical of J(L) under symplectic form
        radical = []
        for x in span_JL:
            is_radical = True
            for y in JL:
                if E.sform(x, y, n):
                    is_radical = False
                    break
            if is_radical:
                radical.append(x)
        
        rad_dim = int(math.log2(len(radical)))
        
        # Compute local distance
        min_d = 999
        radical_set = set(radical)
        for x in span_JL:
            if x not in radical_set:
                w = symp_weight(x)
                if w < min_d:
                    min_d = w
        return rad_dim, min_d

    # Generate and filter candidates purely offline until we find a match
    while E.remaining:
        L = init_L()
        stagnant = 0
        while stagnant < 100:
            rad_dim, d_local = analyze_L(L)
            # If we match the required parameters, evaluate
            if rad_dim == n - k - c and d_local >= target_d:
                S = get_S(L)
                if len(S) == s:
                    res = E.evaluate(S)
                    if res and res.get("offending") == 0 and res.get("c") == c and res.get("d", 0) >= target_d:
                        return S
            
            # Mutate L
            new_L = list(L)
            mut_idx = int(rng.integers(r_L))
            if rng.random() < 0.15:
                new_L[mut_idx] = random_vector()
            else:
                new_L[mut_idx] = mutate_vector(new_L[mut_idx])
            
            if len(E.gf2_basis(new_L)) == r_L:
                L = new_L
                stagnant = 0
            else:
                stagnant += 1

    return None