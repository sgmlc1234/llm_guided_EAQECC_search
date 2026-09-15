#!/usr/bin/env python3
"""Pure-Python verification of the closed-form families at every q.
Runs from any directory; witnesses are read from artifacts/witnesses/.

  (1) Unified family (Theorem: [[n,1,n-1;n-q-1]]_q) for q=2,3,4,5,
      n = 2q+1 .. 2q+8 (q=2: odd n only);
  (2) Qutrit table family [[n,1,n-1;n-3]]_3 for n=5..30;
  (3) every bundled witness (q=3 layers, q=4, q=5) re-verified exactly;
  (4) qutrit-table comparison from the bundled snapshot.
"""
import glob
import json
import os
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("EAQECC_ROOT") or HERE.parents[1])
sys.path.insert(0, str(HERE.parent))
from helpers_eaqecc_fq import Fq, evaluate_L, vecq  # noqa: E402
W = ROOT / "artifacts" / "witnesses"

def unified(Fld, n):
    q = Fld.q
    char2 = (q in (2, 4))
    neg1 = Fld.NEG[1]
    rhos = []
    for i in range(q):
        p = [(0,0)]*n; p[2*i], p[2*i+1] = (0,1), (0,neg1)
        rhos.append(vecq(p, n))
    a = vecq([(1,0)]*n, n)
    z2 = 0 if char2 else 1
    bp = []
    for i in range(q):
        bp += [(i,1),(i,z2)]
    bp += [(0,1)]*(n-2*q)
    b = vecq(bp, n)
    if Fld.sform(a, b, n) == 0:
        for val in range(2, q):
            bp2 = list(bp); bp2[-1] = (0, val)
            b2 = vecq(bp2, n)
            if Fld.sform(a, b2, n) != 0:
                b = b2; break
        else:
            return None
    return rhos + [a, b]

for q in (2, 3, 4, 5):
    Fld = Fq(q)
    for n in range(2*q+1, 2*q+9):
        L = unified(Fld, n)
        if L is None:
            assert q == 2 and n % 2 == 0, (q, n)
            continue
        r = evaluate_L(Fld, n, L, n-1)
        assert (r['k'] == 1 and r['c'] == n-q-1 and r['d'] == n-1
                and r['offending'] == 0), (q, n, r)
    print(f"Unified family verified for q={q}")

F3 = Fq(3)
for n in range(5, 31):
    rhos = [vecq([(0,1),(0,2)] + [(0,0)]*(n-2), n),
            vecq([(0,0)]*2 + [(0,1),(0,2)] + [(0,0)]*(n-4), n)]
    a = vecq([(1,0)]*n, n)
    tail = [(0,1)]*(n-4)
    if n % 3 == 0:
        tail[-1] = (0,2)
    b = vecq([(1,1),(1,1),(2,1),(2,1)] + tail, n)
    r = evaluate_L(F3, n, rhos + [a, b], n-1)
    assert (r['k'] == 1 and r['c'] == n-3 and r['d'] == n-1
            and r['offending'] == 0), (n, r)
print("Qutrit table family verified for n=5..30")

tot = 0
for pat, q in ((W / "q3" / "SOLUTION3_*.json", 3),
               (W / "q4" / "SOLUTION4_*.json", 4),
               (W / "q5" / "SOLUTION5_*.json", 5)):
    Fld = Fq(q)
    for pth in sorted(glob.glob(str(pat))):
        s = json.load(open(pth)); t = s['target']
        L = [np.array(row) for row in s['L_basis']]
        r = evaluate_L(Fld, t['n'], L, t['d'])
        assert (r['k'] == 1 and r['c'] == t['c'] and r['d'] >= t['d']
                and r['offending'] == 0), (pth, r)
        tot += 1
print(f"{tot} bundled witnesses re-verified (q=3,4,5)")

_snaps = sorted(d for d in (ROOT / "artifacts" / "codetables_snapshots").iterdir()
                if d.is_dir() and (d / "qutrit.json").exists())
selected = os.environ.get("EAQECC_SNAPSHOT")
snapshot = (ROOT / "artifacts" / "codetables_snapshots" / selected) if selected else _snaps[-1]
qt = json.load(open(snapshot / "qutrit.json"))
closed = sorted({e['n'] for e in qt if e['k'] == 1 and e['c'] == e['n']-3
                 and e['dl'] < e['n']-1 <= e['du']})
print(f"Qutrit table: family closes {len(closed)} listed gap entries "
      f"(n={closed[0]}..{closed[-1]})")
print("All checks passed.")
