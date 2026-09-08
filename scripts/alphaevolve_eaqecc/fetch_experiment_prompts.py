#!/usr/bin/env python3
"""Recover the task specification of past campaigns from the AlphaEvolve service.

The problem description an experiment was created with is stored server
side, not in the campaign log, so the claim that a construction was *not*
named in a prompt is only auditable once that text is archived. This
fetches each experiment's config and writes

    artifacts/campaigns/prompts/<label>.json    the full experiment record
    artifacts/campaigns/prompts/<label>.txt     its problem_description

Experiment resource names are taken from the command line or extracted
from campaign logs (the lines that print `experiment_name:`).

    PROJECT_ID=... GE_APP_ID=... python3 scripts/alphaevolve_eaqecc/fetch_experiment_prompts.py \
        --from-log campaign_run7.log=campaign1 --from-log run9.log=campaign3

Needs Application Default Credentials for the project that ran the
campaigns (docs/alphaevolve_gcp_setup.md). Read only: nothing is created.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from alpha_evolve.client import AlphaEvolveClient

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "campaigns" / "prompts"
NAME_RE = re.compile(r"projects/[^\s/]+/locations/[^\s/]+/collections/[^\s/]+/"
                     r"engines/[^\s/]+/sessions/\d+/alphaEvolveExperiments/\d+")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="experiment resource names")
    ap.add_argument("--from-log", action="append", default=[],
                    metavar="LOG=LABEL", help="extract the experiment name from a log")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    project, engine = os.getenv("PROJECT_ID", ""), os.getenv("GE_APP_ID", "")
    if not (project and engine):
        sys.exit("set PROJECT_ID and GE_APP_ID (docs/alphaevolve_gcp_setup.md)")
    client = AlphaEvolveClient(project_id=project, location=os.getenv("LOCATION", "global"),
                               engine=engine)
    jobs = [(n, n.rsplit("/", 1)[-1]) for n in args.names]
    for spec in args.from_log:
        log, _, label = spec.partition("=")
        found = sorted(set(NAME_RE.findall(Path(log).read_text(errors="replace"))))
        if not found:
            sys.exit(f"no experiment name in {log}")
        for i, n in enumerate(found):
            jobs.append((n, (label or Path(log).stem) + ("" if len(found) == 1 else f"_{i}")))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, label in jobs:
        rec = client.get_alpha_evolve_experiment(name)
        if not rec:
            print(f"{label}: no record returned for {name}", file=sys.stderr)
            continue
        cfg = rec.get("config", {})
        desc = cfg.get("problemDescription") or cfg.get("problem_description") or ""
        # keep the record, but not the account-identifying resource path
        rec_public = {k: v for k, v in rec.items() if k != "name"}
        (out / f"{label}.json").write_text(json.dumps(rec_public, indent=1))
        (out / f"{label}.txt").write_text(desc)
        print(f"{label}: {len(desc)} chars of task text -> {out / (label + '.txt')}")


if __name__ == "__main__":
    main()
