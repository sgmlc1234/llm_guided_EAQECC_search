r"""F_3 (qutrit) symplectic machinery for EAQECC parameter evaluation.

Vectors in F_3^{2n} as tuples/np arrays; per qudit i, component 2i = X part,
2i+1 = Z part. Symplectic form <u,v> = sum(x_i z'_i - z_i x'_i) mod 3.
Weight = number of qudits with (x,z) != (0,0).

L-side evaluation: given a basis of L = S^perp (dim m small), compute
  rank of the symplectic Gram form on L (= 2c'), radical, and
  min weight over L \ rad(L)  (= d when L is the normalizer side).
Parameters: s = 2n - m (dim S), iso = m - rank, c = (s - iso)/2 wait --
for the L-side view: S = L^perp, dim S = 2n - m, S_iso = rad(L),
iso = dim rad(L) = m - rank, c = ((2n - m) - iso)/2 is WRONG unless
rad(S) = rad(L); correct: rad(S) = S cap S^perp = S cap L ... for
S = L^perp we have S cap S^perp = L^perp cap L = rad(L). So
c = (dim S - dim rad)/2 = (2n - m - (m - rank))/2, k = n - dim S + c.
"""

import itertools
import numpy as np


def sform(u, v, n):
    u = np.asarray(u, dtype=np.int64)
    v = np.asarray(v, dtype=np.int64)
    x1, z1 = u[0::2], u[1::2]
    x2, z2 = v[0::2], v[1::2]
    return int((x1 @ z2 - z1 @ x2) % 3)


def swt(v, n):
    v = np.asarray(v)
    return int(np.count_nonzero((v[0::2] != 0) | (v[1::2] != 0)))


def f3_rank(rows):
    """Rank over F_3 of a list of int vectors (np arrays)."""
    m = [np.array(r, dtype=np.int64) % 3 for r in rows]
    rank, col, nc = 0, 0, len(m[0]) if m else 0
    m = [r.copy() for r in m]
    r = 0
    for col in range(nc):
        piv = next((i for i in range(r, len(m)) if m[i][col] % 3), None)
        if piv is None:
            continue
        m[r], m[piv] = m[piv], m[r]
        inv = 1 if m[r][col] % 3 == 1 else 2  # inverse in F_3
        m[r] = (m[r] * inv) % 3
        for i in range(len(m)):
            if i != r and m[i][col] % 3:
                m[i] = (m[i] - m[i][col] * m[r]) % 3
        r += 1
    return r


def span_iter(basis):
    """Iterate all 3^m combinations of the basis (np arrays mod 3)."""
    m = len(basis)
    B = np.array(basis, dtype=np.int64) % 3
    for coeffs in itertools.product(range(3), repeat=m):
        yield (np.array(coeffs) @ B) % 3


def evaluate_L(n, L_basis, d_target):
    """Exact parameters from a basis of L = S^perp (list of len-2n arrays)."""
    m = f3_rank(L_basis)
    if m != len(L_basis):
        return {"error": f"basis dependent (rank {m} != {len(L_basis)})"}
    gram = np.array([[sform(u, v, n) for v in L_basis] for u in L_basis],
                    dtype=np.int64)
    rank = f3_rank(list(gram))
    iso = m - rank
    s = 2 * n - m
    c = (s - iso) // 2
    k = n - s + c
    # rad(L) membership test per element: v in rad iff gram-pairing with all
    # basis elements is 0 <=> coeff vector in kernel of gram. Enumerate span:
    d = None
    offending = 0
    B = np.array(L_basis, dtype=np.int64) % 3
    for coeffs in itertools.product(range(3), repeat=m):
        cv = np.array(coeffs, dtype=np.int64)
        if not cv.any():
            continue
        if not ((cv @ gram) % 3).any():
            continue  # radical element -> not a logical
        v = (cv @ B) % 3
        w = swt(v, n)
        d = w if d is None else min(d, w)
        if w < d_target:
            offending += 1
    return {"n": n, "s": s, "m": m, "iso": iso, "c": c, "k": k,
            "d": d, "offending": offending}


def vec3(pairs, n):
    """Build vector from list of (x,z) per qudit."""
    v = np.zeros(2 * n, dtype=np.int64)
    for i, (x, z) in enumerate(pairs):
        v[2 * i] = x % 3
        v[2 * i + 1] = z % 3
    return v
