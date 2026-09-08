# Seed program for the AlphaEvolve EAQECC construction-ansatz campaign (run 9).
#
# TARGETS: 329 open parameter points of the codetables.de qubit EAQECC table
# (5 <= n <= 13), each {n, k, c, d, dl, kind}. Two kinds:
#   kind="gap":    a listed entry with dl < d <= corrected upper bound;
#   kind="record": an (n, k, c) cell ABSENT from the table, where achieving
#                  d beats the monotone staircase of known codes.
# Every target's d respects the EA-Plotkin bound (4^k-1) d <= 3*4^{k-1} n and
# EA-Singleton, and eight SAT/exhaustion-proven-nonexistent points are
# excluded — every target is genuinely open and possibly achievable.
#
# Campaign intel (what has actually worked):
#  * A CYCLIC-SHIFT ansatz (generators = 2-bit cyclic shifts of one or two
#    base Pauli strings) discovered [[7,1,6;4]], [[9,1,8;6]], [[11,1,10;8]] —
#    later generalized by hand into the odd-n family [[n,1,n-1;n-3]].
#  * A BLOCK ansatz (radical <X^b, Z^b> on a b-qubit block, logical operators
#    = "transversal" one-of-each-Pauli patterns on the block times uniform
#    tails) yielded the even-n branch of the same family.
#  Both wins came from STRUCTURED CONSTRUCTION PROGRAMS, not from point
#  search: an ansatz that works for one (n, k, c) tends to sweep a whole
#  ladder of targets. Evolve the ansatz library — new structural families
#  (quasi-cyclic with other shift steps, multi-block radicals, GF(4)-additive
#  constructions, extension/shortening of already-closed codes, hyperbolic
#  pairs + isotropic completion) — more than the local-search loop.
#
# Representation: a stabilizer set on n qubits is a list of s = n - k + c
# integers, 2n bits each; per qubit i, bit 2i = X part, bit 2i+1 = Z part.
# Span S must have symplectic Gram rank exactly 2c; d = min symplectic
# weight over S^perp \ S_iso. You may also build the SMALL side L = S^perp
# (dim n + k - c) as a list of Pauli integers and convert:
#   gens = E.nullspace([E._J(v, n) for v in L_basis], 2 * n).
#
# Execution contract (provided in the namespace — do NOT import):
#   E            E.evaluate(n, gens, d_target) -> {n, s, c, iso, k, d,
#                offending} (exact; ~1-20 ms). E.random_stabilizer(n, s,
#                rng), E.sform(u, v, n), E.gf2_basis(vecs),
#                E.symplectic_weights(np_array, n), E.nullspace(rows, nbits),
#                E._J(v, n), E.TARGETS.
#   TARGETS      list of dicts {n, k, c, d, dl, kind}
#   np, rng, TIME_BUDGET_S    as usual
#
# search() must return a list of up to 16 pairs (target_index, gens).
# The evaluator re-verifies exactly; per-candidate score is
# (1000 - offending) when (k, c) match [-5000*|c - c_t| - 1000 when not],
# +1e6 jackpot per target closed (new best-known EAQECC). Numeric care:
# build integers with Python ints; avoid numpy int accumulation of masks.

import math
import itertools
import time


