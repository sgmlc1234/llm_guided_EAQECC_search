# Research-guided program development ablation

This is the only active ablation-study bundle in the submission tree. It contains
the latest study's calibration, all 60 attempted requests, 58 received responses,
model-generated sources, candidate/validation/test records, and both unavailable
response records. The balanced comparison includes the first seven completed
proposals in all four blocks and both policies (56 proposals). Its completion-only
truncation rule was frozen before any validation or test observations.

Both policies receive the same initial S-side program and explicit researcher
suggestion to maintain and mutate L throughout search. The working calibration
control and witness matrices are not supplied to the model. Independent proposals
always receive the initial source/feedback; iterative proposals receive the
best-so-far program and latest attempt with training feedback.

Training uses n=9,11, two seeds and 10,000 evaluator calls per target. Four new
validation seeds select among each pool's top three distinct programs. Eight
further seeds measure reconstruction. A separate n=13,15 transfer uses four
seeds and 30,000 calls. No controller initializer is used. The primary metric is
normalized area under the success-versus-calls curve; misses contribute zero.

From the repository root:

```bash
python3 scripts/eaqecc_ablation/audit.py
python3 scripts/eaqecc_ablation/replay.py --program b02_evolution_g02 --split transfer --out /tmp/eaqecc_replay
python3 scripts/eaqecc_ablation/make_figure.py
```

The audit needs Python and NumPy; replay also needs psutil and the original macOS
sandbox interface. Each target has the same CPU/memory limits as the study.
Replay never calls a model or charges a cloud account. Store reruns outside this
immutable bundle. Hashes, inputs and the generation requests document sampling;
they do not make fresh model sampling deterministic.

Original launch sources in provenance/ record the historical process and may refer
to machine-local budget ledgers. Use the portable audit/replay commands above.
No account configuration, credential tokens or previous-study datasets are shipped.
The prior spending total is retained solely for cumulative budget accounting.
Machine-local study paths and opaque provider metadata were sanitized; the export
index maps original and exported file hashes. Model program bytes are unchanged.

The original 96-proposal plan was interrupted by two unavailable model responses.
Do not describe the 56-proposal balanced result as a completed 96-proposal study.
All observations, including later excluded proposals and failures, are preserved.
Old study datasets are kept in a recoverable research archive outside the Git tree;
this does not alter the original Git history or make this follow-up a first attempt.
