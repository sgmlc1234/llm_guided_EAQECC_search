#!/usr/bin/env python3
"""The auditor: one command re-derives every claim from the archived artifacts.

    python3 scripts/reproduce_eaqecc.py                 # every claim
    python3 scripts/reproduce_eaqecc.py --tier deterministic
    python3 scripts/reproduce_eaqecc.py --claim witnesses
    python3 scripts/reproduce_eaqecc.py --list-snapshots

Claims are grouped by REPRODUCIBILITY TIER, because they are not the same
kind of claim and a report that prints PASS for all of them would hide the
distinction that matters:

  deterministic   pure Python + NumPy, no solver, no network, any machine.
                  Re-derivation is exact, so the result is a proof
                  obligation discharged, not a measurement.
  external        needs a tool the reader may not have (Magma, a SAT
                  solver, a DRAT checker). Reported SKIPPED_NO_TOOL when the
                  tool is absent -- never required for a claim to hold,
                  always binding when the tool is present and disagrees.
  search          reproduces the discovery step itself. Meaningful only
                  under an evaluation budget: seed + N evaluations fix the
                  output, a wall-clock budget does not.

Exit status is 0 unless some claim FAILs. SKIPPED is not a failure; it is
the auditor saying what it could not check here and why.

Data lives under --root (default: the repository this file sits in) and
code next to this file, so the same auditor can be pointed at a copy of the
archive -- that is how the negative-control tests in tests/ work.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # code
ROOT = Path(os.environ.get("EAQECC_ROOT") or HERE.parent)   # data
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "alphaevolve_eaqecc"))

PASS, FAIL = "PASS", "FAIL"
SKIP_TOOL, SKIP_DATA = "SKIPPED_NO_TOOL", "SKIPPED_NO_DATA"
SKIPS = (SKIP_TOOL, SKIP_DATA)

# Set in main() from --snapshot; never hard-code a date. The auditor is
# meant to outlive any one state of the tables: drop a new dated directory
# into artifacts/codetables_snapshots/ and every claim re-runs against it.
SNAPSHOT: Path | None = None

SNAPSHOT_SCHEMA = ("q", "n", "k", "c", "dl", "du")

# The manuscript states these counts. Printing what we happen to find lets
# a truncated archive pass quietly, so each claim asserts its number and
# fails when the archive is not the one the paper describes.
EXPECTED = {
    "witnesses": 114,
    "witnesses_by_q": {2: 64, 3: 27, 4: 13, 5: 10},
    "family_cells": {2: 29, 3: 25},          # listed-open cells the closed form settles
    "table_corrections": 398,
    "openness_cells": 64,                    # sporadic q=2 witnesses
    "refutations_total": 9,                  # entries in the registry
    "refutations_certified": 7,              # of which ship CNF + DRAT
    "magma": 122,
    # What the archived task specifications must say. The first campaigns
    # OFFERED the cyclic-shift symmetry ansatz as one of seven directions;
    # the later ones STATED the finding. Asserting both keeps the paper's
    # attribution honest in both directions: an archive edited to hide the
    # hint fails here as loudly as one edited to invent it.
    "prompts": {"campaign1": ["cyclic qubit shifts"],
                "campaign2": ["cyclic qubit shifts"],
                "campaign3": ["cyclic-shift ansatz", "[[7,1,6;4]]"],
                "campaign4": ["cyclic-shift ansatz", "[[7,1,6;4]]"]},
}


def _paths():
    """Data layout under ROOT, resolved late so --root can change it."""
    a = ROOT / "artifacts"
    return {
        "snapshots": a / "codetables_snapshots",
        "witnesses": a / "witnesses",
        "refutations": a / "refutations",
        "tables": a / "tables",
        "magma": a / "magma",
        "out": a / "reproduce_eaqecc",
        "manifest": ROOT / "MANIFEST.sha256",
    }


def available_snapshots() -> list[Path]:
    """Dated snapshot directories, oldest first. A directory qualifies if
    it holds a qubit.json; qutrit.json is optional."""
    root = _paths()["snapshots"]
    if not root.exists():
        return []
    return sorted((d for d in root.iterdir()
                   if d.is_dir() and (d / "qubit.json").exists()),
                  key=lambda d: d.name)


def load_snapshot(snap: Path, which: str = "qubit") -> list:
    """Read one table of a snapshot, checking every record has the fields
    the claims rely on. A malformed snapshot fails loudly here rather than
    silently skewing an openness check."""
    cells = json.loads((snap / f"{which}.json").read_text())
    for i, cell in enumerate(cells):
        missing = [f for f in SNAPSHOT_SCHEMA if f not in cell]
        if missing:
            raise ValueError(
                f"{snap.name}/{which}.json record {i} lacks {missing}; "
                f"expected records with {SNAPSHOT_SCHEMA}")
    return cells


def sha256(path: Path, full: bool = False) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h if full else h[:16]


def _witness_files(q: int) -> list[Path]:
    return sorted(Path(p) for p in glob.glob(
        str(_paths()["witnesses"] / f"q{q}" / "SOLUTION*.json")))


def _tag(t: dict) -> str:
    sub = "" if t.get("q", 2) == 2 else f"_{t['q']}"
    return f"[[{t['n']},{t['k']},{t['d']};{t['c']}]]{sub}"


# -------------------------------------------------- archive-integrity
def check_archive_integrity() -> dict:
    """Every archived input hashes to what MANIFEST.sha256 says.

    The other claims re-derive results *from* the archive; this one checks
    the archive is the one we published. A missing or altered file fails.
    Files present but unlisted (a reader adding a newer snapshot, say) are
    reported, not failed -- adding data is the intended way to extend the
    audit."""
    p = _paths()
    if not p["manifest"].exists():
        return {"status": FAIL, "detail": "MANIFEST.sha256 missing; run "
                                         "scripts/make_manifest.py"}
    listed, missing, altered = {}, [], []
    for line in p["manifest"].read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        rel = rel.strip()
        listed[rel] = digest
        f = ROOT / rel
        if not f.exists():
            missing.append(rel)
        elif sha256(f, full=True) != digest:
            altered.append(rel)
    present = {str(f.relative_to(ROOT)) for f in (ROOT / "artifacts").rglob("*")
               if f.is_file() and p["out"] not in f.parents
               and f.name != ".DS_Store"}
    unlisted = sorted(present - set(listed))
    ok = not missing and not altered
    return {
        "status": PASS if ok else FAIL,
        "detail": f"{len(listed)} archived files listed; {len(missing)} missing, "
                  f"{len(altered)} altered, {len(unlisted)} present but unlisted",
        "missing": missing[:10], "altered": altered[:10],
        "unlisted": unlisted[:10],
    }


# --------------------------------------------------------- witnesses
def check_witnesses() -> dict:
    """Re-derive (n, k, d, c) for every archived witness, from generators
    alone, in pure Python. q = 2 witnesses carry the S side as bit-packed
    integers; q = 3, 4, 5 witnesses carry the L side as F_q vectors. Any
    derived quantity stored next to a witness is ignored."""
    import helpers_eaqecc as H2
    from helpers_eaqecc_fq import Fq, evaluate_L

    checked, mismatches = [], []

    for p in _witness_files(2):
        s = json.loads(p.read_text())
        t = s["target"]
        r = H2.evaluate(t["n"], s["generators"], t["d"])
        ok = ("error" not in r and r["k"] == t["k"] and r["c"] == t["c"]
              and r["d"] == t["d"] and r["offending"] == 0)
        rec = {"file": p.name, "q": 2,
               "claimed": [t["n"], t["k"], t["d"], t["c"]],
               "rederived": None if "error" in r
               else [t["n"], r["k"], r["d"], r["c"]], "ok": ok}
        checked.append(rec)
        if not ok:
            mismatches.append(rec)

    for q in (3, 4, 5):
        F = Fq(q)
        for p in _witness_files(q):
            s = json.loads(p.read_text())
            t = s["target"]
            if t.get("q", q) != q:
                mismatches.append({"file": p.name, "q": q,
                                   "error": f"filed under q={q}, claims q={t.get('q')}"})
                continue
            r = evaluate_L(F, t["n"], s["L_basis"], t["d"])
            ok = ("error" not in r and r["k"] == t["k"] and r["c"] == t["c"]
                  and r["d"] == t["d"] and r["offending"] == 0)
            rec = {"file": p.name, "q": q,
                   "claimed": [t["n"], t["k"], t["d"], t["c"]],
                   "rederived": None if "error" in r
                   else [t["n"], r["k"], r["d"], r["c"]], "ok": ok}
            checked.append(rec)
            if not ok:
                mismatches.append(rec)

    by_q: dict[int, int] = {}
    for c in checked:
        by_q[c["q"]] = by_q.get(c["q"], 0) + 1
    short = (len(checked) != EXPECTED["witnesses"]
             or by_q != EXPECTED["witnesses_by_q"])
    return {
        "status": FAIL if (mismatches or short) else PASS,
        "expected": EXPECTED["witnesses"],
        "detail": (f"expected {EXPECTED['witnesses']}, found {len(checked)} "
                   f"({EXPECTED['witnesses_by_q']} vs {by_q}); " if short else "")
        + f"{len(checked)} archived witnesses re-derived "
        f"({', '.join(f'q={q}: {n}' for q, n in sorted(by_q.items()))}); "
        f"{len(mismatches)} mismatches",
        "n_checked": len(checked),
        "by_q": by_q,
        "mismatches": mismatches,
    }


# ---------------------------------------------------------- families
def _family_cells_closed() -> dict:
    """Listed-open table cells the closed form [[n,1,n-1;n-q-1]]_q settles,
    read off the snapshot. At q=2 the family sits at c=n-3 directly. At
    q=3 the closed form sits at c=n-4 and the table's listed cells at
    c=n-3 follow by one application of ebit lifting (a code at c gives one
    at c+1, same n, k, d)."""
    out = {}
    for q, which in ((2, "qubit"), (3, "qutrit")):
        if not (SNAPSHOT / f"{which}.json").exists():
            continue
        cells = load_snapshot(SNAPSHOT, which)
        out[q] = sorted(c["n"] for c in cells
                        if c["k"] == 1 and c["c"] == c["n"] - 3
                        and c["dl"] < c["n"] - 1 <= c["du"])
    return out


def check_families() -> dict:
    """Instantiate the closed-form families and verify every member in pure
    Python: the q=2 family with a stdlib-only script (S-side brute force up
    to n=11), and the unified [[n,1,n-1;n-q-1]]_q construction at
    q=2,3,4,5 together with the qutrit table family. Then count, from the
    snapshot, which listed-open cells those families settle."""
    runs = {}
    for name, argv in (("q2", [str(HERE / "families" / "verify_family.py"), "24"]),
                       ("unified", [str(HERE / "families" / "verify_floor.py")])):
        proc = subprocess.run([sys.executable, *argv], capture_output=True,
                              text=True, cwd=str(HERE / "families"),
                              env=dict(os.environ, EAQECC_ROOT=str(ROOT)))
        tail = (proc.stdout or proc.stderr).strip().splitlines()[-2:]
        runs[name] = {"returncode": proc.returncode, "tail": tail}
    cells = _family_cells_closed()
    counts = {q: len(v) for q, v in cells.items()}
    short = counts != EXPECTED["family_cells"]
    ok = all(r["returncode"] == 0 for r in runs.values()) and not short
    return {
        "status": PASS if ok else FAIL,
        "detail": (f"expected family cells {EXPECTED['family_cells']}, found "
                   f"{counts}; " if short else "")
        + "; ".join(f"{k}: rc={v['returncode']} {v['tail'][-1] if v['tail'] else ''}"
                    for k, v in runs.items())
        + f"; families settle {sum(counts.values())} listed-open cells "
          f"({', '.join(f'q={q}: {n}' for q, n in sorted(counts.items()))}) "
          f"in {SNAPSHOT.name}",
        "runs": runs,
        "table_cells_closed": cells,
    }


# -------------------------------------------------- table-correction
def check_table_correction() -> dict:
    """Recompute the EA-Plotkin correction from the dated snapshot and
    check it against the archived correction list.

    EA-Plotkin (Guo-Li 2013): (4^k - 1) d <= 3 * 4^(k-1) n, so any listed
    upper bound above floor(3 * 4^(k-1) n / (4^k - 1)) is not attainable."""
    archived = json.loads((_paths()["tables"] / "plotkin_corrections.json").read_text())
    cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(SNAPSHOT)}

    disagree = []
    for rec in archived:
        n, k, c = rec["n"], rec["k"], rec["c"]
        bound = (3 * 4 ** (k - 1) * n) // (4 ** k - 1)
        cell = cells.get((n, k, c))
        ok = (bound == rec["du_plotkin"]
              and cell is not None and cell["du"] == rec["du_table"]
              and bound < rec["du_table"])
        if not ok:
            disagree.append({**rec, "recomputed_bound": bound,
                             "snapshot_du": cell["du"] if cell else None})
    short = len(archived) != EXPECTED["table_corrections"]
    return {
        "status": FAIL if (disagree or short) else PASS,
        "detail": (f"expected {EXPECTED['table_corrections']} corrections, "
                   f"found {len(archived)}; " if short else "")
        + f"{len(archived)} corrected upper bounds recomputed from "
        f"the {SNAPSHOT.name} snapshot; {len(disagree)} disagree",
        "n_corrections": len(archived),
        "disagreements": disagree[:10],
    }


# ---------------------------------------------------------- openness
def _openness_split(q: int, which: str) -> dict:
    cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(SNAPSHOT, which)}
    open_gap, open_record, not_open = [], [], []
    for p in _witness_files(q):
        t = json.loads(p.read_text())["target"]
        cell = cells.get((t["n"], t["k"], t["c"]))
        if cell is None:
            open_record.append(_tag(t))
        elif cell["dl"] < t["d"] <= cell["du"]:
            open_gap.append(_tag(t))
        else:
            not_open.append({"code": _tag(t), "snapshot_dl": cell["dl"],
                             "snapshot_du": cell["du"]})
    return {"snapshot_cells": len(cells), "gap": open_gap,
            "record": open_record, "not_open": not_open}


def check_openness() -> dict:
    """Every sporadic cell we claim to have closed must have been genuinely
    open in the dated snapshot: listed with dl < d <= du (a gap cell), or
    absent from the table (a record cell). This is what makes the results
    new rather than rediscovered. The qutrit witnesses are reported
    against the qutrit table as well, informationally: the paper's
    openness count is the q=2 set."""
    q2 = _openness_split(2, "qubit")
    total = len(q2["gap"]) + len(q2["record"])
    short = total != EXPECTED["openness_cells"]
    # A snapshot missing records makes every unmatched cell look like a
    # record cell, i.e. *more* novel. Guard the direction that flatters us.
    suspicious = len(q2["gap"]) == 0 and len(q2["record"]) == total
    extra = {}
    if (SNAPSHOT / "qutrit.json").exists():
        q3 = _openness_split(3, "qutrit")
        extra = {"q3_gap": len(q3["gap"]), "q3_record": len(q3["record"]),
                 "q3_not_open": q3["not_open"]}
    return {
        "status": FAIL if (q2["not_open"] or short or suspicious) else PASS,
        "snapshot_cells": q2["snapshot_cells"],
        "detail": (f"expected {EXPECTED['openness_cells']} cells, found "
                   f"{total}; " if short else "")
        + ("no cell was listed-and-open, which usually means the "
           "snapshot is truncated; " if suspicious else "")
        + f"{len(q2['gap'])} closed q=2 cells were listed-and-open and "
        f"{len(q2['record'])} were absent from the table in "
        f"{SNAPSHOT.name}; {len(q2['not_open'])} were not open"
        + (f" (q=3 witnesses: {extra['q3_gap']} listed-and-open, "
           f"{extra['q3_record']} absent, {len(extra['q3_not_open'])} not open)"
           if extra else ""),
        "gap_cells": len(q2["gap"]),
        "record_cells": len(q2["record"]),
        "not_open": q2["not_open"],
        **extra,
    }


# -------------------------------------------------- magma-crosscheck
def check_magma_crosscheck() -> dict:
    """Corroboration in a second computer algebra system.

    Magma is licensed software most readers will not have, so this claim
    has two modes and says which one it is in. With a Magma binary it
    re-runs the verification and reads the fresh result. Without one it
    falls back to the archived log -- evidence that we ran it, not evidence
    the reader can reproduce -- and reports that plainly."""
    m = _paths()["magma"]
    log, data, version = (m / "magma_verification.log", m / "eaqecc_data.m",
                          m / "magma_version.txt")
    script = HERE / "verify_eaqecc.magma"
    magma = shutil.which("magma")
    # The archived export holds every object Magma was given: the witnesses
    # of this artifact plus the instantiated family members, and two
    # corridor witnesses from a companion study. Whatever Magma reports
    # must equal the number of records it was handed, not a number typed
    # into this file.
    n_records = sum(1 for line in data.read_text().splitlines()
                    if line.lstrip().startswith("<")) if data.exists() else 0
    if n_records != EXPECTED["magma"]:
        return {"status": FAIL,
                "detail": f"archived Magma export holds {n_records} records, "
                          f"the paper says {EXPECTED['magma']}"}

    if magma and data.exists() and script.exists():
        proc = subprocess.run([magma, "-b", str(data), str(script)],
                              capture_output=True, text=True,
                              cwd=str(m), timeout=3600)
        out = proc.stdout
        mm = re.search(r"(\d+) verified", out)
        n = int(mm.group(1)) if mm else 0
        ok = "MISMATCH" not in out and n == n_records
        return {"status": PASS if ok else FAIL, "mode": "re-ran Magma",
                "detail": f"re-ran Magma on {n_records} records: {n} verified"
                          + ("" if ok else " -- disagreement")}

    if not log.exists():
        return {"status": SKIP_TOOL,
                "detail": "no Magma binary and no archived log"}
    text = log.read_text()
    mm = re.search(r"(\d+) verified, (\d+) mismatches", text)
    n, bad = (int(mm.group(1)), int(mm.group(2))) if mm else (0, -1)
    ok = bad == 0 and n == n_records
    return {
        "status": SKIP_TOOL if ok else FAIL,
        "mode": "archived log only",
        "detail": "no Magma binary on PATH; read the archived log instead "
                  "(evidence we ran it, not a reproduction): "
                  f"{n} of {n_records} exported records verified, {bad} mismatches"
                  + (f" [{version.read_text().strip()}]" if version.exists() else ""),
        "log_sha256": sha256(log),
    }


# ------------------------------------------------------- refutations
def _find_solver() -> Path | None:
    env = os.environ.get("CADICAL_PATH")
    if env and Path(env).exists():
        return Path(env)
    w = shutil.which("cadical")
    return Path(w) if w else None


def check_refutations() -> dict:
    """Cells closed by proving them empty.

    The registry lists every nonexistence result the paper uses, in three
    grades. *Certified*: CNF and DRAT proof shipped, so the refutation can
    be replayed by any conforming checker and re-decided by any solver
    without trusting ours. *Certified on demand*: CNF shipped and the proof
    regenerable in about a minute, but too large to ship. *Decision*: the
    solver's answer is on record and nothing else; never counted as
    certified. Presence of a tool never decides the status; only what the
    tool says does."""
    import gzip
    import tempfile
    R = _paths()["refutations"]
    reg_path = R / "registry.json"
    if not reg_path.exists():
        return {"status": FAIL, "detail": "no refutation registry"}
    registry = json.loads(reg_path.read_text())
    solver, checker = _find_solver(), shutil.which("drat-trim")

    certified, on_demand, decisions, malformed = [], [], [], []
    with_cnf, unsat, replayed = 0, 0, 0
    for e in registry:
        cnf = R / e["cnf"] if e.get("cnf") else None
        drat = R / e["drat"] if e.get("drat") else None
        if cnf is None or not cnf.exists():
            decisions.append(e["tag"])
            continue
        head = cnf.read_text().splitlines()[0].split()
        if not (len(head) == 4 and head[0] == "p" and head[1] == "cnf"):
            malformed.append(e["tag"])
            continue
        if drat is None:
            on_demand.append(e["tag"])
        elif not (drat.exists() and drat.stat().st_size > 0):
            malformed.append(e["tag"])
            continue
        else:
            certified.append(f"{e['tag']} ({head[2]} vars, {head[3]} clauses)")
        with_cnf += 1
        if solver:
            r = subprocess.run([str(solver), "-q", str(cnf)],
                               capture_output=True, text=True, timeout=1800)
            unsat += 1 if r.returncode == 20 else 0      # 20 = UNSAT, 10 = SAT
        if checker and drat is not None:
            if drat.suffix == ".gz":
                with tempfile.NamedTemporaryFile(suffix=".drat", delete=False) as tmp:
                    tmp.write(gzip.decompress(drat.read_bytes()))
                    proof = Path(tmp.name)
            else:
                proof = drat
            r = subprocess.run([checker, str(cnf), str(proof)],
                               capture_output=True, text=True, timeout=3600)
            replayed += 1 if "s VERIFIED" in r.stdout else 0
            if proof != drat:
                proof.unlink()

    short = (len(registry) != EXPECTED["refutations_total"]
             or len(certified) != EXPECTED["refutations_certified"])
    detail = ((f"expected {EXPECTED['refutations_total']} registry entries with "
               f"{EXPECTED['refutations_certified']} certified, found "
               f"{len(registry)}/{len(certified)}; " if short else "")
              + f"{len(certified)} certified (CNF + DRAT shipped), "
              f"{len(on_demand)} certified on demand (CNF shipped, proof "
              f"regenerable), {len(decisions)} solver decisions on record only"
              + (f" [{', '.join(decisions)}]" if decisions else "") + "; "
              + (f"{unsat}/{with_cnf} CNFs re-decided UNSAT" if solver
                 else "no solver found (CADICAL_PATH or cadical on PATH), "
                      "nothing re-decided") + "; "
              + (f"{replayed}/{len(certified)} proofs replayed" if checker
                 else "no DRAT checker (drat-trim) found, proofs not replayed"))
    if malformed or short:
        status = FAIL
    elif solver and unsat != with_cnf:
        status = FAIL
    elif checker and replayed != len(certified):
        status = FAIL
    elif solver or checker:
        status = PASS
    else:
        status = SKIP_TOOL
    return {"status": status, "detail": detail, "certified": certified,
            "on_demand": on_demand, "decisions": decisions, "malformed": malformed}


# ----------------------------------------------------- novelty-drift
def check_novelty_drift() -> dict:
    """Novelty is a claim about a moving object, so it has to be re-checked
    as the object moves. For every cell we closed, compare the oldest and
    newest snapshots available; a cell since closed by someone else is
    priority information the reader is entitled to. Drop a fresh dated
    directory into artifacts/codetables_snapshots/ to run this."""
    snaps = available_snapshots()
    if len(snaps) < 2:
        return {"status": SKIP_DATA,
                "detail": f"only {len(snaps)} snapshot(s) present "
                          f"({', '.join(s.name for s in snaps) or 'none'}); "
                          f"add a newer dated directory to measure drift",
                "snapshots": [s.name for s in snaps]}
    old, new = snaps[0], snaps[-1]
    old_cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(old)}
    new_cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(new)}

    still_open, closed_by_others = [], []
    for p in _witness_files(2):
        t = json.loads(p.read_text())["target"]
        cell = new_cells.get((t["n"], t["k"], t["c"]))
        if cell is None or cell["dl"] < t["d"]:
            still_open.append(_tag(t))
        else:
            closed_by_others.append(
                {"code": _tag(t), "was": old_cells.get((t["n"], t["k"], t["c"]), {}).get("dl"),
                 "now": cell["dl"]})
    return {
        "status": PASS,
        "detail": f"{old.name} -> {new.name}: {len(still_open)} of our cells "
                  f"still unmatched, {len(closed_by_others)} reached "
                  f"independently since",
        "compared": [old.name, new.name],
        "superseded": closed_by_others,
    }



# -------------------------------------------------- prompt-provenance
def check_prompt_provenance() -> dict:
    """The task specifications the model was given, archived verbatim.

    Two claims in the paper are only checkable against them: that the
    first campaigns were offered a cyclic-shift symmetry ansatz as one
    direction among seven, and that the later campaigns had the finding
    written into their prompt (which is what makes their seeds unusable as
    baselines). Each archived text must contain the phrases the paper
    quotes from it."""
    P = ROOT / "artifacts" / "campaigns" / "prompts"
    missing, wrong, found = [], [], {}
    for label, phrases in EXPECTED["prompts"].items():
        f = P / f"{label}.txt"
        if not f.exists():
            missing.append(label)
            continue
        text = f.read_text()
        absent = [ph for ph in phrases if ph not in text]
        found[label] = {"chars": len(text), "phrases_present": len(phrases) - len(absent)}
        if absent:
            wrong.append({"campaign": label, "expected_phrase_absent": absent})
    ok = not missing and not wrong
    same12 = ((P / "campaign1.txt").exists() and (P / "campaign2.txt").exists()
              and (P / "campaign1.txt").read_text() == (P / "campaign2.txt").read_text())
    return {
        "status": PASS if ok else FAIL,
        "detail": (f"missing {missing}; " if missing else "")
        + (f"phrases absent {wrong}; " if wrong else "")
        + f"{len(found)} archived task specifications; campaigns 1-2 "
        + ("share one text" if same12 else "differ")
        + "; campaign 1 offers the cyclic-shift symmetry ansatz as a direction, "
          "campaign 3 states the finding",
        "campaigns": found,
    }

# ------------------------------------------------ search-determinism
FP_SEEDS = [20260814, 20260815, 20260816, 20260817]
FP_EVALS = 5000
# Fingerprint every arm that produced archived results, not just the
# baseline: the evolved program is the one whose output the paper reports.
FP_ARMS = ["B0", "B1f", "B2"]


def _fingerprint_path() -> Path:
    return HERE / "eaqecc_baselines" / "search_fingerprint.json"


def _run_search(arm: str, seed: int, max_evals: int) -> list:
    """One deterministic search round; returns the proposal list."""
    import tempfile
    sys.path.insert(0, str(HERE / "eaqecc_baselines"))
    import run_baseline as RB

    campaign, harvest = RB.build_campaign_dir(RB.TARGET_SETS["residual"])
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out_f = Path(tmp) / "r.json"
            env = dict(os.environ,
                       TIME_BUDGET_S="240", MAX_EVALS=str(max_evals),
                       EVAL_RNG_SEED=str(seed), HARVEST_DIR=str(harvest))
            subprocess.run(
                [sys.executable, str(campaign / "driver_deterministic.py"),
                 str(RB.ARMS[arm]), str(out_f)],
                env=env, check=False, capture_output=True, timeout=1800)
            r = json.loads(out_f.read_text()) if out_f.exists() else {}
    finally:
        shutil.rmtree(campaign, ignore_errors=True)
    return r.get("candidates", [])


def check_search_determinism(emit: bool = False) -> dict:
    """The discovery step itself reproduces bit-for-bit.

    Only meaningful under the evaluation budget: the candidate program sees
    a virtual clock that advances once per exact evaluation, so seed + N
    determine the proposal list regardless of machine speed."""
    fp = _fingerprint_path()
    fresh = {f"{arm}:{s}": _run_search(arm, s, FP_EVALS)
             for arm in FP_ARMS for s in FP_SEEDS}
    if emit:
        fp.write_text(json.dumps(
            {"arms": FP_ARMS, "target_set": "residual", "max_evals": FP_EVALS,
             "proposals": fresh}, indent=1))
        return {"status": PASS,
                "detail": f"fingerprint written for {len(fresh)} runs "
                          f"({len(FP_ARMS)} arms x {len(FP_SEEDS)} seeds)"}
    if not fp.exists():
        return {"status": SKIP_DATA,
                "detail": "no stored fingerprint; run with --emit-fingerprint"}
    stored = json.loads(fp.read_text())
    differing = [k for k in fresh if fresh[k] != stored["proposals"].get(k)]
    return {
        "status": PASS if not differing else FAIL,
        "detail": f"{len(fresh)} seeded searches re-run at {FP_EVALS} "
                  f"evaluations ({', '.join(FP_ARMS)}); {len(differing)} "
                  f"differ from the stored proposal lists",
        "differing_runs": differing,
    }


CLAIMS = {
    "archive-integrity": ("deterministic", check_archive_integrity,
                          "every archived input hashes to the published manifest"),
    "witnesses": ("deterministic", check_witnesses,
                  "every archived code re-derived from generators alone"),
    "families": ("deterministic", check_families,
                 "closed-form families instantiated and verified per member, "
                 "at every q, and their table cells counted"),
    "table-correction": ("deterministic", check_table_correction,
                         "EA-Plotkin correction recomputed from the snapshot"),
    "openness": ("deterministic", check_openness,
                 "every closed cell was open in the dated snapshot"),
    "novelty-drift": ("deterministic", check_novelty_drift,
                      "novelty re-checked against the newest table snapshot"),
    "refutations": ("external", check_refutations,
                    "archived nonexistence proofs replayed; decisions listed"),
    "magma-crosscheck": ("external", check_magma_crosscheck,
                         "independent re-derivation in a second computer "
                         "algebra system"),
    "search-determinism": ("search", check_search_determinism,
                           "the seeded discovery step reproduces bit-for-bit"),
    "prompt-provenance": ("deterministic", check_prompt_provenance,
                          "the task specifications given to the model are "
                          "archived and say what the paper says they say"),
}


def main(argv=None):
    global SNAPSHOT, ROOT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--claim", default=None, choices=sorted(CLAIMS))
    ap.add_argument("--tier", default=None,
                    choices=["deterministic", "external", "search"])
    ap.add_argument("--snapshot", default="latest",
                    help="dated snapshot directory name, or 'latest' "
                         "(default). Claims are always evaluated against a "
                         "named state of the tables, never a live query.")
    ap.add_argument("--list-snapshots", action="store_true")
    ap.add_argument("--root", default=None,
                    help="directory holding artifacts/ and MANIFEST.sha256 "
                         "(default: this repository)")
    ap.add_argument("--out", default=None,
                    help="where to write the report (default: "
                         "<root>/artifacts/reproduce_eaqecc)")
    ap.add_argument("--emit-fingerprint", action="store_true",
                    help="regenerate the search fingerprint on this machine")
    args = ap.parse_args(argv)
    if args.root:
        ROOT = Path(args.root).resolve()

    snaps = available_snapshots()
    if args.list_snapshots:
        for s in snaps:
            tables = sorted(p.stem for p in s.glob("*.json"))
            print(f"{s.name}  ({', '.join(tables)})")
        if not snaps:
            print(f"no snapshots under {_paths()['snapshots']}")
        return 0
    if not snaps:
        sys.exit(f"no table snapshots under {_paths()['snapshots']}; each must "
                 f"be a dated directory holding qubit.json with records "
                 f"{SNAPSHOT_SCHEMA}")
    if args.snapshot == "latest":
        SNAPSHOT = snaps[-1]
    else:
        match = [s for s in snaps if s.name == args.snapshot]
        if not match:
            sys.exit(f"snapshot '{args.snapshot}' not found; have: "
                     + ", ".join(s.name for s in snaps))
        SNAPSHOT = match[0]

    if args.emit_fingerprint:
        r = check_search_determinism(emit=True)
        print(f"{r['status']:16} search-determinism  {r['detail']}")
        return 0

    selected = [c for c in CLAIMS
                if (args.claim is None or c == args.claim)
                and (args.tier is None or CLAIMS[c][0] == args.tier)]

    out_dir = Path(args.out) if args.out else _paths()["out"]
    out_dir.mkdir(parents=True, exist_ok=True)
    results, worst = {}, PASS

    print(f"snapshot: {SNAPSHOT.name}   root: {ROOT}")
    for cid in selected:
        tier, fn, desc = CLAIMS[cid]
        try:
            r = fn()
        except Exception as e:  # noqa: BLE001
            r = {"status": FAIL, "detail": f"{type(e).__name__}: {e}"}
        r.update({"tier": tier, "description": desc})
        results[cid] = r
        if r["status"] == FAIL:
            worst = FAIL
        print(f"{r['status']:16} {cid:18} [{tier}] {r['detail']}", flush=True)

    report = {"snapshot": SNAPSHOT.name,
              "snapshots_available": [s.name for s in snaps],
              "python": sys.version.split()[0],
              "overall": worst, "claims": results}
    (out_dir / "reproduction_report.json").write_text(json.dumps(report, indent=1))

    lines = ["# EAQECC reproduction report", "",
             f"Snapshot: `{SNAPSHOT.name}` "
             f"(available: {', '.join(s.name for s in snaps)})"
             f"  ·  Python {report['python']}  ·  Overall: **{worst}**", "",
             "| Claim | Tier | Status | Detail |", "|---|---|---|---|"]
    for cid, r in results.items():
        lines.append(f"| `{cid}` | {r['tier']} | {r['status']} | {r['detail']} |")
    (out_dir / "REPRODUCTION_REPORT.md").write_text("\n".join(lines) + "\n")

    print(f"\noverall: {worst}  ->  {out_dir / 'REPRODUCTION_REPORT.md'}")
    return 0 if worst != FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