# EVOLVE-BLOCK-START
def search():
    """Construction-ansatz search over 329 open EAQECC parameter points.

    Policy: repeatedly pick a target and instantiate one of three
    strategies — (A) cyclic-shift ansatz on the S side, (B) block-radical /
    transversal ansatz on the L side (the two proven winners), (C) random
    stabilizer + simulated-annealing repair (fallback). Improve on this:
    richer ansatz families, parameter transfer between targets that share
    structure, smarter target scheduling, coupled moves, exactness repair.
    """
    t0 = time.time()
    best = {}  # target_index -> (objective, gens)

    weights = np.array([1.0 / (t["n"] ** 2) for t in TARGETS])
    weights /= weights.sum()

    def objective(res, t):
        if "error" in res:
            return 10**9
        return 5000 * abs(res["c"] - t["c"]) + 1000 * abs(res["k"] - t["k"]) \
            + res["offending"]

    def consider(ti, gens, res, t):
        o = objective(res, t)
        if o < best.get(ti, (10**9, None))[0]:
            best[ti] = (o, list(gens))
        return o

    mask = lambda n: (1 << (2 * n)) - 1

    def shift_gens(bases, n, s, step=2):
        gens = []
        counts = [s // len(bases) + (1 if i < s % len(bases) else 0)
                  for i in range(len(bases))]
        for g, cnt in zip(bases, counts):
            for i in range(cnt):
                shift = (step * i) % (2 * n)
                gens.append(((g << shift) | (g >> (2 * n - shift))) & mask(n))
        return gens

    def random_pauli(n, w_min, w_max):
        qubits = rng.choice(n, size=int(rng.integers(w_min, w_max + 1)),
                            replace=False)
        delta = 0
        for q in qubits:
            delta |= int(rng.integers(1, 4)) << (2 * int(q))
        return delta

    PAULI = {"I": 0, "X": 1, "Z": 2, "Y": 3}

    def pat(codes, n):
        v = 0
        for q, p in enumerate(codes):
            v |= PAULI[p] << (2 * q)
        return v

    def block_L(t):
        """Block-radical + transversal-logical ansatz for the L side.
        Works when dim L = n + k - c is small (<= ~8)."""
        n, k, c = t["n"], t["k"], t["c"]
        dimL = n + k - c
        j = dimL - 2 * k          # radical dimension
        if j < 0 or dimL > 8:
            return None
        b = int(rng.choice([2, 4, 6]))
        if b > n:
            return None
        L = []
        # radical: uniform strings on the block (X^b, Z^b, and shifts)
        rad_pool = ["X" * b, "Z" * b, "Y" * b,
                    "XZ" * (b // 2), "ZX" * (b // 2)]
        rng.shuffle(rad_pool)
        for i in range(j):
            L.append(pat(rad_pool[i % len(rad_pool)], n))
        # hyperbolic pairs: transversal-ish block patterns x uniform tails
        tails = ["X", "Z", "Y"]
        rng.shuffle(tails)
        for i in range(k):
            blk1 = list("IXYZ" * (b // 4 + 1))[:b]
            blk2 = list("IZXY" * (b // 4 + 1))[:b]
            rng.shuffle(blk1)
            rng.shuffle(blk2)
            u = pat("".join(blk1) + tails[0] * (n - b), n)
            v = pat("".join(blk2) + tails[1] * (n - b), n)
            L += [u, v]
        if len(E.gf2_basis(L)) != dimL:
            return None
        return E.nullspace([E._J(v, n) for v in L], 2 * n)

    while time.time() - t0 < TIME_BUDGET_S:
        ti = int(rng.choice(len(TARGETS), p=weights))
        t = TARGETS[ti]
        n, s = t["n"], t["n"] - t["k"] + t["c"]

        strategy = rng.random()
        gens = None
        if strategy < 0.40 and s <= 2 * n:            # (A) quasi-cyclic shifts
            nb = 1 + int(rng.integers(3))
            step = int(rng.choice([2, 4, 6]))
            bases = [int(rng.integers(1, 1 << (2 * n))) for _ in range(nb)]
            gens = shift_gens(bases, n, s, step=step)
        elif strategy < 0.70:                          # (B) block ansatz
            gens = block_L(t)
        
        # Ensure we have a valid starting basis of size s
        if gens is None or len(E.gf2_basis(gens)) != s:  # (C) fallback
            gens = list(E.random_stabilizer(n, s, rng))

        res = E.evaluate(n, gens, t["d"])
        cur = consider(ti, gens, res, t)
        if cur == 0:
            continue

        # SA repair
        state = list(gens)
        temp, fails = 30.0, 0
        while fails < 1500 and time.time() - t0 < TIME_BUDGET_S:
            temp = max(0.1, temp * 0.995)
            new_state = list(state)
            if rng.random() < 0.2 and s >= 2:
                g1, g2 = rng.choice(s, 2, replace=False)
                new_state[g1] ^= new_state[g2]
            else:
                new_state[int(rng.integers(s))] ^= random_pauli(n, 1, 3)
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
# EVOLVE-BLOCK-END
