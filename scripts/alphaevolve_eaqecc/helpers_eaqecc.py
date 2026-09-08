"""Fixed exact machinery for the AlphaEvolve EAQECC campaign.

Formalism (binary symplectic representation, qubit codes): a stabilizer set
is a list of s integers, each 2n bits, bit layout per qubit i:
bit 2i = X-part a_i, bit 2i+1 = Z-part b_i. Symplectic product
<u,v> = sum_i (a_i b'_i + b_i a'_i) mod 2. Symplectic weight = number of
qubits acted on (pair != 00).

Given S = span(gens) with dim s on n qubits:
  2c   = rank of the symplectic Gram matrix on S   (c ebits)
  iso  = s - 2c = dim of the radical S_iso = S ∩ S^perp
  k    = n - s + c   (logical qubits)
  d    = min symplectic weight over S^perp \\ S_iso
This is the convention behind the codetables.de EAQECC tables
(Luo-Ezerman-Grassl-Ling, arXiv:2207.05647). Verified against the proven
facts d(5,2;3)=3 and d(6,2;4)=4.

evaluate(n, gens, d_target) enumerates S^perp exactly (2^(2n-s) vectors,
vectorized numpy) — for the n <= 13 target list this stays <= 2^20.
"""

import json
from pathlib import Path

import numpy as np

def _load_targets() -> list:
    """Open targets: targets.json minus entries already closed (a
    SOLUTION_n{n}_k{k}_c{c}_d{d}.json exists in the harvest dir)."""
    import os
    targets = json.loads((Path(__file__).parent / "targets.json").read_text())
    harvest = Path(os.getenv(
        "HARVEST_DIR",
        Path(__file__).resolve().parents[2] / "artifacts" /
        "witnesses" / "q2"))
    return [t for t in targets
            if not (harvest /
                    f"SOLUTION_n{t['n']}_k{t['k']}_c{t['c']}_d{t['d']}.json"
                    ).exists()]


TARGETS = _load_targets()


def _xmask(n: int) -> int:
    return int(sum(1 << (2 * i) for i in range(n)))


def _J(v: int, n: int) -> int:
    """Swap X/Z parts: symplectic product <u,v> = popcount(u & J(v)) mod 2."""
    xm = _xmask(n)
    return ((v & xm) << 1) | ((v >> 1) & xm)


def sform(u: int, v: int, n: int) -> int:
    return bin(u & _J(v, n)).count("1") & 1


def symplectic_weights(vs: np.ndarray, n: int) -> np.ndarray:
    m = np.uint64(_xmask(n))
    v = vs.astype(np.uint64)
    acted = (v | (v >> np.uint64(1))) & m
    return np.bitwise_count(acted).astype(np.int64)


def gf2_basis(vecs) -> list:
    """Reduced GF(2) basis of the span of the given integers."""
    basis = []
    for x in vecs:
        x = int(x)
        for b in basis:
            x = min(x, x ^ b)
        if x:
            basis.append(x)
            basis.sort(reverse=True)
    return basis


def span_array(basis: list) -> np.ndarray:
    """All 2^len(basis) elements of the span (int64 array)."""
    out = np.zeros(1 << len(basis), dtype=np.int64)
    for i, b in enumerate(basis):
        step = 1 << i
        out[step:2 * step] = out[:step] ^ np.int64(b)
    return out


def nullspace(rows: list, nbits: int) -> list:
    """Basis of {v : popcount(v & r) even for all r} in F_2^nbits."""
    # full Gauss-Jordan so each pivot column appears in exactly one row
    red = []  # list of (pivot_col, row)
    for r in rows:
        x = int(r)
        for col, rr in red:
            if (x >> col) & 1:
                x ^= rr
        if x:
            piv = x.bit_length() - 1
            red = [(c, rr ^ x if (rr >> piv) & 1 else rr) for c, rr in red]
            red.append((piv, x))
    pivot_cols = {col for col, _ in red}
    basis = []
    for j in range(nbits):
        if j in pivot_cols:
            continue
        v = 1 << j
        for col, rr in red:
            # rr contains pivot col and free columns only; parity over free
            # part of v decides the pivot bit
            if bin(v & rr & ~(1 << col)).count("1") & 1:
                v |= 1 << col
        basis.append(v)
    return basis


def evaluate(n: int, gens, d_target: int) -> dict:
    """Exact EAQECC parameters of span(gens), plus the exact number of
    logical operators (S^perp \\ S_iso) of weight < d_target."""
    mask = (1 << (2 * n)) - 1
    basis = gf2_basis(int(g) & mask for g in gens)
    s = len(basis)
    if s == 0 or s > 2 * n:
        return {"error": "degenerate stabilizer set"}
    if 2 * n - s > 22:
        return {"error": "S^perp too large to enumerate"}
    # S^perp
    perp_basis = nullspace([_J(b, n) for b in basis], 2 * n)
    perp = span_array(perp_basis)
    # S_iso = S ∩ S^perp (S is small: enumerate and test orthogonality)
    S = span_array(basis)
    iso_mask = np.ones(len(S), dtype=bool)
    for b in basis:
        jb = np.int64(_J(b, n))
        iso_mask &= (np.bitwise_count((S & jb).astype(np.uint64)) & 1) == 0
    iso_vecs = np.sort(S[iso_mask])
    iso = int(np.log2(len(iso_vecs)))
    c2 = s - iso
    if c2 % 2:
        return {"error": "odd symplectic rank (bug)"}
    c = c2 // 2
    k = n - s + c
    w = symplectic_weights(perp, n)
    logical = ~np.isin(perp, iso_vecs)
    if not logical.any():
        return {"n": n, "s": s, "c": c, "iso": iso, "k": k, "d": None,
                "offending": 0}
    d = int(w[logical].min())
    offending = int((w[logical] < d_target).sum())
    return {"n": n, "s": s, "c": c, "iso": iso, "k": k, "d": d,
            "offending": offending}


def random_stabilizer(n: int, s: int, rng) -> list:
    """Random s independent generators on n qubits (no rank shaping)."""
    gens = []
    while len(gf2_basis(gens)) < s:
        gens.append(int(rng.integers(1, 1 << (2 * n))))
        gens = gf2_basis(gens)
    return gens
