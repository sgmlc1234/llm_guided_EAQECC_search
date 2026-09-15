#!/usr/bin/env python3
"""Audit the computational EAQECC claims from the archived artifacts.

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
                  tool is absent -- reported separately from archive-only evidence; discrepancies fail.
  search          replays a fixed archived program. Meaningful only
                  under an evaluation budget: seed + N evaluations fix the
                  output, a wall-clock budget does not.

Exit status is nonzero if a check FAILs. Overall PARTIAL means at least
one selected check was not completed; it must not be interpreted as PASS.

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

PASS, FAIL, PARTIAL = "PASS", "FAIL", "PARTIAL"
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
    "witnesses": 115,
    "witnesses_by_q": {2: 65, 3: 27, 4: 13, 5: 10},
    "family_cells": {2: 29, 3: 25},          # listed-open cells the closed form settles
    "table_corrections": 398,
    "openness_cells": 65,                    # q=2 witness files, not unique cells
    "refutations_total": 10,                  # entries in the registry
    "refutations_certified": 9,              # of which ship CNF + DRAT
    "magma": 148,
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
        "paper_reference": a / "paper_reference.json",
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
    seen = set()
    expected_q = {"qubit": 2, "qutrit": 3}[which]
    for i, cell in enumerate(cells):
        missing = [f for f in SNAPSHOT_SCHEMA if f not in cell]
        if missing:
            raise ValueError(f"{snap.name}/{which}.json record {i} lacks {missing}")
        if any(type(cell[f]) is not int for f in SNAPSHOT_SCHEMA):
            raise ValueError(f"{which} record {i}: parameters must be integers")
        if (cell["q"] != expected_q or cell["n"] < 1
                or not 0 <= cell["k"] <= cell["n"] or cell["c"] < 0
                or not 0 <= cell["dl"] <= cell["du"]):
            raise ValueError(f"{which} record {i}: invalid parameter range")
        key = (cell["q"], cell["n"], cell["k"], cell["c"])
        if key in seen:
            raise ValueError(f"{which} record {i}: duplicate cell {key}")
        seen.add(key)
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
                              env=dict(os.environ, EAQECC_ROOT=str(ROOT), EAQECC_SNAPSHOT=SNAPSHOT.name))
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
def _best_witness_targets(q: int) -> dict:
    best = {}
    for path in _witness_files(q):
        t = dict(json.loads(path.read_text())["target"], q=q)
        key = (t["n"], t["k"], t["c"])
        if key not in best or t["d"] > best[key]["d"]:
            best[key] = t
    return best


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
    best = _best_witness_targets(q)
    return {"snapshot_cells": len(cells), "gap": open_gap,
            "record": open_record, "not_open": not_open,
            "unique_cells": len(best),
            "unique_listed_cells": sum(key in cells for key in best),
            "unique_absent_cells": sum(key not in cells for key in best)}



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
        + f"{total} q=2 witness files: {len(q2['gap'])} listed-and-open, "
        f"{len(q2['record'])} absent; {q2['unique_cells']} unique cells "
        f"({q2['unique_listed_cells']} listed, {q2['unique_absent_cells']} absent) in "
        f"{SNAPSHOT.name}; {len(q2['not_open'])} were not open"
        + (f" (q=3 witnesses: {extra['q3_gap']} listed-and-open, "
           f"{extra['q3_record']} absent, {len(extra['q3_not_open'])} not open)"
           if extra else ""),
        "gap_cells": len(q2["gap"]),
        "record_cells": len(q2["record"]),
        "unique_cells": q2["unique_cells"],
        "unique_listed_cells": q2["unique_listed_cells"],
        "unique_absent_cells": q2["unique_absent_cells"],
        "not_open": q2["not_open"],
        **extra,
    }


def check_solver_refinement() -> dict:
    from verify_solver_refinement import verify
    claims = json.loads((ROOT / "artifacts/solver_refinement/claims.json").read_text())
    expected = {"qubit_12_2_9": [12, 2, 9, 9], "qubit_13_1_8": [13, 1, 11, 8]}
    if len(claims) != 2 or {c["id"] for c in claims} != set(expected):
        return {"status": FAIL, "detail": "refinement ledger must contain both named cells"}
    registry = {e["tag"]: e for e in json.loads(
        (_paths()["refutations"] / "registry.json").read_text())}
    checked = []
    for c in claims:
        params = [c["n"], c["k"], c["d"], c["c"]]
        if params != expected[c["id"]]:
            return {"status": FAIL, "detail": f"incorrect refinement parameters: {c['id']}"}
        result = verify(ROOT / "artifacts" / c["witness"], params)
        if c["upper_kind"] == "EA-Plotkin":
            upper = (3 * 4 ** (c["k"] - 1) * c["n"]) // (4 ** c["k"] - 1)
        elif c["upper_kind"] == "certified-refutation":
            e = registry[c["refutation_tag"]]
            if ([e["q"], e["n"], e["k"], e["c"], e["d"]]
                    != [c["q"], c["n"], c["k"], c["c"], c["d"] + 1]
                    or e.get("status") != "certified"
                    or not (_paths()["refutations"] / e["cnf"]).is_file()
                    or not (_paths()["refutations"] / e["drat"]).is_file()):
                return {"status": FAIL, "detail": "refinement certificate link is invalid"}
            upper = e["d"] - 1
        else:
            return {"status": FAIL, "detail": "unknown refinement upper-bound source"}
        if upper != c["d"]:
            return {"status": FAIL, "detail": "refinement lower and upper bounds disagree"}
        result.update({"upper_bound": upper, "upper_kind": c["upper_kind"]})
        checked.append(result)
    return {"status": PASS,
            "detail": "two refinement witnesses independently re-derived; distance 9 "
                      "matches EA-Plotkin, distance 11 links to the archived d>=12 "
                      "certificate (fresh replay is reported by refutations)",
            "checked": checked}


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
    magma = os.environ.get("MAGMA_PATH") or shutil.which("magma")
    ssh_host = os.environ.get("MAGMA_SSH_HOST")
    # The current export holds all witnesses plus the family instances.
    # Earlier exports remain under history/. Whatever Magma reports
    # must equal the number of records it was handed, not a number typed
    # into this file.
    n_records = sum(1 for line in data.read_text().splitlines()
                    if line.lstrip().startswith("<")) if data.exists() else 0
    if n_records != EXPECTED["magma"]:
        return {"status": FAIL,
                "detail": f"archived Magma export holds {n_records} records, "
                          f"the paper says {EXPECTED['magma']}"}

    if (magma or ssh_host) and data.exists() and script.exists():
        if magma:
            proc = subprocess.run([magma, "-b", str(data), str(script)],
                                  capture_output=True, text=True,
                                  cwd=str(m), timeout=3600)
            mode = "re-ran Magma locally"
        else:
            import shlex
            if ssh_host.startswith("-"):
                raise ValueError("invalid MAGMA_SSH_HOST")
            ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", ssh_host]
            remote = subprocess.check_output(
                [*ssh, "mktemp -d /tmp/eaqecc-verify.XXXXXX"], text=True, timeout=30).strip()
            if not re.fullmatch(r"/tmp/eaqecc-verify\.[A-Za-z0-9]+", remote):
                raise ValueError("unexpected remote temporary directory")
            try:
                subprocess.run(["scp", "-q", str(data), str(script), f"{ssh_host}:{remote}/"],
                               check=True, capture_output=True, timeout=60)
                command = (f"cd {shlex.quote(remote)} && timeout 3600 magma -b "
                           f"{shlex.quote(data.name)} {shlex.quote(script.name)}")
                proc = subprocess.run([*ssh, command], capture_output=True,
                                      text=True, timeout=3660)
            finally:
                cleanup = (f"rm -f {shlex.quote(remote + '/' + data.name)} "
                           f"{shlex.quote(remote + '/' + script.name)} && rmdir {shlex.quote(remote)}")
                subprocess.run([*ssh, cleanup], capture_output=True, timeout=30)
            mode = "re-ran Magma over SSH"
        text = proc.stdout
        mm = re.search(r"(\d+) verified, (\d+) mismatches", text)
        n, bad = (int(mm.group(1)), int(mm.group(2))) if mm else (0, -1)
        ok = proc.returncode == 0 and bad == 0 and n == n_records
        return {"status": PASS if ok else FAIL, "mode": mode,
                "detail": f"{mode}: {n}/{n_records} records verified, {bad} mismatches",
                "returncode": proc.returncode, "export_sha256": sha256(data, full=True)}

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


def validate_qutrit_normalization(entry: dict, cnf: Path) -> dict:
    """Check the recorded representative-CNF transformation, not the lemma's proof."""
    meta = json.loads((_paths()["refutations"] / entry["normalization"]).read_text())
    n, k, c, d, q = (entry[x] for x in ("n", "k", "c", "d", "q"))
    j = n - k - c
    if q != 3 or k != 1 or d != n - 1 or j <= 2:
        return {"status": FAIL, "detail": "coordinate-normalization lemma does not apply"}
    if any(meta.get(key) != entry[key] for key in ("q", "n", "k", "c", "d")):
        return {"status": FAIL, "detail": "normalization metadata target mismatch"}
    units = [1 + 3 * (i * 2 * n + 2 * t) for i in range(j) for t in range(n)]
    lines = cnf.read_text().splitlines()
    header = lines[0].split()
    if (meta.get("unit_literals") != units
            or lines[-len(units):] != [f"{u} 0" for u in units]
            or int(header[3]) != meta["base_clauses"] + len(units)):
        return {"status": FAIL, "detail": "normalization clauses do not match the declared frame"}
    header[3] = str(meta["base_clauses"])
    original = " ".join(header) + "\n" + "\n".join(lines[1:-len(units)]) + "\n"
    if (hashlib.sha256(original.encode()).hexdigest() != meta["source_sha256"]
            or sha256(cnf, full=True) != meta["normalized_sha256"]):
        return {"status": FAIL, "detail": "normalization source/CNF hash mismatch"}
    return {"status": PASS, "detail": f"{len(units)} coordinate-frame units; "
            "applicability and source hash checked; see the coordinate-projection lemma"}


