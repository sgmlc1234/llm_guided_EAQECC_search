import math
import numpy as np

def search(target, max_evals):
    n = target["n"]
    k = target["k"]
    c = target["c"]
    s = n - k + c
    l_size = 2 * n - s
    
    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        c_diff = abs(res.get("c", 0) - c)
        off = res.get("offending", 2 * n)
        d = res.get("d")
        if d is None:
            d = 0
        return 1000 * c_diff + 100 * off - d

    def get_S(L):
        rows = [E._J(v, n) for v in L]
        return E.nullspace(rows, 2 * n)

    def random_L():
        L = []
        while len(L) < l_size:
            v = int(rng.integers(1, 1 << (2 * n)))
            candidate = L + [v]
            if len(E.gf2_basis(candidate)) == len(candidate):
                L.append(v)
        return L

    L = random_L()
    S = get_S(L)
    cur_obj = objective(E.evaluate(S))

    temp = 10.0
    fails = 0
    
    while E.remaining:
        new_L = list(L)
        idx = int(rng.integers(l_size))
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        
        new_L[idx] ^= delta
        if len(E.gf2_basis(new_L)) != l_size:
            continue
            
        new_S = get_S(new_L)
        res = E.evaluate(new_S)
        new_obj = objective(res)
        
        if res.get("c") == c and res.get("offending") == 0 and res.get("d", 0) >= target["d"]:
            return new_S
            
        delta_obj = new_obj - cur_obj
        if delta_obj <= 0 or rng.random() < math.exp(-delta_obj / temp):
            L = new_L
            cur_obj = new_obj
            fails = 0
        else:
            fails += 1
            
        temp = max(0.01, temp * 0.999)
        if fails > 300:
            L = random_L()
            S = get_S(L)
            cur_obj = objective(E.evaluate(S))
            temp = 10.0
            fails = 0

    return None