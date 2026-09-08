# Exhaustive check: does an EAQECC [[6,2,5;4]] exist?
# iso = n-k-c = 0, L = S_perp is 4-dim non-degenerate in F_2^12,
# all 15 nonzero vectors must have symplectic weight >= 5.
import time
import numpy as np

n = 6
t0 = time.time()

def sweight(v):
    return sum(1 for i in range(n) if (v >> (2*i)) & 3)

W = np.array([v for v in range(1, 1 << (2*n)) if sweight(v) >= 5], dtype=np.int64)
Wset = np.zeros(1 << (2*n), dtype=bool)
Wset[W] = True
print('|W| =', len(W), flush=True)

def sform(u, v):
    s = 0
    for i in range(n):
        a1, b1 = (u >> (2*i)) & 1, (u >> (2*i+1)) & 1
        a2, b2 = (v >> (2*i)) & 1, (v >> (2*i+1)) & 1
        s ^= (a1 & b2) ^ (b1 & a2)
    return s

count = 0
found = None
nW = len(W)
for i1 in range(nW):
    v1 = int(W[i1])
    if i1 % 100 == 0:
        print('progress i1=%d/%d count=%d %.0fs' % (i1, nW, count, time.time()-t0), flush=True)
    # candidates beyond v1 whose xor with v1 stays in W
    tail = W[i1+1:]
    ok2 = tail[Wset[np.bitwise_xor(tail, v1)]]
    for i2 in range(len(ok2)):
        v2 = int(ok2[i2])
        s2 = (v1, v2, v1 ^ v2)
        t2 = ok2[i2+1:]
        m = Wset[np.bitwise_xor(t2, v1)] & Wset[np.bitwise_xor(t2, v2)] & Wset[np.bitwise_xor(t2, v1 ^ v2)]
        ok3 = t2[m]
        for i3 in range(len(ok3)):
            v3 = int(ok3[i3])
            s3 = s2 + (v3, v3 ^ v1, v3 ^ v2, v3 ^ v1 ^ v2)
            t3 = ok3[i3+1:]
            m3 = np.ones(len(t3), dtype=bool)
            for s in s3:
                m3 &= Wset[np.bitwise_xor(t3, s)]
            ok4 = t3[m3]
            for v4 in ok4:
                count += 1
                basis = [v1, v2, v3, int(v4)]
                G = [[sform(a, b) for b in basis] for a in basis]
                M = [int("".join(map(str, r)), 2) for r in G]
                r = 0
                for bit in range(3, -1, -1):
                    piv = next((k for k in range(r, 4) if (M[k] >> bit) & 1), None)
                    if piv is None:
                        continue
                    M[r], M[piv] = M[piv], M[r]
                    for k in range(4):
                        if k != r and (M[k] >> bit) & 1:
                            M[k] ^= M[r]
                    r += 1
                if r == 4:
                    found = basis
                    print('FOUND NON-DEGENERATE:', basis, flush=True)
if found:
    print('RESULT: [[6,2,5;4]] EXISTS, basis', found)
else:
    print('RESULT: no non-degenerate weight-clean subspace — [[6,2,5;4]] DOES NOT EXIST')
print('weight-clean subspaces (bases counted):', count, 'time %.0fs' % (time.time() - t0))
