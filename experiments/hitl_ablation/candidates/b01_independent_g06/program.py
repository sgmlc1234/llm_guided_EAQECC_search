import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    # L of rank n + k - c
    # In training cells: L has n + k - c elements. 
    # For n=9, k=1, c=6, len(L) = 9 + 1 - 6 = 4 vectors.
    # For n=11, k=1, c=8, len(L) = 11 + 1 - 8 = 4 vectors.
    L_len = n + k - c
    
    def get_stabilizer(L):
        # Convert L (size L_len) to S (size s = 2*n - L_len = n - k + c)
        # Swapped rows = [E._J(v, n) for v in L]
        # Nullspace of swapped rows gives the symplectic dual S
        swapped = [E._J(v, n) for v in L]
        dual = E.nullspace(swapped, 2 * n)
        return list(dual)

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        # prioritize correct c, then minimize offending, then maximize distance
        val = 5000 * abs(res["c"] - c) + 10 * res["offending"]
        if res.get("d") is not None:
            val -= res["d"]
        return val

    # Generate a random independent set of size L_len
    def random_L():
        while True:
            cand = []
            for _ in range(L_len):
                # Generate a random non-zero vector
                val = 0
                while val == 0:
                    val = int(rng.integers(1, 1 << (2 * n)))
                cand.append(val)
            if len(E.gf2_basis(cand)) == L_len:
                return cand

    def mutate_L(L):
        # Mutate one element of L
        L_new = list(L)
        idx = int(rng.integers(L_len))
        # Generate a small change
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        L_new[idx] ^= delta
        if len(E.gf2_basis(L_new)) == L_len:
            return L_new
        return None

    while E.remaining:
        L = random_L()
        S = get_stabilizer(L)
        if len(S) != s:
            continue
        res = E.evaluate(S)
        cur = objective(res)
        if res.get("offending") == 0 and res.get("c") == c and res.get("k") == k:
            return S

        temp = 30.0
        fails = 0
        while fails < 400 and E.remaining:
            temp = max(0.1, temp * 0.992)
            L_next = mutate_L(L)
            if L_next is None:
                fails += 1
                continue
            S_next = get_stabilizer(L_next)
            if len(S_next) != s:
                fails += 1
                continue
            
            res_next = E.evaluate(S_next)
            if res_next.get("offending") == 0 and res_next.get("c") == c and res_next.get("k") == k:
                return S_next
                
            new_obj = objective(res_next)
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = L_next, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1

    return None