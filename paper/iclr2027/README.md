# Researcher-in-the-loop Evolutionary Discovery of entanglement-assisted quantum code families

`paper/main.tex` and `paper/main.pdf` contain the current manuscript: nine main
pages (24 pages including statements, references and appendices), with the latest shared-guidance ablation in Section 5 and its complete
protocol in Appendix C. AI use, Ethics and Reproducibility statements flow directly after the conclusion
and are excluded from the main-text limit. References begin on page 11. Earlier ablation inputs and figures are not included.
The publication snapshot preserves all mathematical results and historical
program provenance used elsewhere in the paper.

From this directory, build with:

```bash
cd paper
tectonic -X compile main.tex
```

The exact transitive TeX inputs, bibliography, local style files and referenced
images are included. The two latest-study figure assets also include SVG/PNG
versions. From the repository root, regenerate them with:

```bash
python3 scripts/eaqecc_ablation/make_replication_figure.py
```

Figure 4 shows the new eight-block cohort with initial-program, classical-control, independent-proposal and
iterative-evolution success curves in the same LaTeX Times family as Figures 1 and 2. Figure 5 in Appendix C shows the longer-code part of the separate 32-seed repeat; shorter-length outcomes remain in the body and block table.
The n=13,15 results and complete preserved-lineage comparison are reported in
the body and appendix.
Regenerating Figure 4 requires Tectonic and Poppler and writes TikZ source plus
standalone PDF/SVG/PNG. The main manuscript includes the TikZ directly.

Algorithm 1 in Section 4 summarizes `rank05_1001000.py`. Figure 2 compares
its progress-dependent target selection, reuse of stored proposals and added
whole-generator rotation with the construction-campaign seed. Shading identifies
these principal source-level changes. Appendix B.1 defines the remaining routines,
including their rank checks and early-exit behavior. Algorithm 2 in the preserved-program appendix
contains the separate controlled-study dual-space program, `b02_evolution_g02`,
with its existing immediate-parent comparison.

Appendix B.3 presents researcher proposals and task specifications as selectable
Times text with pale shading; matching SVG/PDF/PNG exports are in `task_specs/`.
Appendix C uses natural vertical spacing, keeps the block table with the outcome discussion
and places Algorithm 2 above the intact longer-code result paragraph. Regenerate
the task-specification layouts from the repository root with
`python3 scripts/make_task_spec_panels.py`.

Appendix D focuses on Theorem 1: exact goal, final proof body, certificate scope
and the verified coefficient map and certificate properties. Operational
verification logs and CLI compatibility patches are documented in the repository. The original Lean project is in
`formal/eaqecc/` at the repository root; Lemma 2 remains supporting codebase evidence.

The abstract and Contributions describe the researcher-in-the-loop pipeline,
general constructions and measured contribution of iterative evolution. Section 3
and the Figure 1 caption use “The researcher-in-the-loop discovery pipeline”.
Section 3.3 combines independent verification and nonexistence checking; Section
3.4 presents reproducibility in one paragraph. Results begins at the top of page 5.
The AI use statement retains substantive research/proof assistance and author
responsibility while grouping editorial and artifact preparation into one sentence.

Appendix B.2 includes resource measurements for all ten checked SAT refutations,
including the regenerated proof for `[[10,1,9;5]]₂`. The abstract and Theorem 1
state the field-size and length conditions explicitly. General entanglement costs
count maximally entangled qudit pairs; the Background distinguishes ebit units.

The original four-block comparison and the fixed-program follow-up are reported
separately. The short-length success-rate reversal is explicit, while the
abstract and contributions focus on verified longer-code performance of the
original validation-selected program. The earlier 3/4 results remain identified
as the original cohort. Updated source data are in `experiments/hitl_followup/`.

Regenerate the fresh-seed figure with `python3 scripts/eaqecc_ablation/make_followup_figure.py`.

Section 3.2 distinguishes the in-program parameter oracle from the controller's
program-level reward; Section 3.4 identifies the outputs covered by reproduction.
Appendix B.1 describes complementary q=4,5 finite-field searches. Their source
and provenance audit are in `artifacts/construction_provenance/nonbinary/`.
The binary scope of the EA-Plotkin correction and the two distinct qutrit
propagation paths are explicit in Appendix A.

Appendix D.1 defines the coefficient-function space using set notation and
identifies it with a q-dimensional vector space. Figure 6 groups the
algebraic certificate dependencies. Dashed edges identify the standard stabilizer
interpretation. The verified Lean source and exact goal remain unchanged.
Lemma 1 states the known entanglement propagation rule with a proof sketch.
Theorem and Lemma have separate counters, preserving Theorem 1 and coordinate
normalization Lemma 2 and their original Lean artifact names.
