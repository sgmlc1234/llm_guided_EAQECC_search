"""Refine the protected starting state, then use the same annealing heuristic."""

import math


def search(target, max_evals):
    n, s = target["n"], target["n"] - target["k"] + target["c"]

    def objective(res):
        if res.get("offending") is None or res.get("c") is None:
            return 10**9
        return 5000 * abs(res["c"] - target["c"]) + res["offending"]

    def random_pauli():
        qubits = rng.choice(n, size=int(rng.integers(1, 3)), replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    initial_state = E.incumbent
    initial_measurement = E.incumbent_parameters
    while E.remaining:
        if initial_state is not None:
            state = initial_state
            cur = objective(initial_measurement)
            initial_state = None
        else:
            state = list(E.random_stabilizer(n, s, rng))
            cur = objective(E.evaluate(state))
        temp, fails = 30.0, 0
        while fails < 1500 and E.remaining:
            temp = max(0.1, temp * 0.995)
            candidate = list(state)
            candidate[int(rng.integers(s))] ^= random_pauli()
            if len(E.gf2_basis(candidate)) != s:
                fails += 1
                continue
            new_obj = objective(E.evaluate(candidate))
            delta = new_obj - cur
            if delta <= 0 or rng.random() < math.exp(-delta / temp):
                state, cur = candidate, new_obj
                fails = 0 if delta < 0 else fails + 1
            else:
                fails += 1
    # The trusted driver retains the best verified candidate from E.evaluate.
    return None
