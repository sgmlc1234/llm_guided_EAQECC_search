# Reproducibility checklist

Start with the [reviewer guide](REVIEWER_GUIDE.md) and the [paper result map](RESULTS_AND_EVIDENCE.md).

What a reader needs in order to check each thing the paper says, and where
it lives. Organised the way ICLR's reproducibility guidance asks: code,
data, environment, randomness, compute, and what is *not* reproducible.

| Item | Where | Notes |
|---|---|---|
| One-command reproduction | `python3 scripts/reproduce_eaqecc.py` | exits nonzero on any failed claim; writes `artifacts/reproduce_eaqecc/` |
| Claims graded by what they need | `--tier deterministic \| external \| search` | missing checks produce an overall PARTIAL result; inspect solver/proof status per entry |
| Archive integrity | `MANIFEST.sha256`, claim `archive-integrity` | every archived input is hashed; CI checks the manifest is current |
| Environment | `requirements*.txt`, CI matrix py3.9 + py3.12 | deterministic tier: Python ≥ 3.9, NumPy ≥ 2.0, nothing else |
| Data | `artifacts/codetables_snapshots/<date>/` | two dated snapshots; paper_reference.json fixes the manuscript comparison; latest is explicit |
| Witnesses | `artifacts/witnesses/q{2,3,4,5}/` | generators only; every derived quantity is recomputed |
| Families | `scripts/families/` | closed forms instantiated and verified in pure Python at q = 2, 3, 4, 5 |
| Nonexistence | `artifacts/refutations/registry.json` | 9 shipped CNF/DRAT pairs and 1 on-demand proof; qutrit completeness lemma in the manuscript and qutrit_certificate.md |
| Second implementation | `scripts/verify_eaqecc.magma`, `artifacts/magma/` | 148-object export; local Magma or explicit MAGMA_SSH_HOST, otherwise archive-only evidence |
| Randomness | `EVAL_RNG_SEED`, `MAX_EVALS` | seed + evaluation budget fix the search output; wall clock never enters |
| Search replay | claim `search-determinism`, `scripts/eaqecc_baselines/search_fingerprint.json` | 3 programs × 4 seeds, proposal lists compared bit for bit |
| Compute | paper App. B; `artifacts/campaigns/*.log` | 401 completed worker searches × 240 s = 26.73 h of nominal search allowance across four campaigns; service counters additionally include each initial seed |
| Ablation data | `experiments/hitl_ablation/` | latest balanced 56-proposal study; 60 attempted requests, 58 received sources; offline audit and sandboxed replay via `scripts/eaqecc_ablation/` |
| Prompts | `artifacts/campaigns/prompts/campaign{1..4}.{txt,json}`, claim `prompt-provenance` | recovered from the service with `scripts/alphaevolve_eaqecc/fetch_experiment_prompts.py`; includes per-campaign token counts |
| Negative controls | `tests/test_auditor_negative_controls.py` | the auditor is shown to FAIL on a damaged archive |
| Not reproducible | the evolutionary run itself | LLM sampling is nondeterministic; we replay programs, not their discovery |

## Refreshing the archive

Any legitimate change to `artifacts/` (a new snapshot, a new certificate)
must be followed by `python3 scripts/make_manifest.py`, and both committed
together; otherwise `archive-integrity` fails, by design.

## New refinement and snapshot coverage

The bundle includes a new `[[12,2,9;9]]_2` code and a checked d>=12 exclusion at `(n,k,c)=(13,1,8)`. The `solver-refinement` claim verifies codes and links upper-bound evidence, while `refutations` replays certificates. `openness` distinguishes 65 q=2 files from 61 unique cells. `novelty-drift` compares both q=2 and q=3 and does not label a changed table value as an independent discovery.

## Regenerating certificates

Use the isolated on-demand proof-cache command in README.md for the large qubit proof.
The qutrit certificate is included. [qutrit_certificate.md](qutrit_certificate.md)
gives its coordinate-normalization proof, exact CNF transformation and regeneration
commands. The auditor checks the recorded transformation and replays the DRAT proof;
it does not mechanically verify the mathematical lemma.
Proof files are large (megabytes for the k = 1 floor cells); they are kept
because a proof a reader can replay is the whole point of shipping them.

## Two numbers that look inconsistent and are not

`artifacts/tables/bound_map.json` reports `stats.plotkin = 396` while the
paper and the `table-correction` claim say 398. The bound map classifies
each cell once; two of the 398 Plotkin-corrected cells are also cells where
we constructed or refuted a code, and they are counted under that class
instead. The correction list itself has 398 entries.

The q=3 code `[[8,1,7;5]]_3` is listed in the qutrit table already
(`dl = du = 7`): it re-derives a known value and is kept as a code of the
closed-form cell, not claimed as new. The `openness` claim reports this.

## Manuscript terminology and algorithm numbering

The paper uses **codes**, **code constructions** and **generator matrices** for
existence results, and **DRAT proofs** or **certificates of unsatisfiability**
for solver-produced nonexistence evidence. Historical directory names such as
`artifacts/witnesses/`, `.witness.json` files and the `witnesses` auditor claim
remain unchanged so prior records, commands and integrity hashes remain valid.
Algorithm 1 is the archived AlphaEvolve rank05 construction program; Algorithm 2
in Appendix D.4 is the supplementary dual-space program from the ablation.
