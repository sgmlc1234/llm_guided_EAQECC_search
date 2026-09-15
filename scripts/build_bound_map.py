#!/usr/bin/env python3
"""Build the (n,k,c) bound-provenance map for the two EAQECC papers.

Cross-references our results against a dated codetables.de snapshot
(the manuscript's frozen comparison unless explicitly overridden) and emits JSON that
scripts/make_bound_map_figure.py turns into the provenance figure.

Cell classes (per (q,n,k,c)):
  lower   -- we constructed a code of distance d there (lower bound proved)
  upper   -- we proved no code of distance d exists (upper bound proved)
  both    -- both of the above at the same cell (distance pinned exactly)
  plotkin -- upper bound lowered by the (known) EA-Plotkin bound we applied
"""

import argparse
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SNAP_ROOT = ROOT / "artifacts" / "codetables_snapshots"
# Match the auditor: a newer snapshot must not silently change the paper figure.
parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument('snapshot', nargs='?', default='paper',
                    help='paper (default), latest, or an archived date')
parser.add_argument('--out', type=Path, default=ROOT / 'artifacts/tables/bound_map.json')
args = parser.parse_args()
_snaps = sorted(d for d in SNAP_ROOT.iterdir()
                if d.is_dir() and (d / "qubit.json").exists())
if args.snapshot == 'paper':
    SNAP = SNAP_ROOT / json.loads((ROOT / 'artifacts/paper_reference.json').read_text())['snapshot']
elif args.snapshot == 'latest':
    SNAP = _snaps[-1]
else:
    SNAP = SNAP_ROOT / args.snapshot
if not SNAP.exists():
    sys.exit(f"snapshot not found: {SNAP}")

NMAX = {2: 64, 3: 36}

# ---------------------------------------------------------------- our results
# (n, k, c, d, source, paper)
LOWER = []
UPPER = []

# ---- paper 1: qubit families ------------------------------------------------
for n in range(5, 65):
    LOWER.append((2, n, 1, n - 3, n - 1, "Thm 1 — family [[n,1,n-1;n-3]]", 1))
for n in range(6, 65, 2):
    LOWER.append((2, n, 1, n - 4, n - 1, "Thm 2 — family [[n,1,n-1;n-4]] (BDH-violating)", 1))
for n in range(10, 65, 2):
    LOWER.append((2, n, 1, n - 6, n - 2, "Thm 3 — family [[n,1,n-2;n-6]] (BDH-violating)", 1))
for n in range(13, 64, 2):
    LOWER.append((2, n, 1, n - 7, n - 2, "Thm 4 — family [[n,1,n-2;n-7]] (BDH -2)", 1))

# ---- paper 1: sporadic essential codes --------------------------------------
SPORADIC = [(5,2,2,3),(6,2,1,3),(6,2,3,4),(7,2,2,4),(7,2,4,5),(7,3,3,4),
            (7,4,2,3),(8,1,2,6),(8,4,1,3),(8,5,2,3),(9,1,2,7),(9,2,3,5),
            (9,3,2,4),(9,3,4,5),(9,5,1,3),(10,2,2,5),(10,2,7,7),(11,1,4,9),
            (12,2,9,8),(12,3,8,7),(12,5,4,5),(13,2,10,9),(13,6,6,6)]
for (n, k, c, d) in SPORADIC:
    LOWER.append((2, n, k, c, d, "sporadic code (evolutionary + SAT sweep)", 1))

# ---- paper 1: nonexistence ---------------------------------------------------
for (n, k, c, d, how) in [(5,2,3,4,"exhaustive enumeration + DRAT"),
                          (6,2,4,5,"exhaustive enumeration + DRAT"),
                          (6,2,2,4,"SAT refutation"), (7,2,3,5,"SAT refutation"),
                          (7,3,4,5,"SAT refutation"), (8,2,4,6,"SAT refutation"),
                          (8,3,5,6,"SAT refutation"), (9,2,5,7,"SAT refutation")]:
    UPPER.append((2, n, k, c, d, f"nonexistence — {how}", 1))

