"""Exact binary evaluator for the controlled pilot; no harvest-dependent targets."""

import numpy as np


def gf2_basis(vecs):
    basis = []
    for value in vecs:
        value = int(value)
        for row in basis:
            value = min(value, value ^ row)
        if value:
            basis.append(value)
            basis.sort(reverse=True)
    return basis


def _J(value, n):
    mask = sum(1 << (2 * i) for i in range(n))
    return ((int(value) & mask) << 1) | ((int(value) >> 1) & mask)


def sform(a, b, n):
    return (int(a) & _J(b, n)).bit_count() & 1


def nullspace(rows, nbits):
    reduced = []
    for value in rows:
        value = int(value)
        for col, row in reduced:
            if (value >> col) & 1:
                value ^= row
        if value:
            pivot = value.bit_length() - 1
            reduced = [(col, row ^ value if (row >> pivot) & 1 else row)
                       for col, row in reduced]
            reduced.append((pivot, value))
    pivots = {col for col, _ in reduced}
    basis = []
    for free in range(nbits):
        if free in pivots:
            continue
        value = 1 << free
        for col, row in reduced:
            if (value & row & ~(1 << col)).bit_count() & 1:
                value |= 1 << col
        basis.append(value)
    return basis


def span_array(basis):
    if len(basis) > 20:
        raise ValueError("enumeration dimension exceeds pilot limit")
    values = np.zeros(1 << len(basis), dtype=np.int64)
    for i, row in enumerate(basis):
        step = 1 << i
        values[step:2 * step] = values[:step] ^ int(row)
    return values


def symplectic_weights(values, n):
    mask = np.uint64(sum(1 << (2 * i) for i in range(n)))
    values = values.astype(np.uint64)
    return np.bitwise_count((values | (values >> np.uint64(1))) & mask).astype(np.int64)


def random_stabilizer(n, s, rng):
    if not 1 <= n <= 20 or not 0 <= s <= 2 * n:
        raise ValueError("invalid generator dimensions")
    generators = []
    while len(generators) < s:
        generators = gf2_basis([*generators, int(rng.integers(1, 1 << (2 * n)))])
    return generators


def evaluate(n, gens, d_target):
    if not isinstance(n, (int, np.integer)) or not 1 <= n <= 20:
        return {"error": "invalid length"}
    basis = gf2_basis(int(g) & ((1 << (2 * n)) - 1) for g in gens)
    s = len(basis)
    if not s or 2 * n - s > 20:
        return {"error": "invalid rank or enumeration dimension"}
    dual = nullspace([_J(row, n) for row in basis], 2 * n)
    # The Gram kernel gives radical coefficients, avoiding enumeration of S.
    gram = [sum(sform(a, b, n) << j for j, b in enumerate(basis)) for a in basis]
    coefficients = nullspace(gram, s)
    radical = []
    for vector in coefficients:
        value = 0
        for j, row in enumerate(basis):
            if (vector >> j) & 1:
                value ^= row
        radical.append(value)
    iso = len(radical)
    c = (s - iso) // 2
    values = span_array(dual)
    logical = ~np.isin(values, span_array(radical))
    weights = symplectic_weights(values, n)[logical]
    return {"n": int(n), "s": s, "c": c, "iso": iso, "k": int(n - s + c),
            "d": int(weights.min()) if len(weights) else None,
            "offending": int((weights < d_target).sum()), "logical_count": len(weights)}
