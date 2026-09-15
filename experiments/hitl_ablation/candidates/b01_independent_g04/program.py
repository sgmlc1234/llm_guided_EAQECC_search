import math

def search(target, max_evals):
    n, k, c_target = target["n"], target["k"], target["c"]
    s = n - k + c_target
    r_L = n + k - c_target # which is 4 for these cases

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - c_target) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 4)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    def get_L_basis():
        while True:
            candidate = [int(rng.integers(0, 1 << (2 * n))) for _ in range(r_L)]
            if len(E.gf2_basis(candidate)) == r_L:
                return candidate

    while E.remaining:
        L = get_L_basis()
        S = E.nullspace([E._J(v, n) for v in L], 2 * n)
        cur = objective(E.evaluate(S))
        temp, fails = 40.0, 0
        
        while fails < 1200 and E.remaining:
            temp = max(0.05, temp * 0.995)
            candidate_L = list(L)
            idx = int(rng.integers(r_L))
            if rng.random() < 0.5:
                candidate_L[idx] ^= random_pauli()
            else:
                candidate_L[idx] = int(rng.integers(0, 1 << (2 * n)))
            
            if len(E.gf2_basis(candidate_L)) != r_L:
                fails += 1
                continue
            
            cand_S = E.nullspace([E._J(v, n) for v in candidate_L], 2 * n)
            eval_res = E.evaluate(cand_S)
            new_obj = objective(eval_res)
            
            if eval_res.get("offending") == 0 and eval_res.get("c") == c_target and eval_res.get("d") is not None and eval_res.get("d") >= target["d"]:
                return cand_S
                
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                L, cur = candidate_L, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None