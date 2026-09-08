#!/usr/bin/env python3
"""Re-derive the nonexistence results in artifacts/refutations/registry.json.

For every entry, rebuild the CNF with the named encoder, decide it with a
SAT solver, and -- this is the point -- ask for a DRAT certificate, so that
what the archive holds afterwards is a proof any checker can replay rather
than a solver's word. On success the entry is updated in place with the
artifact names, the solver version and the wall time.

    python3 scripts/refutations/run_registry.py            # entries lacking a proof
    python3 scripts/refutations/run_registry.py --all      # regenerate everything
    python3 scripts/refutations/run_registry.py --tag q2_n7_k1_c3_d6

An entry whose solver run exceeds --timeout is left as it was: a decision
on record, which the auditor reports as such and never as certified.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "artifacts" / "refutations" / "registry.json"
sys.path.insert(0, str(HERE))
from solver import find_solver, solver_version  # noqa: E402

ENCODERS = {
    "normal-form-q2": (HERE / "sat_normal_form_q2.py",
                       lambda e: ["--only", f"{e['n']},{e['k']},{e['c']},{e['d']}"]),
    "free-radical-q3": (HERE / "sat_free_radical_q3.py",
                        lambda e: [str(e["n"]), str(e["c"]), str(e["d"])]),
    "free-radical-fq": (HERE / "sat_free_radical_fq.py",
                        lambda e: [str(e["q"]), str(e["n"]), str(e["c"]), str(e["d"])]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args()
    find_solver()
    registry = json.loads(REG.read_text())
    out = REG.parent

    for e in registry:
        if args.tag and e["tag"] != args.tag:
            continue
        if e.get("encoder") not in ENCODERS:
            print(f"{e['tag']:24} {e.get('method','')}: no SAT encoder, skipped")
            continue
        if e.get("drat") and (out / e["drat"]).exists() and not args.all:
            print(f"{e['tag']:24} already certified ({e['drat']})")
            continue
        if e.get("status") == "certified-on-demand" and not args.all:
            print(f"{e['tag']:24} certified on demand; pass --all to regenerate the proof")
            continue
        script, argv = ENCODERS[e["encoder"]]
        cmd = [sys.executable, str(script), *argv(e), "--proof", "--out", str(out),
               "--timeout", str(args.timeout)]
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=args.timeout + 120, cwd=str(ROOT))
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = None
        dt = time.time() - t0
        log = out / f"{e['tag']}.log"
        log.write_text((proc.stdout + proc.stderr) if rc is not None else "TIMEOUT\n")
        cnf, drat = out / f"{e['tag']}.cnf", out / f"{e['tag']}.drat"
        if rc == 20 and cnf.exists() and drat.exists() and drat.stat().st_size > 0:
            e.update({"cnf": cnf.name, "drat": drat.name, "log": log.name,
                      "status": "certified", "solver": solver_version(),
                      "seconds": round(dt, 1)})
            print(f"{e['tag']:24} UNSAT, DRAT {drat.stat().st_size/1e6:.1f} MB, {dt:.0f}s")
        elif rc == 10:
            e.update({"status": "SAT -- registry entry is WRONG", "log": log.name})
            print(f"{e['tag']:24} *** SAT: a code exists; the registry is wrong ***")
        else:
            e.update({"status": "decision (re-run did not finish)", "log": log.name,
                      "seconds": round(dt, 1)})
            print(f"{e['tag']:24} rc={rc} after {dt:.0f}s; left as decision")
        REG.write_text(json.dumps(registry, indent=1) + "\n")


if __name__ == "__main__":
    main()