def check_refutations() -> dict:
    """Report archive grade, solver re-decision and proof replay separately."""
    import gzip
    import tempfile
    ref_dir = _paths()["refutations"]
    registry = json.loads((ref_dir / "registry.json").read_text())
    solver = _find_solver()
    checker = os.environ.get("DRAT_TRIM_PATH") or shutil.which("drat-trim")
    cache = Path(os.environ["EAQECC_PROOF_CACHE"]) if os.environ.get("EAQECC_PROOF_CACHE") else None
    certified, on_demand, decisions, malformed, entries = [], [], [], [], []
    unsat = replayed = with_cnf = proof_available = 0

    def execute(argv, timeout, success):
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status": PARTIAL, "detail": "verification timed out"}
        ok = success(result)
        return {"status": PASS if ok else FAIL, "returncode": result.returncode,
                "detail": result.stdout[-300:] if not ok else "verified"}

    for e in registry:
        cnf = ref_dir / e["cnf"] if e.get("cnf") else None
        shipped = ref_dir / e["drat"] if e.get("drat") else None
        entry = {"tag": e["tag"], "grade": e.get("status", ""),
                 "solver": {"status": SKIP_TOOL},
                 "certificate": {"status": SKIP_DATA}}
        entries.append(entry)
        if cnf is None:
            if not e.get("status", "").startswith("decision"):
                malformed.append(e["tag"])
            decisions.append(e["tag"])
            entry["solver"] = {"status": SKIP_DATA, "detail": "no archived CNF; decision record only"}
            continue
        if not cnf.is_file():
            malformed.append(e["tag"])
            continue
        with cnf.open() as stream:
            header = stream.readline().split()
        if len(header) != 4 or header[:2] != ["p", "cnf"]:
            malformed.append(e["tag"])
            continue
        if e.get("encoder") == "coordinate-normal-q3":
            entry["normalization"] = validate_qutrit_normalization(e, cnf)
            if entry["normalization"]["status"] != PASS:
                malformed.append(e["tag"])
                continue
        proof = shipped
        if shipped is not None:
            if not shipped.is_file() or shipped.stat().st_size == 0:
                malformed.append(e["tag"])
                continue
            certified.append(e["tag"])
        elif e.get("status") == "certified-on-demand":
            on_demand.append(e["tag"])
            candidate = cache / (e["tag"] + ".drat") if cache else None
            proof = candidate if candidate and candidate.is_file() else None
        else:
            malformed.append(e["tag"])
            continue
        with_cnf += 1
        if solver:
            entry["solver"] = execute([str(solver), "-q", str(cnf)], 1800,
                                      lambda result: result.returncode == 20)
            unsat += entry["solver"]["status"] == PASS
        if proof is None:
            entry["certificate"]["detail"] = "on-demand proof not in EAQECC_PROOF_CACHE"
            continue
        proof_available += 1
        if not checker:
            entry["certificate"] = {"status": SKIP_TOOL, "detail": "no DRAT checker"}
            continue
        with tempfile.TemporaryDirectory(prefix="eaqecc_proof_") as tmp:
            uncompressed = proof
            if proof.suffix == ".gz":
                uncompressed = Path(tmp) / "proof.drat"
                with gzip.open(proof, "rb") as source, uncompressed.open("wb") as target:
                    shutil.copyfileobj(source, target)
            entry["certificate"] = execute([str(checker), str(cnf), str(uncompressed)], 3600,
                lambda result: result.returncode == 0
                and re.search(r"^s VERIFIED\s*$", result.stdout, re.MULTILINE) is not None)
        replayed += entry["certificate"]["status"] == PASS
    short = (len(registry) != EXPECTED["refutations_total"]
             or len(certified) != EXPECTED["refutations_certified"]
             or len(on_demand) != 1 or len(decisions) != 0)
    statuses = [v[operation]["status"] for v in entries for operation in ("solver", "certificate")]
    if malformed or short or FAIL in statuses:
        status = FAIL
    elif not solver and not checker:
        status = SKIP_TOOL
    elif any(v != PASS for v in statuses):
        status = PARTIAL
    else:
        status = PASS
    detail = (f"{len(certified)} CNF/proof pairs, {len(on_demand)} on-demand proof, "
              f"{len(decisions)} decision-only record; {unsat}/{with_cnf} CNFs "
              f"re-decided UNSAT; {replayed}/{proof_available} available certificates "
              "replayed; unperformed checks are listed per entry")
    if malformed or short:
        detail = "registry or artifact coverage mismatch; " + detail
    return {"status": status, "detail": detail, "certified": certified,
            "on_demand": on_demand, "decisions": decisions, "malformed": malformed,
            "entries": entries, "solver_redecided": unsat,
            "certificates_replayed": replayed, "certificates_available": proof_available}


