# Arm B0 — the pre-evolution human baseline.
#
# Reconstructed from the seed heuristic quoted in eaqecc_family_main.tex
# (Section "How the family was found"): unstructured random stabilizer
# start, simulated annealing on 5000*|c - c_t| + offending, moves = XOR one
# generator with a random Pauli on 1-2 qubits.
#
# The SA loop parameters (temp 30.0, decay 0.995, 1500 non-improving moves)
# are taken verbatim from program.py so that the ONLY difference between
# this arm and B1 is the structured construction ansatz. Everything else --
# target schedule, objective, move set, return convention -- is identical.
#
# Execution contract is the campaign's: E, TARGETS, np, rng, TIME_BUDGET_S
# are provided in the namespace; search() returns up to 16 (target_index,
# gens) pairs.

import math
import time


def search():
    t0 = time.time()
    best = {}  # target_index -> (objective, gens)

    weights = np.array([1.0 / (t["n"] ** 2) for t in TARGETS])
    weights /= weights.sum()

    def objective(res, t):
        if "error" in res:
            return 10**9
        return 5000 * abs(res["c"] - t["c"]) + res["offending"]

    def random_pauli(n, w_min, w_max):
        qubits = rng.choice(n, size=int(rng.integers(w_min, w_max + 1)),
                            replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    while time.time() - t0 < TIME_BUDGET_S:
        ti = int(rng.choice(len(TARGETS), p=weights))
        t = TARGETS[ti]
        n, s = t["n"], t["n"] - t["k"] + t["c"]

        gens = list(E.random_stabilizer(n, s, rng))   # unstructured start
        res = E.evaluate(n, gens, t["d"])
        cur = objective(res, t)
        if cur < best.get(ti, (10**9, None))[0]:
            best[ti] = (cur, list(gens))
        if cur == 0:
            continue

        state = list(gens)
        temp, fails = 30.0, 0
        while fails < 1500 and time.time() - t0 < TIME_BUDGET_S:
            temp = max(0.1, temp * 0.995)
            new_state = list(state)
            new_state[int(rng.integers(s))] ^= random_pauli(n, 1, 2)
            if len(E.gf2_basis(new_state)) != s:
                fails += 1
                continue
            res2 = E.evaluate(n, new_state, t["d"])
            o2 = objective(res2, t)
            dlt = o2 - cur
            if dlt <= 0 or rng.random() < math.exp(-dlt / temp):
                state, cur = new_state, o2
                fails = 0 if dlt < 0 else fails + 1
                if o2 < best.get(ti, (10**9, None))[0]:
                    best[ti] = (o2, list(state))
                if cur == 0:
                    break
            else:
                fails += 1

    ranked = sorted(best.items(), key=lambda kv: kv[1][0])
    return [(ti, gens) for ti, (_, gens) in ranked[:16]]
