"""Launch the AlphaEvolve EAQECC multi-target campaign (codetables gaps).

Usage:
    .venv/bin/python scripts/alphaevolve_eaqecc/run_evolution.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import nest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parent))

from alpha_evolve.client import AlphaEvolveClient
from alpha_evolve.controller import run_controller_loop
from alpha_evolve.experiment import AlphaEvolveExperiment

from evaluate import (
    INITIAL_PROGRAM_CODE,
    MAIN_METRIC,
    eaqecc_evaluation,
)

# No defaults for the two project-specific values: a stale default silently
# calls someone else's Cloud project. Both name resources you create in the
# Google Cloud console -- see docs/alphaevolve_gcp_setup.md.
PROJECT_ID = os.getenv("PROJECT_ID", "")
LOCATION = os.getenv("LOCATION", "global")
GE_APP_ID = os.getenv("GE_APP_ID", "")
MODEL_1 = os.getenv("MODEL_1", "gemini-3.5-flash")
MODEL_1_WEIGHT = float(os.getenv("MODEL_1_WEIGHT", "0.5"))
MODEL_2 = os.getenv("MODEL_2", "gemini-3.1-pro-preview")
MODEL_2_WEIGHT = float(os.getenv("MODEL_2_WEIGHT", "0.5"))
MAX_PROGRAMS_GENERATED = int(os.getenv("MAX_PROGRAMS_GENERATED", "120"))
MAX_PROGRAMS_EVALUATED = int(os.getenv("MAX_PROGRAMS_EVALUATED", "120"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "4"))
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))

PROBLEM_DESCRIPTION = """\
Target: 329 open parameter points of the codetables.de qubit EAQECC table
(Grassl), 5 <= n <= 13. Each target {n, k, c, d, dl, kind} asks for an
entanglement-assisted quantum code [[n,k,d;c]]. kind="gap": listed entry
with open distance gap. kind="record": an (n,k,c) cell ABSENT from the
table where reaching d beats the monotone staircase of known codes — a
brand-new parameter set. All targets respect the EA-Plotkin bound
(4^k-1)d <= 3*4^{k-1}n and EA-Singleton; eight proven-nonexistent points
are excluded. Closing ANY target is a new best-known quantum code.

Proven meta-lesson of this campaign: STRUCTURED CONSTRUCTION PROGRAMS beat
point search. A cyclic-shift ansatz (generators = 2-bit cyclic shifts of
one or two base Pauli strings) closed [[7,1,6;4]], [[9,1,8;6]],
[[11,1,10;8]] and was generalized by hand into an infinite optimal family
for odd n; a block ansatz (radical <X^b, Z^b> on a b-qubit block, logicals
= one-of-each-Pauli "transversal" block patterns times uniform tails) gave
the even-n branch. One good ansatz sweeps a whole ladder of targets at
once. Evolve NEW construction families: other shift steps / quasi-cyclic
orbits, multi-block radicals, GF(4)-additive constructions (Wilde-Brun:
c = rank of H H^dagger), extension/shortening/puncturing of the
already-closed [[n,1,n-1;n-3]] family, hyperbolic pairs + isotropic
completion, and transfer of a working ansatz across all targets sharing
its structure.

Representation: stabilizer set = s = n-k+c integers of 2n bits (per qubit
i: bit 2i = X, bit 2i+1 = Z); Gram rank exactly 2c required. You may also
construct the SMALL side L = S^perp (dim n+k-c) and convert via
E.nullspace([E._J(v, n) for v in L], 2*n). E.evaluate(n, gens, d_target)
verifies exactly in ~1-20 ms ("offending" = logical operators below the
target distance; 0 + matching (k,c) closes the target, +1e6 jackpot each).
Numeric care: generators are Python ints up to 2^26; avoid uint8/int32
numpy bit accumulation. Programs that crash or hang waste their slot.
"""


def _require_gcp_config():
    missing = [k for k, v in (("PROJECT_ID", PROJECT_ID),
                              ("GE_APP_ID", GE_APP_ID)) if not v]
    if missing:
        sys.exit(
            "missing required environment variable(s): " + ", ".join(missing)
            + "\n\nPROJECT_ID is your Google Cloud project; GE_APP_ID is the"
              " AlphaEvolve\napp (Discovery Engine engine) created in that"
              " project. Set both, e.g.\n\n"
              "    export PROJECT_ID=my-project\n"
              "    export GE_APP_ID=my-alphaevolve-app\n\n"
              "and authenticate once with\n\n"
              "    gcloud auth application-default login\n"
              "    gcloud auth application-default set-quota-project"
              " $PROJECT_ID\n\n"
              "See docs/alphaevolve_gcp_setup.md for the full prerequisites.")


def main():
    logging.basicConfig(level=logging.INFO)
    _require_gcp_config()

    client = AlphaEvolveClient(
        project_id=PROJECT_ID, location=LOCATION, engine=GE_APP_ID)

    experiment = AlphaEvolveExperiment(
        client, eaqecc_evaluation, MAX_PROGRAMS_EVALUATED,
        parallel_evaluation=True)

    models_raw = [(MODEL_1, MODEL_1_WEIGHT), (MODEL_2, MODEL_2_WEIGHT)]
    generation_models = [
        {"name": m, "weight": round(w, 2)}
        for m, w in {n: sum(w for n2, w in models_raw if n2 == n)
                     for n, _ in models_raw}.items() if m]

    exp_config = {
        "title": "EAQECC codetables gaps (68 open targets, n<=13)",
        "problem_description": PROBLEM_DESCRIPTION,
        "program_language": "python",
        "run_settings": {
            "max_programs": MAX_PROGRAMS_GENERATED,
            "concurrency": CONCURRENCY,
        },
        "generation_settings": {"models": generation_models},
    }

    experiment.create_experiment(exp_config)

    initial_program = {
        "content": {"files": [{"path": "program.py",
                               "content": INITIAL_PROGRAM_CODE}]},
        "evaluation": {"scores": {"scores": [
            {"metric": MAIN_METRIC, "score": -1e9}]}},
    }
    experiment.create_initial_program(initial_program)
    experiment.start_experiment()

    nest_asyncio.apply()
    search_budget = float(os.getenv("SEARCH_BUDGET_S", "240"))
    idle_timeout = int(search_budget * 1.5 + 60 + 180)
    asyncio.run(run_controller_loop(experiment,
                                    num_evaluators=WORKER_CONCURRENCY,
                                    idle_timeout_s=idle_timeout))

    response = experiment.list_programs()
    progs = (response or {}).get("alphaEvolvePrograms", [])
    print(f"\n=== {len(progs)} programs in experiment ===")
    from alpha_evolve.visualization import get_score
    progs.sort(key=lambda p: get_score(p, MAIN_METRIC), reverse=True)
    for i, p in enumerate(progs[:15]):
        print(f"rank {i+1}: score={get_score(p, MAIN_METRIC)} "
              f"name={p.get('name', '?')[-20:]}")


if __name__ == "__main__":
    main()
