#!/usr/bin/env python3
r"""Exhaustive nonexistence proof for the [[5,2,4;3]] EAQECC.

Since n-k-c = 0, the code exists iff a 4-dim subspace L of F_2^10 exists
with (i) all 15 nonzero vectors of symplectic weight >= 4 and (ii) the
symplectic form nondegenerate on L. This script enumerates ALL increasing
bases from the 648 weight->=4 vectors with closure checks (every subspace
appears via each of its increasing bases) and tests the Gram rank.
Result: 2,177,280 bases found, Gram matrix singular for every one.
Runtime: ~3 minutes in pure Python.
"""
import time
n = 5
t0 = time.time()

def sweight(v):
    return sum(1 for i in range(n) if (v >> (2*i)) & 3)

def sform(u, v):
    s = 0
    for i in range(n):
        a1, b1 = (u >> (2*i)) & 1, (u >> (2*i+1)) & 1
        a2, b2 = (v >> (2*i)) & 1, (v >> (2*i+1)) & 1
        s ^= a1 & b2 ^ b1 & a2
    return s

W = [v for v in range(1, 1 << (2*n)) if sweight(v) >= 4]
Wset = set(W)
count, found = 0, None
for i1, v1 in enumerate(W):
    for i2 in range(i1+1, len(W)):
        v2 = W[i2]
        if v1 ^ v2 not in Wset: continue
        span2 = [v1, v2, v1 ^ v2]
        for i3 in range(i2+1, len(W)):
            v3 = W[i3]
            if any((v3 ^ s) not in Wset for s in span2): continue
            span3 = span2 + [v3] + [v3 ^ s for s in span2]
            for i4 in range(i3+1, len(W)):
                v4 = W[i4]
                if any((v4 ^ s) not in Wset for s in span3): continue
                count += 1
                basis = [v1, v2, v3, v4]
                M = [int("".join(str(sform(a, b)) for b in basis), 2) for a in basis]
                r = 0
                for bit in range(3, -1, -1):
                    piv = next((i for i in range(r, 4) if (M[i] >> bit) & 1), None)
                    if piv is None: continue
                    M[r], M[piv] = M[piv], M[r]
                    for i in range(4):
                        if i != r and (M[i] >> bit) & 1: M[i] ^= M[r]
                    r += 1
                if r == 4:
                    found = basis
print('weight-clean bases:', count, 'nondegenerate found:', found,
      'time %.0fs' % (time.time() - t0))
assert found is None and count == 2177280
print('CONFIRMED: no [[5,2,4;3]] EAQECC exists.')
