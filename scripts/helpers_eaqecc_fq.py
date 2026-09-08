"""General F_q symplectic machinery for EAQECC L-side evaluation.

Supports prime q (mod-p arithmetic) and q = 4 (F_4 = F_2[w]/(w^2+w+1),
elements encoded 0,1,2,3 = 0,1,w,w+1; addition = XOR, char 2).

Conventions as in helpers_eaqecc_f3: vectors in F_q^{2n}, per qudit i the
pair (x_i, z_i); alternating form <u,v> = sum(x_i z'_i - z_i x'_i);
weight = #{i : (x_i,z_i) != (0,0)}. L-side evaluation for F_q-LINEAR L.
NOTE (scope): for prime-power q this covers F_q-linear codes only; general
additive codes need the trace form and are out of scope here.
"""

import itertools

import numpy as np


class Fq:
    def __init__(self, q):
        self.q = q
        if q == 4:
            add = [[a ^ b for b in range(4)] for a in range(4)]
            mul = [[0] * 4 for _ in range(4)]
            # 1=1, 2=w, 3=w+1; w^2=w+1, w(w+1)=1, (w+1)^2=w
            tbl = {(1, 1): 1, (1, 2): 2, (1, 3): 3,
                   (2, 2): 3, (2, 3): 1, (3, 3): 2}
            for (a, b), v in tbl.items():
                mul[a][b] = mul[b][a] = v
            self.ADD = np.array(add, dtype=np.int64)
            self.MUL = np.array(mul, dtype=np.int64)
            self.NEG = np.arange(4, dtype=np.int64)  # char 2
        else:
            # prime field
            self.ADD = np.array([[(a + b) % q for b in range(q)]
                                 for a in range(q)], dtype=np.int64)
            self.MUL = np.array([[(a * b) % q for b in range(q)]
                                 for a in range(q)], dtype=np.int64)
            self.NEG = np.array([(-a) % q for a in range(q)], dtype=np.int64)

    def add_vec(self, u, v):
        return self.ADD[u, v]

    def smul_vec(self, s, v):
        return self.MUL[s, v]

    def sform(self, u, v, n):
        acc = 0
        for i in range(n):
            t1 = self.MUL[u[2 * i], v[2 * i + 1]]
            t2 = self.MUL[u[2 * i + 1], v[2 * i]]
            acc = self.ADD[acc, self.ADD[t1, self.NEG[t2]]]
        return int(acc)


def swt(v, n):
    v = np.asarray(v)
    return int(np.count_nonzero((v[0::2] != 0) | (v[1::2] != 0)))


def fq_rank(F, rows):
    q = F.q
    m = [np.array(r, dtype=np.int64).copy() for r in rows]
    if not m:
        return 0
    nc = len(m[0])
    inv = {a: next(b for b in range(q) if F.MUL[a][b] == 1)
           for a in range(1, q)}
    r = 0
    for col in range(nc):
        piv = next((i for i in range(r, len(m)) if m[i][col]), None)
        if piv is None:
            continue
        m[r], m[piv] = m[piv], m[r]
        s = inv[int(m[r][col])]
        m[r] = F.MUL[s, m[r]]
        for i in range(len(m)):
            if i != r and m[i][col]:
                coef = int(m[i][col])
                m[i] = F.ADD[m[i], F.NEG[F.MUL[coef, m[r]]]]
        r += 1
    return r


def evaluate_L(F, n, L_basis, d_target):
    """Exact parameters from an F_q-linear basis of L = S^perp."""
    q = F.q
    m = fq_rank(F, L_basis)
    if m != len(L_basis):
        return {"error": f"basis dependent (rank {m})"}
    gram = np.array([[F.sform(u, v, n) for v in L_basis] for u in L_basis],
                    dtype=np.int64)
    rank = fq_rank(F, list(gram))
    iso = m - rank
    s = 2 * n - m
    c = (s - iso) // 2
    k = n - s + c
    B = np.array(L_basis, dtype=np.int64)
    d = None
    offending = 0
    for coeffs in itertools.product(range(q), repeat=m):
        cv = np.array(coeffs, dtype=np.int64)
        if not cv.any():
            continue
        # gram pairing of the combination with each basis vector
        gp = 0
        pair = np.zeros(m, dtype=np.int64)
        for idx in range(m):
            acc = 0
            for jdx in range(m):
                acc = F.ADD[acc, F.MUL[cv[jdx], gram[jdx][idx]]]
            pair[idx] = acc
        if not pair.any():
            continue  # radical element
        v = np.zeros(2 * n, dtype=np.int64)
        for idx in range(m):
            if cv[idx]:
                v = F.ADD[v, F.MUL[cv[idx], B[idx]]]
        w = swt(v, n)
        d = w if d is None else min(d, w)
        if w < d_target:
            offending += 1
    return {"n": n, "s": s, "m": m, "iso": iso, "c": c, "k": k,
            "d": d, "offending": offending, "q": q}


def vecq(pairs, n):
    v = np.zeros(2 * n, dtype=np.int64)
    for i, (x, z) in enumerate(pairs):
        v[2 * i], v[2 * i + 1] = x, z
    return v
