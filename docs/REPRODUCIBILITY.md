# Reproducibility checklist

What a reader needs in order to check each thing the paper says, and where
it lives. Organised the way ICLR's reproducibility guidance asks: code,
data, environment, randomness, compute, and what is *not* reproducible.

| Item | Where | Notes |
|---|---|---|
| One-command reproduction | `python3 scripts/reproduce_eaqecc.py` | exits nonzero on any failed claim; writes `artifacts/reproduce_eaqecc/` |
| Claims graded by what they need | `--tier deterministic \| external \| search` | `SKIPPED_NO_TOOL` / `SKIPPED_NO_DATA` are never failures, never passes |
| Archive integrity | `MANIFEST.sha256`, claim `archive-integrity` | every archived input is hashed; CI checks the manifest is current |
| Environment | `requirements*.txt`, CI matrix py3.9 + py3.12 | deterministic tier: Python ≥ 3.9, NumPy ≥ 2.0, nothing else |
| Data | `artifacts/codetables_snapshots/<date>/` | dated table snapshots; no date compiled in; add a directory to extend |
| Witnesses | `artifacts/witnesses/q{2,3,4,5}/` | generators only; every derived quantity is recomputed |
| Families | `scripts/families/` | closed forms instantiated and verified in pure Python at q = 2, 3, 4, 5 |
| Nonexistence | `artifacts/refutations/registry.json` | CNF + DRAT where certified; solver decisions listed as decisions |
| Second implementation | `scripts/verify_eaqecc.magma`, `artifacts/magma/` | re-run if Magma is present, else the archived log is reported as a log |
| Randomness | `EVAL_RNG_SEED`, `MAX_EVALS` | seed + evaluation budget fix the search output; wall clock never enters |
| Search replay | claim `search-determinism`, `scripts/eaqecc_baselines/search_fingerprint.json` | 3 programs × 4 seeds, proposal lists compared bit for bit |
| Compute | paper App. B; `artifacts/campaigns/*.log` | 401 candidates × 240 s ≈ 26.7 h evaluator time across four campaigns |
| Ablation data | `artifacts/ablation/{residual,original,pinned}/` | every round of every arm, `rounds.jsonl` + closures |
| Prompts | paper App. B.3; `scripts/alphaevolve_eaqecc/run_evolution.py` | the campaign-3 task text is the one in the script; campaign-1 text in the paper |
| Negative controls | `tests/test_auditor_negative_controls.py` | the auditor is shown to FAIL on a damaged archive |
| Not reproducible | the evolutionary run itself | LLM sampling is nondeterministic; we replay programs, not their discovery |

## Refreshing the archive

Any legitimate change to `artifacts/` (a new snapshot, a new certificate)
must be followed by `python3 scripts/make_manifest.py`, and both committed
together; otherwise `archive-integrity` fails, by design.

## Regenerating certificates

`python3 scripts/refutations/run_registry.py` rebuilds the CNF for every
registry entry that lacks a proof and asks CaDiCaL for a DRAT certificate.
Proof files are large (megabytes for the k = 1 floor cells); they are kept
because a proof a reader can replay is the whole point of shipping them.

## Two numbers that look inconsistent and are not

`artifacts/tables/bound_map.json` reports `stats.plotkin = 396` while the
paper and the `table-correction` claim say 398. The bound map classifies
each cell once; two of the 398 Plotkin-corrected cells are also cells where
we constructed or refuted a code, and they are counted under that class
instead. The correction list itself has 398 entries.

The q=3 witness `[[8,1,7;5]]_3` is listed in the qutrit table already
(`dl = du = 7`): it re-derives a known value and is kept as a witness of the
closed-form cell, not claimed as new. The `openness` claim reports this.
