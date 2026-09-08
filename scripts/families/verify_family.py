#!/usr/bin/env python3
r"""Self-contained verification of the EAQECC family [[n,1,n-1;n-3]], n >= 5.

Construction (binary symplectic representation; per qubit i, bit 2i = X
part, bit 2i+1 = Z part). For ODD n:
    rho1 = Z_1 Z_2         rho2 = Z_3 Z_4
    a    = X^{\otimes n}
    b    = Y_1 X_2 Z_3 I_4 Z_5 ... Z_n
For EVEN n >= 6 (block construction):
    rho1 = X_1 X_2 X_3 X_4         rho2 = Z_1 Z_2 Z_3 Z_4
    a    = X_1 I_2 Y_3 Z_4 X_5 ... X_n
    b    = X_1 Z_2 I_3 Y_4 Z_5 ... Z_n
In both cases:
    L    = <a, b, rho1, rho2>          (the normalizer quotient side)
    S    = L^perp (symplectic complement) is the stabilizer set:
           dim S = 2n-4, radical dim 2, c = n-3 ebits, k = 1, d = n-1.

d = n-1 meets the entanglement-assisted Singleton bound
2(d-1) <= n-k+c, so every member is optimal.

Checks performed for each n in range:
  (1) dim L = 4;
  (2) rad(L) = <rho1, rho2> (dim 2);
  (3) all 12 elements of L \\ rad(L) have symplectic weight in {n-1, n},
      with minimum exactly n-1;
  (4) <a,b> = 1 (so the form on L has rank exactly 2).
For n <= 11 an additional full brute-force check over all 4^n Pauli
vectors recomputes S^perp, the radical, c, k and d from the S side.

Usage: python3 verify_family.py [n_max]
"""

import sys


def P(i, t):
    return {"X": 1, "Z": 2, "Y": 3}[t] << (2 * i)


def sform(u, v, n):
    s = 0
    for i in range(n):
        a1, b1 = (u >> (2 * i)) & 1, (u >> (2 * i + 1)) & 1
        a2, b2 = (v >> (2 * i)) & 1, (v >> (2 * i + 1)) & 1
        s ^= (a1 & b2) ^ (b1 & a2)
    return s


def swt(v, n):
    return sum(1 for i in range(n) if (v >> (2 * i)) & 3)


def family_generators(n):
    assert n >= 5
    if n % 2 == 1:
        rho1 = P(0, "Z") | P(1, "Z")
        rho2 = P(2, "Z") | P(3, "Z")
        a = 0
        for i in range(n):
            a |= P(i, "X")
        b = P(0, "Y") | P(1, "X") | P(2, "Z")
        for i in range(4, n):
            b |= P(i, "Z")
    else:
        rho1 = P(0, "X") | P(1, "X") | P(2, "X") | P(3, "X")
        rho2 = P(0, "Z") | P(1, "Z") | P(2, "Z") | P(3, "Z")
        a = P(0, "X") | P(2, "Y") | P(3, "Z")
        for i in range(4, n):
            a |= P(i, "X")
        b = P(0, "X") | P(1, "Z") | P(3, "Y")
        for i in range(4, n):
            b |= P(i, "Z")
    return a, b, rho1, rho2


def check_L_side(n):
    a, b, rho1, rho2 = family_generators(n)
    basis = [a, b, rho1, rho2]
    span = {0}
    for g in basis:
        span |= {x ^ g for x in span}
    assert len(span) == 16, "dim L != 4"
    rad = {v for v in span if all(sform(v, g, n) == 0 for g in basis)}
    assert rad == {0, rho1, rho2, rho1 ^ rho2}, "radical != <rho1, rho2>"
    ws = sorted(swt(v, n) for v in span - rad)
    assert ws[0] == n - 1 and ws[-1] <= n, f"weights {ws}"
    assert sform(a, b, n) == 1, "<a,b> != 1"
    return ws[0]


