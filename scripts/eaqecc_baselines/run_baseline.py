#!/usr/bin/env python3
"""Matched-compute baseline comparison for the EAQECC discovery campaign.

Every arm searches the SAME target set under the SAME protocol: R
independent rounds of TIME_BUDGET_S seconds, one fixed seed per round,
candidates re-verified exactly in this process. Total search compute per arm
is R * TIME_BUDGET_S, matched across arms.

Arms:
  B0   seed_naive_sa.py                     pre-evolution human heuristic
  B1   alphaevolve_eaqecc/program.py        run-9 seed as shipped (crashes)
  B1f  seed_run9_fixed.py                   run-9 seed, shift bug fixed
  B2   artifacts/campaigns/run9_top_programs/rank01_1001000.py  best evolved program

Target sets (--targets):
  residual  scripts/alphaevolve_eaqecc/targets.json      309 still-open cells
  original  targets_original68.json    68 pre-campaign gap-one entries
  pinned    targets_family_pinned.json the four family instances only

B1, B1f and B2 are contaminated with respect to `original` and `pinned`:
their headers name the cyclic-shift ansatz and the instances it closed.
Only B0 may be run on those sets.

Rounds are executed through the campaign's own driver.py, so the candidate
cap (16 proposals, 40 generators) and the isolation model are identical to
what the evolution runs faced. Because helpers_eaqecc derives TARGETS from
`targets.json` next to itself, minus every target whose SOLUTION file exists
in HARVEST_DIR, each run gets a scratch campaign directory holding copies of
helpers_eaqecc.py, driver.py and the chosen target file renamed
targets.json, plus an empty harvest dir that is kept empty. The originals
are never touched and target indices stay fixed across rounds.

Usage:
    python3 scripts/eaqecc_baselines/run_baseline.py \
        --arm B0 --targets residual --rounds 80 --budget 240 --workers 4 \
        --out /tmp/my_ablation      # default appends to the archived rounds
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CAMPAIGN = REPO / "scripts" / "alphaevolve_eaqecc"

ARMS = {
    "B0": HERE / "seed_naive_sa.py",
    "B1": CAMPAIGN / "program.py",
    "B1f": HERE / "seed_run9_fixed.py",
    "B2": (REPO / "artifacts" / "campaigns" / "run9_top_programs"
           / "rank01_1001000.py"),
}
TARGET_SETS = {
    "residual": CAMPAIGN / "targets.json",
    "original": HERE / "targets_original68.json",
    "pinned": HERE / "targets_family_pinned.json",
}
CONTAMINATED = {"B1", "B1f", "B2"}   # may not be run on original / pinned

E = None  # helpers module, imported in main() from the scratch campaign dir


def run_round(args) -> dict:
    """Execute one search round in a driver subprocess. Returns raw result."""
    program, budget, seed, index, campaign_dir, harvest_dir, max_evals = args
    driver = "driver.py" if max_evals is None else "driver_deterministic.py"
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        out_f = Path(tmp) / "result.json"
        env = dict(os.environ,
                   TIME_BUDGET_S=str(budget),
                   EVAL_RNG_SEED=str(seed),
                   HARVEST_DIR=harvest_dir)
        if max_evals is not None:
            env["MAX_EVALS"] = str(max_evals)
        proc = subprocess.run(
            [sys.executable, str(Path(campaign_dir) / driver),
             str(program), str(out_f)],
            env=env, timeout=budget * 1.5 + 60, check=False,
            capture_output=True)
        if out_f.exists():
            result = json.loads(out_f.read_text())
        else:
            result = {"candidates": [], "elapsed": time.time() - t0,
                      "error": f"driver produced no output (rc={proc.returncode}): "
                               f"{proc.stderr.decode()[-400:]}"}
    result["round"] = index
    result["seed"] = seed
    result["wall_s"] = time.time() - t0
    return result


def verify(result: dict) -> dict:
    """Exactly re-verify every proposal; classify the round."""
    closed, progress, invalid, mismatch = [], [], 0, 0
    best_offending = None
    for tid, gens in result["candidates"]:
        t = E.TARGETS[tid]
        r = E.evaluate(t["n"], gens, t["d"])
        if "error" in r:
            invalid += 1
            continue
        if r["c"] != t["c"] or r["k"] != t["k"]:
            mismatch += 1
            continue
        off = r["offending"]
        best_offending = off if best_offending is None else min(best_offending, off)
        key = f"[[{t['n']},{t['k']},{t['d']};{t['c']}]]"
        if off == 0:
            closed.append({"tid": tid, "key": key, "target": t,
                           "generators": [int(g) for g in gens],
                           "verified": r})
        else:
            progress.append({"tid": tid, "key": key, "offending": off})
    return {"closed": closed, "progress": progress, "invalid": invalid,
            "signature_mismatch": mismatch, "best_offending": best_offending}


def build_campaign_dir(target_file: Path) -> tuple[Path, Path]:
    """Scratch copy of the campaign machinery pinned to one target file."""
    scratch = Path(tempfile.mkdtemp(prefix="eaqecc_campaign_"))
    shutil.copy(CAMPAIGN / "helpers_eaqecc.py", scratch / "helpers_eaqecc.py")
    shutil.copy(CAMPAIGN / "driver.py", scratch / "driver.py")
    shutil.copy(HERE / "driver_deterministic.py",
                scratch / "driver_deterministic.py")
    shutil.copy(target_file, scratch / "targets.json")
    harvest = scratch / "empty_harvest"       # must stay empty: see docstring
    harvest.mkdir()
    return scratch, harvest


def main():
    global E
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--targets", default="residual", choices=sorted(TARGET_SETS))
    ap.add_argument("--rounds", type=int, default=80)
    ap.add_argument("--budget", type=float, default=240.0)
    ap.add_argument("--seed0", type=int, default=20260814)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--max-evals", type=int, default=None,
                    help="switch to the reproducible evaluation budget: the "
                         "candidate sees a virtual clock that advances once "
                         "per exact evaluation, so seed + N fix the output "
                         "regardless of machine speed")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.targets != "residual" and args.arm in CONTAMINATED:
        sys.exit(f"arm {args.arm} is contaminated for target set "
                 f"'{args.targets}' (its header names the ansatz and the "
                 f"instances it closed); only B0 is valid there")

    program = ARMS[args.arm]
    if not program.exists():
        sys.exit(f"program for arm {args.arm} not found: {program}")

    campaign_dir, harvest = build_campaign_dir(TARGET_SETS[args.targets])
    os.environ["HARVEST_DIR"] = str(harvest)
    sys.path.insert(0, str(campaign_dir))
    import helpers_eaqecc  # noqa: E402
    E = helpers_eaqecc

    out_dir = Path(args.out or (REPO / "artifacts" / "ablation"
                                / args.targets)) / args.arm
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "rounds.jsonl"
    sol_dir = out_dir / "solutions"
    sol_dir.mkdir(exist_ok=True)

    print(f"arm={args.arm} program={program.name} targets={args.targets}"
          f"({len(E.TARGETS)}) rounds={args.rounds} budget={args.budget:g}s "
          f"total={args.rounds * args.budget / 3600:.2f}h workers={args.workers}",
          flush=True)

    jobs = [(program, args.budget, args.seed0 + i, i, str(campaign_dir),
             str(harvest), args.max_evals) for i in range(args.rounds)]
    solved, first_closure, done = {}, {}, 0
    actual_s, crashes = 0.0, 0
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as pool, \
            jsonl.open("a") as log:
        for result in pool.map(run_round, jobs):
            v = verify(result)
            done += 1
            actual_s += result["elapsed"]
            crashes += 1 if result["error"] else 0
            # Compute allocated once this round completed, not wall clock:
            # rounds may run concurrently. A round that crashes early still
            # consumed its allocation, so the curves are plotted against
            # allocated compute; actual_s records what was really spent.
            compute_s = done * args.budget
            for c in v["closed"]:
                if c["key"] not in solved:
                    solved[c["key"]] = c
                    first_closure[c["key"]] = compute_s
                    (sol_dir / f"SOLUTION_n{c['target']['n']}_k{c['target']['k']}"
                               f"_c{c['target']['c']}_d{c['target']['d']}.json"
                     ).write_text(json.dumps(c, indent=1))
                    print(f"  [{args.arm}] CLOSED {c['key']} at "
                          f"{compute_s / 3600:.2f}h of search compute", flush=True)
            log.write(json.dumps({
                "arm": args.arm, "targets": args.targets,
                "round": result["round"], "seed": result["seed"],
                "elapsed_s": result["elapsed"], "wall_s": result["wall_s"],
                "error": result["error"], "n_proposals": len(result["candidates"]),
                "closed": [c["key"] for c in v["closed"]],
                "progress": v["progress"][:5],
                "invalid": v["invalid"],
                "signature_mismatch": v["signature_mismatch"],
                "best_offending": v["best_offending"],
                "cumulative_closed": len(solved),
                "compute_s": compute_s,
                "cumulative_actual_s": actual_s,
            }) + "\n")
            log.flush()
            print(f"  [{args.arm}] round {done}/{args.rounds} "
                  f"proposals={len(result['candidates'])} "
                  f"closed_total={len(solved)}", flush=True)

    (out_dir / "summary.json").write_text(json.dumps({
        "arm": args.arm,
        "program": str(program),
        "target_set": args.targets,
        "n_targets": len(E.TARGETS),
        "rounds": args.rounds,
        "budget_s": args.budget,
        "total_search_s": args.rounds * args.budget,
        "actual_search_s": actual_s,
        "crashed_rounds": crashes,
        "wall_s": time.time() - t_start,
        "seed0": args.seed0,
        "closed": sorted(solved),
        "n_closed": len(solved),
        "first_closure_compute_s": first_closure,
    }, indent=1))
    shutil.rmtree(campaign_dir, ignore_errors=True)
    print(f"arm={args.arm} done: {len(solved)} targets closed in "
          f"{args.rounds * args.budget / 3600:.2f}h of search compute", flush=True)


if __name__ == "__main__":
    main()
