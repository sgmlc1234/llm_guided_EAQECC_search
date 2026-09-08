#!/usr/bin/env python3
"""Summarize the EAQECC baseline arms into the ICLR comparison table/figure.

Usage: python3 scripts/eaqecc_baselines/summarize.py [--plot] [--targets residual|original|pinned] [--base DIR]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "artifacts" / "ablation"
# Directory names are the historical arm ids; the labels are the names the
# paper uses, so a reader can line the two up without a decoder ring.
LABEL = {
    "B0":  "Anneal        (pre-evolution human heuristic)",
    "B1":  "Ansatz-seed   (as shipped: crashes on most seeds)",
    "B1f": "Ansatz-seed   (shift bug fixed)",
    "B2":  "Evolved       (best program the search returned)",
}


def load(arm: str, target_set: str):
    s = BASE / target_set / arm / "summary.json"
    r = BASE / target_set / arm / "rounds.jsonl"
    if not r.exists():
        return None, []
    rounds = [json.loads(l) for l in r.open()]
    return (json.loads(s.read_text()) if s.exists() else None), rounds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--targets", default="residual",
                    choices=["residual", "original", "pinned"])
    ap.add_argument("--base", default=None,
                    help="ablation directory (default: artifacts/ablation)")
    ap.add_argument("--ci", action="store_true",
                    help="bootstrap the rounds (2000 resamples) and print a 95%% "
                         "interval for the number of cells closed within the budget")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    global BASE
    if args.base:
        BASE = Path(args.base)

    print(f"{'arm':4} {'program':30} {'gap':>4} {'rec':>4} {'all':>4} "
          f"{'rounds':>7} {'crash':>6} {'alloc(h)':>9} {'actual(h)':>10}")
    curves = {}
    for arm in sorted(LABEL):
        summary, rounds = load(arm, args.targets)
        if not rounds:
            print(f"{arm:4} {'(no data yet)':30}")
            continue
        last = rounds[-1]
        crashes = sum(1 for r in rounds if r["error"])
        closed = last["cumulative_closed"]
        alloc = last["compute_s"] / 3600
        actual = last["cumulative_actual_s"] / 3600
        # Split by target kind: "gap" entries are listed table entries with an
        # open distance gap; "record" cells are absent from the table. Record
        # cells are markedly easier, so a combined count flatters every arm.
        kinds = {"gap": 0, "record": 0}
        for f in (BASE / args.targets / arm / "solutions").glob("*.json"):
            k = json.loads(f.read_text())["target"].get("kind", "gap")
            kinds[k] = kinds.get(k, 0) + 1
        print(f"{arm:4} {LABEL[arm]:30} {kinds['gap']:4d} {kinds['record']:4d} "
              f"{closed:4d} {len(rounds):7d} "
              f"{crashes:6d} {alloc:9.2f} {actual:10.2f}")
        curves[arm] = [(r["compute_s"] / 3600, r["cumulative_closed"])
                       for r in rounds]
        if args.ci:
            # Rounds are independent seeds, so resampling them with
            # replacement gives the sampling distribution of "cells closed
            # within this budget" for one program at this compute.
            import random
            rng = random.Random(args.seed)
            per_round = [set(r["closed"]) for r in rounds]
            per_kind = {k: set() for k in ("gap", "record")}
            for f in (BASE / args.targets / arm / "solutions").glob("*.json"):
                d = json.loads(f.read_text())
                per_kind[d["target"].get("kind", "gap")].add(f"[[{d['target']['n']},{d['target']['k']},{d['target']['d']};{d['target']['c']}]]")
            tot, gap = [], []
            for _ in range(2000):
                u = set().union(*(per_round[rng.randrange(len(per_round))]
                                  for _ in range(len(per_round))))
                tot.append(len(u)); gap.append(len(u & per_kind["gap"]))
            tot.sort(); gap.sort()
            lo, hi = tot[int(0.025 * len(tot))], tot[int(0.975 * len(tot)) - 1]
            glo, ghi = gap[int(0.025 * len(gap))], gap[int(0.975 * len(gap)) - 1]
            print(f"       95% bootstrap over rounds: closed {lo}-{hi} (gap {glo}-{ghi})")
        if summary and summary["closed"]:
            for key in summary["closed"]:
                t = summary["first_closure_compute_s"][key] / 3600
                print(f"       {key:24} first closed at {t:.2f} h")

    if args.plot and curves:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.2, 3.4))
        for arm in sorted(curves):
            xs, ys = zip(*curves[arm])
            ax.step(xs, ys, where="post", label=f"{arm}: {LABEL[arm]}")
        ax.set_xlabel("allocated search compute (h)")
        ax.set_ylabel("open targets closed")
        ax.legend(fontsize=7, loc="upper left")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        out = BASE / f"baseline_curves_{args.targets}.pdf"
        fig.savefig(out)
        fig.savefig(out.with_suffix(".png"), dpi=160)
        print(f"\nfigure written: {out}")


if __name__ == "__main__":
    main()