# ---- paper 1: the qubit first-level floor (Prop. "minimum entanglement") -----
# CaDiCaL normal-form refutations of [[7,1,6;3]], [[9,1,8;5]], [[11,1,10;7]]
# (odd n, c=n-4) and [[6,1,5;1]], [[8,1,7;3]], [[10,1,9;5]] (even n, c=n-5).
for n in (7, 9, 11):
    UPPER.append((2, n, 1, n - 4, n - 1,
                  "qubit floor — normal-form SAT refutation", 1))
for n in (6, 8, 10):
    UPPER.append((2, n, 1, n - 5, n - 1,
                  "qubit floor — normal-form SAT refutation", 1))

# ---- paper 2: qutrit families ------------------------------------------------
for n in range(5, 37):
    LOWER.append((3, n, 1, n - 3, n - 1, "Thm — qutrit family [[n,1,n-1;n-3]]", 2))
for n in range(6, 37):
    LOWER.append((3, n, 1, n - 4, n - 1, "Thm (unified, q=3) [[n,1,n-1;n-4]] (BDH-violating)", 2))
for n in range(8, 16):
    LOWER.append((3, n, 1, n - 5, n - 1, "third layer, verified witness (BDH -2)", 2))

# ---- paper 2: qutrit floor (nonexistence) ------------------------------------
for n in (10, 11, 12):
    UPPER.append((3, n, 1, n - 6, n - 1,
                  "floor theorem — complete SAT refutation (free radical)", 2))

# ---- paper 2: qubit corridor endpoint + second level -------------------------
UPPER.append((2, 9, 1, 1, 7, "GHW bound not tight — complete SAT refutation", 2))
LOWER.append((2, 9, 1, 2, 7, "c_min(9,1,7)=2 — SAT witness", 2))
for (n, c) in [(7, 1), (8, 1), (10, 3), (11, 3), (12, 5), (13, 5)]:
    UPPER.append((2, n, 1, c, n - 2,
                  "second-level floor — complete SAT refutation", 2))

# Released witness and refutation records take precedence over older summaries.
for path in sorted((ROOT / "artifacts/witnesses/q2").glob("SOLUTION*.json")):
    record = json.loads(path.read_text())
    t = record["target"]
    LOWER.append((2, t["n"], t["k"], t["c"], t["d"],
                  f"archived witness: {path.name}", 1))
for e in json.loads((ROOT / "artifacts/refutations/registry.json").read_text()):
    UPPER.append((e["q"], e["n"], e["k"], e["c"], e["d"],
                  f"registry: {e['tag']} ({e['status']})", 1))

# ---------------------------------------------------------------- table data
def load(q):
    name = "qubit" if q == 2 else "qutrit"
    return json.load(open(SNAP / f"{name}.json"))

cells = {}          # (q,n,k,c) -> dict
for q in (2, 3):
    for e in load(q):
        cells[(q, e["n"], e["k"], e["c"])] = {
            "q": q, "n": e["n"], "k": e["k"], "c": e["c"],
            "dl": e["dl"], "du": e["du"], "listed": True,
            "title": e.get("title", ""), "lower": None, "upper": None,
        }

def touch(q, n, k, c):
    key = (q, n, k, c)
    if key not in cells:
        cells[key] = {"q": q, "n": n, "k": k, "c": c, "dl": None, "du": None,
                      "listed": False, "title": "", "lower": None, "upper": None}
    return cells[key]

for (q, n, k, c, d, src, paper) in LOWER:
    if n > NMAX[q]:
        continue
    cell = touch(q, n, k, c)
    if cell["lower"] is None or d > cell["lower"]["d"]:
        cell["lower"] = {"d": d, "src": src, "paper": paper}

for (q, n, k, c, d, src, paper) in UPPER:
    cell = touch(q, n, k, c)
    if cell["upper"] is None or d < cell["upper"]["d"]:
        cell["upper"] = {"d": d, "src": src, "paper": paper}

# ---- EA-Plotkin corrections (paper 1) ---------------------------------------
plot = json.load(open(ROOT / "artifacts" / "tables" / "plotkin_corrections.json"))
for e in plot:
    cell = touch(2, e["n"], e["k"], e["c"])
    cell["plotkin"] = {"du_table": e["du_table"], "du_new": e["du_plotkin"]}