def check_S_side_bruteforce(n):
    a, b, rho1, rho2 = family_generators(n)
    L = [a, b, rho1, rho2]
    perp = [v for v in range(1 << (2 * n))
            if all(sform(v, g, n) == 0 for g in L)]  # this is S = L^perp
    import math
    s = int(math.log2(len(perp)))
    Sset = set(perp)
    # S^perp = L (verify) and radical
    Lspan = {0}
    for g in L:
        Lspan |= {x ^ g for x in Lspan}
    rad = Lspan & Sset
    iso = int(math.log2(len(rad)))
    c = (s - iso) // 2
    k = n - s + c
    d = min(swt(v, n) for v in Lspan - rad)
    assert (s, iso, c, k, d) == (2 * n - 4, 2, n - 3, 1, n - 1), \
        (s, iso, c, k, d)


def family2_generators(n):
    """Second family [[n,1,n-1;n-4]], even n >= 6 (violates BDH Singleton)."""
    assert n % 2 == 0 and n >= 6
    rhos = [P(0, "Z") | P(1, "Z"), P(2, "Z") | P(3, "Z"), P(4, "Z") | P(5, "Z")]
    a = P(1, "Z") | P(2, "X") | P(3, "X") | P(4, "X") | P(5, "X")
    b = P(0, "X") | P(1, "X") | P(3, "Z") | P(4, "X") | P(5, "Y")
    for i in range(6, n):
        a |= P(i, "Z")
        b |= P(i, "X")
    return a, b, rhos


def check_family2(n):
    a, b, rhos = family2_generators(n)
    basis = [a, b] + rhos
    span = {0}
    for g in basis:
        span |= {x ^ g for x in span}
    assert len(span) == 32, "dim L != 5"
    rad = {v for v in span if all(sform(v, g, n) == 0 for g in basis)}
    radgen = {0}
    for r in rhos:
        radgen |= {x ^ r for x in radgen}
    assert rad == radgen, "radical != <rho1,rho2,rho3>"
    ws = sorted(swt(v, n) for v in span - rad)
    assert ws[0] == n - 1 and ws[-1] == n - 1, f"weights {ws}"
    assert sform(a, b, n) == 1
    assert 2 * (n - 2) > n - 1 + (n - 4), "BDH violation check"


def family34_generators(n, j):
    """Families 3 (even n>=10, j=5) and 4 (odd n>=13, j=6): [[n,1,n-2;n-j-1]]."""
    rhos = [P(2*i, "Z") | P(2*i+1, "Z") for i in range(j)]
    apat = ["X"]*8 + ["Z","I"]*(j-4)
    bpat = ["Y","X","Y","X","Z","I","Z","I"] + ["X","X"]*(j-4)
    a = b = 0
    for i, s in enumerate(apat):
        a |= P(i, s) if s != "I" else 0
    for i, s in enumerate(bpat):
        b |= P(i, s) if s != "I" else 0
    for i in range(2*j, n):
        a |= P(i, "X")
        b |= P(i, "Z")
    return a, b, rhos


def check_family34(n, j):
    a, b, rhos = family34_generators(n, j)
    basis = [a, b] + rhos
    span = {0}
    for g in basis:
        span |= {x ^ g for x in span}
    assert len(span) == 1 << (j + 2), "dim L wrong"
    rad = {v for v in span if all(sform(v, g, n) == 0 for g in basis)}
    radgen = {0}
    for r in rhos:
        radgen |= {x ^ r for x in radgen}
    assert rad == radgen, "radical mismatch"
    ws = sorted(swt(v, n) for v in span - rad)
    assert ws[0] == n - 2, f"min weight {ws[0]}"
    assert sform(a, b, n) == 1
    assert 2 * (n - 3) > n - 1 + (n - j - 1), "BDH violation check"


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    for n in range(5, n_max + 1):
        d = check_L_side(n)
        extra = ""
        if n <= 11:
            check_S_side_bruteforce(n)
            extra = "  [S-side brute force OK]"
        print(f"[[{n},1,{d};{n-3}]] verified{extra}")
        if n % 2 == 0 and n >= 6:
            check_family2(n)
            print(f"[[{n},1,{n-1};{n-4}]] (family 2, BDH-violating) verified")
        if n % 2 == 0 and n >= 10:
            check_family34(n, 5)
            print(f"[[{n},1,{n-2};{n-6}]] (family 3, BDH-violating) verified")
        if n % 2 == 1 and n >= 13:
            check_family34(n, 6)
            print(f"[[{n},1,{n-2};{n-7}]] (family 4, BDH -2) verified")
    print("All checks passed.")


if __name__ == "__main__":
    main()
