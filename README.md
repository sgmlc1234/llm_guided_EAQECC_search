# A reproducible pipeline for LLM-guided discovery of entanglement-assisted quantum codes

Code, archived results and the **auditor** for a pipeline that attacks the
open cells of the entanglement-assisted quantum code tables with LLM-guided
program evolution, verifies what it finds in a second implementation, and
closes cells from the other side with SAT refutations.

The repository is organised around one command:

```bash
python3 scripts/reproduce_eaqecc.py
```

It re-derives every claim the paper makes from the archived artifacts,
prints one line per claim, exits nonzero if any fails, and writes a report
to `artifacts/reproduce_eaqecc/`. The [reference report](artifacts/reproduce_eaqecc/REPRODUCTION_REPORT.md)
is committed so you can compare your run against ours.

```
PASS             archive-integrity  [deterministic] 227 archived files listed; 0 missing, 0 altered
PASS             witnesses          [deterministic] 114 archived witnesses re-derived (q=2: 64, q=3: 27, q=4: 13, q=5: 10); 0 mismatches
PASS             families           [deterministic] closed forms verified at q=2,3,4,5; families settle 54 listed-open cells (q=2: 29, q=3: 25)
PASS             table-correction   [deterministic] 398 corrected upper bounds recomputed from the 2026-07-17 snapshot; 0 disagree
PASS             openness           [deterministic] 8 closed q=2 cells were listed-and-open and 56 were absent from the table; 0 were not open
SKIPPED_NO_DATA  novelty-drift      [deterministic] only 1 snapshot present; add a newer dated directory to measure drift
PASS             refutations        [external]      7 certified (CNF + DRAT shipped), 1 certified on demand, 1 solver decision; 8/8 CNFs re-decided UNSAT
SKIPPED_NO_TOOL  magma-crosscheck   [external]      no Magma binary; archived log: 122 of 122 exported records verified, 0 mismatches
PASS             search-determinism [search]        12 seeded searches re-run at 5000 evaluations (B0, B1f, B2); 0 differ
```

## Install

The deterministic tier needs **Python 3.9+ and NumPy 2.0+** and nothing
else: no solver, no network, no cloud credentials. The NumPy floor is real
--- the exact evaluator counts symplectic weight with `np.bitwise_count`,
added in 2.0.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # reproduce
pip install -r requirements-dev.txt        # + tests and lint
pip install -r requirements-figures.txt    # + regenerate figures
pip install -r requirements-search.txt     # + evolve new programs (needs Google Cloud)
```

Optional tools, each unlocking one `external` claim: a SAT solver
([CaDiCaL](https://github.com/arminbiere/cadical); set `CADICAL_PATH` or
put `cadical` on `PATH`), a DRAT checker
([drat-trim](https://github.com/marijnheule/drat-trim)), and Magma.

## What the auditor checks, and how each claim is graded

Claims are graded by **reproducibility tier** --- what a reader needs in
order to check them --- because a report that printed `PASS` uniformly
would hide the one distinction that matters.

| Claim | Tier | What it does |
|---|---|---|
| `archive-integrity` | deterministic | every archived input hashes to `MANIFEST.sha256` |
| `witnesses` | deterministic | recomputes $(n,k,d;c)$ for 114 archived codes from generators alone, at $q=2,3,4,5$ |
| `families` | deterministic | instantiates the closed forms $[[n,1,n-1;n-q-1]]_q$ at every $q$, verifies each member, counts the listed-open cells they settle |
| `table-correction` | deterministic | recomputes 398 EA-Plotkin corrections to listed upper bounds from the snapshot |
| `openness` | deterministic | checks every closed cell was genuinely open (listed gap, or absent) in the dated snapshot |
| `novelty-drift` | deterministic | compares oldest vs newest snapshot present; reports cells since reached by others |
| `refutations` | external | re-decides every archived CNF and replays every DRAT proof; lists decisions as decisions |
| `magma-crosscheck` | external | re-runs the Magma verification if Magma is present; otherwise reports the archived log *as a log* |
| `search-determinism` | search | replays three programs × four seeds under an evaluation budget, bit for bit |

`deterministic` holds on any machine. `external` is `SKIPPED_NO_TOOL` when
the tool is absent --- never a failure, never a pass --- and **binding when
the tool is present**: a solver that answers SAT fails the claim.
`SKIPPED_NO_DATA` marks a check that needs an input the archive does not
yet hold (a second snapshot). Run one tier or one claim:

```bash
python3 scripts/reproduce_eaqecc.py --tier deterministic
python3 scripts/reproduce_eaqecc.py --claim witnesses
```

### The auditor is itself tested

An auditor that only ever says `PASS` proves nothing, so
`tests/test_auditor_negative_controls.py` damages a private copy of the
archive in each of the ways that would flatter us --- a missing witness, a
forged generator, a truncated snapshot (which makes results look *more*
novel), a schema break deep in the table, an altered correction list, a
solver that lies --- and asserts the auditor fails.

```bash
python3 -m pytest
```

## Snapshots: no date is compiled in

Tables of best-known parameters move, so novelty claims decay after
publication. A snapshot is a dated directory under
`artifacts/codetables_snapshots/` holding `qubit.json` (and optionally
`qutrit.json`) as records `{q, n, k, c, dl, du, ...}`. The auditor
discovers whichever are present, evaluates against the newest by default,
and validates every record on load.

```bash
python3 scripts/reproduce_eaqecc.py --list-snapshots
python3 scripts/reproduce_eaqecc.py --snapshot 2026-07-17
```

Drop in a newer dated directory, run `python3 scripts/make_manifest.py`,
and `novelty-drift` starts reporting what has changed --- including, if it
happens, that someone reached one of these cells first.

## Refutations: proofs, not verdicts

`artifacts/refutations/registry.json` lists every nonexistence result the
paper uses, in three grades the auditor keeps apart:

- **certified** --- CNF and DRAT proof shipped (7 entries; proofs above a
  megabyte are gzipped). Replay with any conforming checker.
- **certified on demand** --- CNF shipped, proof regenerable in about a
  minute but too large to ship (1 entry, 583 MB).
- **decision** --- the solver's answer is on record and nothing else
  (1 entry). Never counted as certified.

```bash
python3 scripts/refutations/run_registry.py          # regenerate missing proofs (needs CaDiCaL)
```

## Reproducing the search, and its boundary

`search-determinism` replays the archived programs. It is meaningful only
under an **evaluation budget**: the programs spend a wall-clock budget, and
a seeded generator inside a wall-clock loop is not reproducible, because a
faster machine draws more random numbers and returns something else for
the same seed. `scripts/eaqecc_baselines/driver_deterministic.py` replaces
the `time` module the candidate sees with a virtual clock that advances
once per evaluation, so seed and budget fix the output on any machine.

What is **not** reproducible is the evolutionary run that produced those
programs: the model calls are nondeterministic and we did not attempt to
make them so. A reader can verify every result and re-run the search that
finds them; a reader cannot replay the discovery.

## The ablation

Three programs, matched compute, same target set; every round of every
arm is archived under `artifacts/ablation/`.

| Name | Directory | What it is |
|---|---|---|
| `Anneal` | `B0` | the human heuristic that preceded evolution |
| `Ansatz-seed` | `B1f` | the later human-written seed, already carrying the discovered construction |
| `Evolved` | `B2` | the best program the search returned |

```bash
python3 scripts/eaqecc_baselines/summarize.py --targets residual
python3 scripts/eaqecc_baselines/run_baseline.py --arm B0 --targets residual \
    --rounds 80 --budget 240 --workers 4 --out /tmp/my_ablation
