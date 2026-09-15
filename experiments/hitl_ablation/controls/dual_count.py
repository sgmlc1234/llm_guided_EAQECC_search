"""Researcher-assisted small-side variant of the fixed annealing baseline.

Search a basis of L = S-perp, rather than a basis of S. The random restart,
Pauli move, temperature and stagnation rules match seed_naive_sa.py.
No witness, family formula, or target-specific pattern is embedded.
"""

import math


def search(target, max_evals):
    n = target["n"]
    rank = n + target["k"] - target["c"]

    def objective(result):
        if result.get("offending") is None or result.get("c") is None:
            return 10**9
        return 5000 * abs(result["c"] - target["c"]) + result["offending"]

    def evaluate(basis):
        generators = E.nullspace([E._J(row, n) for row in basis], 2 * n)
        return E.evaluate(generators)

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while E.remaining:
        state = list(E.random_stabilizer(n, rank, rng))
        cur = objective(evaluate(state))
        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate = list(state)
            candidate[int(rng.integers(rank))] ^= random_pauli()
            if len(E.gf2_basis(candidate)) != rank:
                fails += 1
                continue
            new_obj = objective(evaluate(candidate))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                state, cur = candidate, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    return None
