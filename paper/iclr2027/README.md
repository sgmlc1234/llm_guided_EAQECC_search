# From LLM-Guided Program Evolution to General Constructions of EAQECCs

`paper/main.tex` and `paper/main.pdf` contain the current manuscript: nine main
pages (22 pages including statements, references and appendices), with the latest shared-guidance ablation in Section 5 and its complete
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
python3 scripts/eaqecc_ablation/make_figure.py
```

Figure 4 shows the initial-program, independent-proposal and iterative-evolution
success curves in the same LaTeX Times family as Figures 1 and 2. The n=13,15
transfer results remain in the body and appendix; no transfer panel is included.
Regenerating Figure 4 requires Tectonic and Poppler and writes TikZ source plus
standalone PDF/SVG/PNG. The main manuscript includes the TikZ directly.

Algorithm 1 in Section 4 summarizes `rank05_1001000.py`. Figure 2 compares
its progress-dependent target selection, reuse of stored proposals and added
whole-generator rotation with the construction-campaign seed. Shading identifies
these principal source-level changes. Appendix B.1 defines the remaining routines,
including their rank checks and early-exit behavior. Algorithm 2 in Appendix C.4
contains the separate controlled-study dual-space program, `b02_evolution_g02`,
with its existing immediate-parent comparison.

Appendix B.3 presents researcher proposals and task specifications as selectable
Times text with pale shading; matching SVG/PDF/PNG exports are in `task_specs/`.
Appendix C uses natural vertical spacing, keeps Table 3 with the outcome discussion
and places Algorithm 2 above the intact longer-code result paragraph. Regenerate
the task-specification layouts from the repository root with
`python3 scripts/make_task_spec_panels.py`.

Appendix D focuses on Theorem 1: exact goal, final proof body, certificate scope
and separate kernel/Comparator records. The original Lean project is in
`formal/eaqecc/` at the repository root; Lemma 2 remains supporting codebase evidence.

The abstract and Contributions describe the researcher-in-the-loop pipeline,
general constructions and measured contribution of iterative evolution. Section 3
and the Figure 1 caption use “The researcher-in-the-loop discovery pipeline”.
Section 3.3 combines independent verification and nonexistence checking; Section
3.4 presents reproducibility in one paragraph. Results begins at the top of page 5.
The AI use statement retains substantive research/proof assistance and author
responsibility while grouping editorial and artifact preparation into one sentence.