```

`Ansatz-seed` and `Evolved` are refused on the pre-campaign target sets
(`original`, `pinned`): their program headers and prompts name the
construction and the instances it closed, so a "rediscovery" by them would
be circular. The runner enforces this rather than trusting the operator to
remember it. Pass `--max-evals N` to run under the reproducible evaluation
budget instead of wall clock.

## Evolving new programs

Needs a Google Cloud project allowlisted for AlphaEvolve. See
[docs/alphaevolve_gcp_setup.md](docs/alphaevolve_gcp_setup.md) for the
prerequisites and the exact `gcloud` commands; copy `.env.example` to
`.env` and fill in `PROJECT_ID` and `GE_APP_ID`. Neither has a default ---
a stale default silently calls a project that is not yours.

## Layout

```
scripts/reproduce_eaqecc.py        the auditor: one claim per function
scripts/alphaevolve_eaqecc/        search stage: exact evaluator, driver, seed program, campaign launcher
scripts/eaqecc_baselines/          ablation runner, deterministic driver, search fingerprint
scripts/families/                  pure-Python verification of the closed forms (q = 2; q = 2..5)
scripts/refutations/               SAT encoders (normal form, free radical), registry runner
scripts/verify_eaqecc.magma        the second implementation
scripts/build_bound_map.py         provenance data from the archive     -> artifacts/tables/bound_map.json
scripts/make_bound_map_figure.py   the paper's provenance figure (TikZ) from that data
scripts/make_manifest.py           MANIFEST.sha256
artifacts/codetables_snapshots/    dated table snapshots
artifacts/witnesses/q{2,3,4,5}/    every archived code, generators only
artifacts/refutations/             registry, CNFs, DRAT proofs
artifacts/tables/                  EA-Plotkin corrections, bound map
artifacts/magma/                   Magma export, archived log, version
artifacts/campaigns/               campaign logs and the top evolved programs
artifacts/ablation/                every round of every arm
tests/                             negative controls, evaluator, determinism
docs/                              GCP setup, reproducibility checklist, anonymization checklist
```

Everything under `artifacts/` is hashed in `MANIFEST.sha256`; a change
there without a manifest update fails `archive-integrity`, by design.

## License

MIT. The AlphaEvolve client this depends on for the search stage is
Google's, Apache-2.0, and is not vendored here.
