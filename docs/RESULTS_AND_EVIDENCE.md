# Paper results and their evidence

All paths below are relative to the repository root. Each computation can be run
without regenerating the model proposals. See [the reviewer guide](REVIEWER_GUIDE.md)
for installation, output locations and external-tool requirements.

| Paper item | Evidence | Verification or reproduction |
|---|---|---|
| Tables 1 and 2: 18 displayed codes | `artifacts/witnesses/q{2,3,4,5}/`; n=15 and additional n=13 reconstructions in `experiments/hitl_ablation/transfer/` | `python scripts/paper_results.py` emits row-to-witness paths and checks the 13 historical intervals; run both mathematical and ablation audits for exact distances |
| Prior intervals and dates | `artifacts/codetables_snapshots/2026-07-17/`; manuscript Appendix A.4 and `refs.bib` | `paper_results.py`; `--claim openness`; sources and propagation rules are stated in Appendix A.4 |
| Theorem 1 and 54 gap closures | `scripts/families/`; paper proof; `artifacts/tables/bound_map.json` | `--claim families`; computation checks finite instances and snapshot counts, not the proof for every length |
| 398 EA-Plotkin corrections | `artifacts/tables/plotkin_corrections.json` | `--claim table-correction`; the exclusive Figure 3 plot class has 396 cells because two are classified by other evidence |
| Optimality and 10 exclusions | `artifacts/refutations/registry.json` and each referenced CNF/proof | `--claim refutations`; one proof is generated on demand; qutrit completeness uses the normalization lemma |
| Solver-refined distances 9 and 11 | `artifacts/solver_refinement/claims.json` | `--claim solver-refinement` plus fresh `--claim refutations` |
| Magma 148/148 | `artifacts/magma/eaqecc_data.m`, `magma_verification.log`, `magma_version.txt` | `--claim magma-crosscheck`; the 115 core objects plus 33 family instances |
| Figure 1: pipeline | `scripts/make_pipeline_overview.py`; `assets/logos/`; `paper/iclr2027/paper/fig_overview_content.tex` | regenerate with the command in `docs/paper_figures.md` |
| Figure 2: historical program development | `paper/iclr2027/paper/fig_program.tex`; campaign prompts and `artifacts/campaigns/run9_top_programs/` | `--claim prompt-provenance` and historical search replay; schematic lineage is distinct from the current controlled ablation |
| Figure 3: construction and exclusion map | `artifacts/tables/bound_map.json`; `paper/iclr2027/paper/fig_boundmap.tex` | `scripts/build_bound_map.py`; `scripts/make_bound_map_figure.py`; see figure instructions |
| Algorithm 1 | `experiments/hitl_ablation/candidates/b02_evolution_g02/program.py` and `parentage.json`; parent `b02_evolution_g01` | `scripts/eaqecc_ablation/audit.py`; `replay.py --program b02_evolution_g02`; shading marks edits, not separately established causal effects |
| Figure 4 and Section 5.1 | `balanced_prefix_protocol.json`, `selected_programs.json`, `heldout_results.json`, `test/` under the study bundle | ablation audit and replay: independent 21/64, iterative 38/64; normalized curve area 0.2391 vs 0.3579; four generation blocks |
| Section 5.2 and Table 1 daggers | study `transfer/` and its witness files | replay split `transfer`: selected program 3/4 at each length; all-policy totals 0/32 vs 6/32 |
| Evaluation budgets, interruptions, model costs | study `protocol.json`, `budget_ledger.json`, `transport_stop.json`, amendments, all `candidates/` requests/responses | ablation audit validates the 56-proposal balanced prefix, 60 attempts and 58 received sources; excluded proposals and failures are retained |
| Historical fixed-program replay | `scripts/eaqecc_baselines/search_fingerprint.json`; `artifacts/campaigns/run9_top_programs/` | `--claim search-determinism`: three programs, four seeds |
| Two snapshot comparison | `artifacts/paper_reference.json`, snapshots dated 2026-07-17 and 2026-09-10 | `--claim novelty-drift`; matching bounds do not establish independent authorship |

The entire latest study is retained, including unsuccessful and excluded runs.
Earlier exploratory datasets and internal manuscript-editing notes are outside the
release. They motivated the final follow-up; the final study is not represented as
the first experiment. See [the archival boundary](EXPERIMENT_ARCHIVING.md).
