# Frozen-program follow-up

This separately recorded follow-up re-executes the eight original validation selections, initial program, unchanged classical L-side control, and two ancestors of the selected block-3 iterative program. It does not generate or reselect programs.

There are 24 classical-control runs on the original test/longer-code seeds, followed by 12 programs × four lengths × 32 fresh seeds: **1,560 runs**, **545 independently verified successful code records**, and **zero process errors**. Repeated code matrices are separate execution outcomes, not additional parameter discoveries. Budgets remain 10,000 calls at n=9,11 and 30,000 at n=13,15.

[All program results](RESULTS.md) · [Integrity audit](AUDIT.json) · [Lineage interpretation](LINEAGE_INTERPRETATION.md) · [Model-token accounting](token_accounting.json)

The repeat changes the success-rate ordering at n=9,11: independent proposals achieve 96/128 and 39/128, versus 81/128 and 34/128 for iterative evolution. The corresponding mean curve areas are similar. At n=13,15, the iterative selections achieve 39/128 and 20/128, versus 17/128 and 1/128. The unchanged classical control achieves 3/32 and 0/32 at these longer lengths.

Within the preserved block-3 lineage, adding the distance-shortfall penalty improves n=13 success from 13/32 to 29/32 and n=15 from 3/32 to 28/32. The validation-selected child scores 30/32 and 20/32. The parent was not selected using these new tests, and the original selected child remains the policy-comparison entry. The lineage is a post-hoc diagnosis, not a new generation block.

## Inspect or repeat

From the repository root, check completeness and all preserved hashes:

```bash
python3 experiments/hitl_followup/audit_performance.py
python3 experiments/hitl_followup/analyze_performance.py
```

The audit checks the saved independent-verification receipts and code hashes. Re-execution additionally invokes the separate code verifier on successful outputs. Use the original Python 3.12.12 / NumPy 2.5.1 environment and the macOS sandbox backend. No model or cloud calls are made:

```bash
python3 experiments/hitl_followup/replay.py --dry-run --out ../checks/followup
python3 experiments/hitl_followup/replay.py --program classical_dual --length 13 --phase fresh --out ../checks/classical-n13
python3 experiments/hitl_followup/replay.py --out ../checks/full-followup
```

The full replay uses at most four workers and a four-hour scheduling limit. Program outputs, evaluator-call counts and generator matrices are compared to the archive; host timings may differ. Existing output directories are not overwritten.

`inputs/` preserves the exact program/runtime/target bytes and hashes. `records/` contains all full evaluations; `codes/` holds successful matrices. The exported protocol omits local authorization prose, and recorded filesystem paths are relative; `source_protocol.sha256` identifies the original frozen protocol. No scientific jobs or inputs changed during export. Per-program execution intervals describe execution randomness; pooled intervals are not uncertainty estimates for generation-policy superiority. There are still four original independent generation blocks.
