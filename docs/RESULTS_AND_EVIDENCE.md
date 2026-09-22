# Paper results and their evidence

All paths below are relative to the repository root. Each computation can be run
without regenerating the model proposals. See [the reviewer guide](REVIEWER_GUIDE.md)
for installation, output locations and external-tool requirements.

| Paper item | Evidence | Verification or reproduction |
|---|---|---|
| Tables 1 and 2: 18 displayed codes | `artifacts/witnesses/q{2,3,4,5}/`; n=15 and additional n=13 reconstructions in `experiments/hitl_ablation/transfer/` | `python scripts/paper_results.py` emits row-to-code paths and checks the 13 historical intervals; run both mathematical and ablation audits for exact distances |
| Prior intervals and dates | `artifacts/codetables_snapshots/2026-07-17/`; manuscript Appendix A.4 and `refs.bib` | `paper_results.py`; `--claim openness`; sources and propagation rules are stated in Appendix A.4 |
| Discovery and generalization of the family | Early campaign code records; `artifacts/campaigns/prompts/campaign1.txt` and `campaign3.txt`; proof in Appendix A.2 | Initial instructions contain search directions, not the family formula. Later instructions explicitly record researcher generalization of the qubit constructions. The current prime-power theorem is a further mathematical extension; retained Algorithm 1 is a later program |
| Lean verification of the construction | `formal/eaqecc/`; Appendix D | Original exact goal and proof preserved; fresh macOS kernel build and Linux Comparator replay pass. Full Linux logs and a one-line CLI compatibility patch are preserved. The standard stabilizer interpretation is explained in the paper |
| Theorem 1 and 54 gap closures | `scripts/families/`; paper proof; `artifacts/tables/bound_map.json` | `--claim families`; computation checks finite instances and snapshot counts, not the proof for every length |
| 398 EA-Plotkin corrections | `artifacts/tables/plotkin_corrections.json` | `--claim table-correction`; the exclusive Figure 3 plot class has 396 cells because two are classified by other evidence |
| Optimality and 10 exclusions | `artifacts/refutations/registry.json` and each referenced CNF/proof | `--claim refutations`; one proof is generated on demand; qutrit completeness uses the normalization lemma |
| Solver-refined distances 9 and 11 | `artifacts/solver_refinement/claims.json` | `--claim solver-refinement` plus fresh `--claim refutations` |
| Magma 148/148 | `artifacts/magma/eaqecc_data.m`, `magma_verification.log`, `magma_version.txt` | `--claim magma-crosscheck`; the 115 core objects plus 33 family instances |
| Figure 1: pipeline | `scripts/make_pipeline_overview.py`; `assets/logos/`; `paper/iclr2027/paper/fig_overview_content.tex` | regenerate with the command in `docs/paper_figures.md` |
| Figure 2: program changes | `paper/iclr2027/paper/fig_program.tex`; rank05 and the campaign seed | Schematic comparison of target selection, initialization and generator-row mutation; regenerate with `scripts/make_readme_figures.py` |
| Figure 3: construction and exclusion map | `artifacts/tables/bound_map.json`; `paper/iclr2027/paper/fig_boundmap.tex` | `scripts/build_bound_map.py`; `scripts/make_bound_map_figure.py`; see figure instructions |
| Algorithm 1 and Figure 2 | `artifacts/campaigns/run9_top_programs/rank05_1001000.py`; compared with `scripts/alphaevolve_eaqecc/program.py` | Direct rank05 replay is documented in the reviewer guide; the older B2 fingerprint remains rank01 and is not relabeled as rank05 |
| Algorithm 2 (preserved-program appendix) | `experiments/hitl_ablation/candidates/b02_evolution_g02/program.py` and `parentage.json`; parent `b02_evolution_g01` | `scripts/eaqecc_ablation/audit.py`; `replay.py --program b02_evolution_g02`; shading marks edits, not separately established causal effects |
| Original test cohort (Appendix C) | `balanced_prefix_protocol.json`, `selected_programs.json`, `heldout_results.json`, `test/` under the study bundle | ablation audit and replay: independent 21/64, iterative 38/64; normalized curve area 0.2391 vs 0.3579; four generation blocks |
| Original longer-code cohort and Table 1 daggers | study `transfer/` and its code records | replay split `transfer`: selected program 3/4 at each length; all-policy totals 0/32 vs 6/32 |
| Evaluation budgets, interruptions, model costs | study `protocol.json`, `budget_ledger.json`, `transport_stop.json`, amendments, all `candidates/` requests/responses | ablation audit validates the 56-proposal balanced prefix, 60 attempts and 58 received sources; excluded proposals and failures are retained |
| Historical fixed-program replay | `scripts/eaqecc_baselines/search_fingerprint.json`; `artifacts/campaigns/run9_top_programs/` | `--claim search-determinism`: three programs, four seeds |
| Two snapshot comparison | `artifacts/paper_reference.json`, snapshots dated 2026-07-17 and 2026-09-10 | `--claim novelty-drift`; matching bounds do not establish independent authorship |

The entire latest study is retained, including unsuccessful and excluded runs.
Earlier exploratory datasets and internal manuscript-editing notes are outside the
release. They motivated the final follow-up; the final study is not represented as
the first experiment. See [the archival boundary](EXPERIMENT_ARCHIVING.md).

## Frozen-program repeat

`experiments/hitl_followup/` contains all 1,560 evaluations and 545 independently
checked successful code records. Figure 4 adds the classical-control executions
on the original seeds. Figure 5 and Appendix C report the distinct 32-seed
repeat, including its reversed short-length success ranking and improved
longer-code outcomes. The lineage table includes the first proposal, parent and
validation-selected child without reselection. Model token totals come from
the 56 original included proposal receipts, not new model calls.

## Discovery stages and nonbinary search

[Discovery and reproduction map](DISCOVERY_AND_REPRODUCTION.md) distinguishes
initial code discovery, researcher generalization, later program evolution,
fixed-program replay, and the two evaluation roles. The
[nonbinary provenance bundle](../artifacts/construction_provenance/nonbinary/README.md)
preserves the q=4,5 annealing routines and maps all 23 matrices to historical
records or fresh reconstruction evidence. Its structural audit is
`python3 scripts/audit_nonbinary_provenance.py`.

## Prospective replication and binary-normalization follow-up

Figure 4 now uses `experiments/hitl_replication/`: eight new generation blocks,
111 received programs out of 112 allocated slots, and matched-seed fixed controls.
Run `scripts/eaqecc_ablation/audit_replication.py` to check prompts, parent choices,
selection, quotas, code parameters and all paired metrics. The primary mean
curve-area gain is +0.0987 in 5/8 positive blocks (descriptive p=0.3281).
Longer-length outcomes are secondary; the original four-block results are kept
separately. Rebuild the figure with `make_replication_figure.py`.

The seven new binary normalized CNFs and independently checked DRAT proofs are
in `artifacts/refutations/binary_normalization/2026-09-22/`. They confirm the same
seven exclusions, not seven additional nonexistence results. The feasible
[[6,1,5;2]]2 control remains SAT and passes the independent matrix checker.