# ---------------------------------------------------------------- q = 4, 5
# No codetables.de table exists at these local dimensions, so every cell is
# ours.  Provenance ranks: floor witness > theorem > explicit witness >
# implied by ebit-lifting; walls are searches that found nothing (NOT proofs).
Q45_NMAX = 20
WITNESS = {
    4: [(8, 5), (10, 4), (10, 5), (10, 6), (10, 7), (12, 6), (12, 7), (12, 8),
        (12, 9), (14, 8), (14, 9), (14, 10), (14, 11)],
    5: [(12, 5), (12, 6), (12, 7), (12, 8), (12, 9), (14, 7), (14, 8), (14, 9),
        (14, 10), (14, 11)],
}
# q=5 n=12 c=5 was reported as a wall by a short run, then found by a longer
# one; only walls that still stand are listed.
WALL = {4: [(12, 5), (14, 7)], 5: [(14, 6)]}

q45 = []
for q in (4, 5):
    thm_c = lambda n: n - q - 1          # unified theorem diagonal
    floor_c = lambda n: n - q - 2        # deepest layer reached by search
    wit = set(WITNESS[q])
    wall = set(WALL[q])
    for n in range(2 * q, Q45_NMAX + 1):
        for c in range(0, n):
            d = n - 1
            kind = None
            if (n, c) in wall:
                kind = "wall"
            elif (n, c) in wit and c == floor_c(n):
                kind = "floor"
            elif n >= 2 * q + 1 and c == thm_c(n):
                kind = "thm"
            elif (n, c) in wit:
                kind = "wit"
            elif n >= 2 * q + 1 and c > thm_c(n) and c <= n - 1:
                kind = "lift"
            if kind:
                q45.append({"q": q, "n": n, "k": 1, "c": c, "d": d, "kind": kind})

# ---------------------------------------------------------------- classify
out = []
stats = {"gap_closed": 0, "new_cell": 0, "lower_raised": 0, "upper_proved": 0,
         "pinned": 0, "plotkin": 0}
for key, cell in cells.items():
    lo, up = cell["lower"], cell["upper"]
    kind = None
    note = []
    if lo and up:
        kind = "both"
    elif lo:
        kind = "lower"
    elif up:
        kind = "upper"
    elif cell.get("plotkin"):
        kind = "plotkin"
    if kind is None:
        cell["kind"] = "table" if cell["listed"] else None
    else:
        cell["kind"] = kind
    # effect bookkeeping
    effective_upper = cell["du"]
    if up:
        effective_upper = up["d"] - 1 if effective_upper is None else min(effective_upper, up["d"] - 1)
    if cell.get("plotkin"):
        effective_upper = (cell["plotkin"]["du_new"] if effective_upper is None
                           else min(effective_upper, cell["plotkin"]["du_new"]))
    if lo:
        if cell["listed"]:
            if cell["dl"] < lo["d"]:
                if effective_upper is not None and lo["d"] >= effective_upper:
                    stats["gap_closed"] += 1
                    note.append("closes a listed gap (d_lower raised to d_upper)")
                else:
                    stats["lower_raised"] += 1
                    note.append("raises the listed lower bound")
            else:
                note.append("re-derives a value already listed")
        else:
            stats["new_cell"] += 1
            note.append("cell absent from the table — new parameter set")
    if up:
        stats["upper_proved"] += 1
        note.append(f"no code with d={up['d']} exists ⇒ d_upper ≤ {up['d']-1}")
    if cell.get("plotkin") and kind == "plotkin":
        stats["plotkin"] += 1
    if lo and up:
        stats["pinned"] += 1
    cell["note"] = note
    if cell["kind"]:
        out.append(cell)

# effective bounds after our work
for cell in out:
    dl, du = cell["dl"], cell["du"]
    if cell["lower"]:
        dl = cell["lower"]["d"] if dl is None else max(dl, cell["lower"]["d"])
    if cell["upper"]:
        du = cell["upper"]["d"] - 1 if du is None else min(du, cell["upper"]["d"] - 1)
    if cell.get("plotkin"):
        du = cell["plotkin"]["du_new"] if du is None else min(du, cell["plotkin"]["du_new"])
    cell["dl_new"], cell["du_new"] = dl, du

payload = {"cells": out, "stats": stats, "nmax": NMAX, "q45": q45,
           "q45_nmax": Q45_NMAX, "snapshot": f"codetables.de, {SNAP.name}"}
dst = args.out
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(payload))
print(json.dumps(stats, indent=1))
print("cells written:", len(out), "->", dst)
