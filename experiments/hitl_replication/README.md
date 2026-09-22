# Prospective eight-block generation replication

This is a new cohort of eight paired generation blocks. It is analyzed separately from the original four-block study and its frozen-program repeat. The model, shared researcher proposal, evaluator budgets and validation selection are preserved. Seven proposal slots per arm and block were fixed before generation. There are 111 received programs and one unavailable response, retained under the recorded rule rather than replaced.

## Results

| Length | Independent | Iterative | Initial | Classical L-side |
|---:|---:|---:|---:|---:|
| 9 | 154/256 | 186/256 | 1/32 | 22/32 |
| 11 | 69/256 | 111/256 | 0/32 | 7/32 |
| 13 | 50/256 | 118/256 | 0/32 | 5/32 |
| 15 | 8/256 | 81/256 | 0/32 | 0/32 |

Policies have eight validation-selected programs and 32 executions per program/length. Each fixed control has 32 executions per length. The controls were replayed after policy outcomes became available, using their unchanged pre-existing sources; they were not tuned or selected on these outcomes. Budgets are 10,000 evaluations at n=9,11 and 30,000 at n=13,15.

The prespecified primary endpoint is the paired block difference in normalized test success-curve area. Mean area is 0.2600 for independent proposals and 0.3587 for iterative evolution, difference **+0.0987**, positive in **5/8** blocks. A descriptive two-sided sign-flip calculation gives **p=0.3281**. Restricting to the seven completely received blocks gives +0.1504. Longer-length results are secondary. These are eight paired generation observations, not hundreds of independent program-generation trials.

## Offline verification and replay

From the repository root:

```sh
python scripts/eaqecc_ablation/audit_replication.py
python scripts/eaqecc_ablation/replay.py --bundle experiments/hitl_replication --program b04_evolution_g05 --split transfer --out ../checks/new-cohort-replay
python scripts/eaqecc_ablation/make_replication_figure.py
```

The audit checks every received prompt and parent relationship, reconstructs validation selection, checks quotas and independently recomputes saved code parameters. Replay uses the preserved macOS sandbox runtime and requires its dependencies; it does not contact a model service. See docs/REVIEWER_GUIDE.md and requirements-ablation.txt. `study.py` is the preserved controller source, not a configured public cloud execution entry point. Original model sampling is documented through requests and responses; new sampling is not guaranteed to reproduce those responses.

[Selection](selected_programs.json) · [Block results](replication_analysis.json) · [Audit](AUDIT.json) · [Source review](SOURCE_REVIEW.md) · [Missing-response rule](missing_response_amendment.json)

## Export scope

Scientific sources and measurements are preserved. JSON paths are made relative; private cloud execution identity, credentials and spending authorization are omitted. `protocol.json` records the original protocol digest and input hashes alongside the exported input hashes. Five feasibility-check records change only their path field. `MANIFEST.sha256.json` hashes the public export. All generated sources and runtime code retain their original bytes. A new output directory is required when replaying; frozen records are not overwritten.
