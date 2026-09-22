import math
import numpy as np

def search(target, max_evals):
    n, k, c = target["n"], target["k"], target["c"]
    s = n - k + c
    len_L = n + k - c

    # We maintain L of size len_L.
    # Its symplectic dual S = nullspace({J(v) for v in L}) has size s = n - k + c.
    # L must have rank len_L and must be isotropic under J (actually, to have s independent stabilizers,
    # and preserve the signature, we can mutate L randomly, extract its symplectic dual S,
    # check if S is valid, evaluate S and minimize distance/offending/c-error).
    
    def get_S(L_basis):
        # L_basis is a list/array of len_L integers
        # J(v) is E._J(v, n)
        rows = [E._J(v, n) for v in L_basis]
        dual = E.nullspace(rows, 2 * n)
        return dual

    def objective(res):
        if res is None or res.get("offending") is None or res.get("c") is None:
            return 10**9
        # prioritize offending = 0, then c close to target c
        return 5000 * abs(res["c"] - c) + res["offending"]

    # Generate a random initial L of rank len_L
    # We can do this by taking a random stabilizer of size len_L
    def random_L():
        while True:
            cand = list(E.random_stabilizer(n, len_L, rng))
            if len(E.gf2_basis(cand)) == len_L:
                return cand

    L = random_L()
    S = get_S(L)
    cur_res = E.evaluate(S)
    cur_val = objective(cur_res)

    def mutate_L(L_curr):
        # Mutate one element of L
        L_new = list(L_curr)
        idx = rng.integers(len_L)
        # Random Pauli modification
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        L_new[idx] ^= delta
        return L_new

    temp = 30.0
    fails = 0
    
    while E.remaining:
        # Periodically restart to avoid local minima
        if fails > 800:
            L = random_L()
            S = get_S(L)
            cur_res = E.evaluate(S)
            cur_val = objective(cur_res)
            fails = 0
            temp = 30.0
            continue

        temp = max(0.05, temp * 0.995)
        L_cand = mutate_L(L)
        if len(E.gf2_basis(L_cand)) != len_L:
            fails += 1
            continue
            
        S_cand = get_S(L_cand)
        if len(S_cand) != s:
            fails += 1
            continue
            
        res = E.evaluate(S_cand)
        val = objective(res)
        
        delta = val - cur_val
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            L, cur_val = L_cand, val
            fails = 0 if delta < 0 else fails + 1
        else:
            fails += 1
            
    return None