# ----------------------------------------------------- novelty-drift
def check_novelty_drift() -> dict:
    """Compare dated bounds for both q=2 and q=3, without inferring authorship."""
    snaps = available_snapshots()
    if len(snaps) < 2:
        return {"status": SKIP_DATA, "detail": "only one snapshot; add a newer dated snapshot"}
    old, new = snaps[0], snaps[-1]
    by_q, missing, changed_total = {}, [], 0
    for q, name in ((2, "qubit"), (3, "qutrit")):
        if not (old / f"{name}.json").exists() or not (new / f"{name}.json").exists():
            missing.append(name)
            continue
        old_cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(old, name)}
        new_cells = {(c["n"], c["k"], c["c"]): c for c in load_snapshot(new, name)}
        removed = sorted(set(old_cells) - set(new_cells))
        if removed:
            return {"status": FAIL, "detail": f"latest {name} snapshot omits "
                    f"{len(removed)} previously listed cells; check source completeness"}
        changes = [{"cell": key, "before": [old_cells[key]["dl"], old_cells[key]["du"]],
                    "after": [new_cells[key]["dl"], new_cells[key]["du"]]}
                   for key in old_cells.keys() & new_cells.keys()
                   if (old_cells[key]["dl"], old_cells[key]["du"])
                   != (new_cells[key]["dl"], new_cells[key]["du"])]
        changed_total += len(changes)
        unmatched, previously_matched, newly_matched = [], [], []
        for key, t in _best_witness_targets(q).items():
            previous, current = old_cells.get(key), new_cells.get(key)
            if current is None or current["dl"] < t["d"]:
                unmatched.append(_tag(t))
            elif previous is not None and previous["dl"] >= t["d"]:
                previously_matched.append(_tag(t))
            else:
                newly_matched.append({"code": _tag(t), "now": current["dl"],
                                      "provenance": current.get("title", "")})
        by_q[q] = {"old_records": len(old_cells), "new_records": len(new_cells),
                   "bound_changes": changes, "unmatched": unmatched,
                   "previously_matched": previously_matched, "newly_matched": newly_matched}
    return {"status": SKIP_DATA if missing else PASS,
            "detail": f"{old.name} -> {new.name}: q=2,3 comparison; {changed_total} "
                      f"changed bounds; {sum(len(v['newly_matched']) for v in by_q.values())} "
                      "witness cells newly matched by listed bounds; independent discovery "
                      "is not inferred from a table update",
            "compared": [old.name, new.name], "by_q": by_q, "missing_tables": missing}


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
    "solver-refinement": ("deterministic", check_solver_refinement,
                          "independent witness and upper-bound links for two refined cells"),
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
    ap.add_argument("--snapshot", default="paper",
                    help="paper (default: artifacts/paper_reference.json), latest, "
                         "or a dated directory name")
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
    if args.snapshot == "paper":
        args.snapshot = json.loads(_paths()["paper_reference"].read_text())["snapshot"]
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

    if worst != FAIL and any(r["status"] != PASS for r in results.values()):
        worst = PARTIAL
    report = {"snapshot": SNAPSHOT.name,
              "snapshots_available": [s.name for s in snaps],
              "python": sys.version.split()[0],
              "overall": worst, "all_selected_checks_completed": worst == PASS,
              "claims": results}
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
