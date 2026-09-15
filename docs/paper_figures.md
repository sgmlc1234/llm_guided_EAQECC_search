# Current paper figures

Figure 4 contains three preserved success curves at each of n=9 and n=11:
initial program, independent proposals and iterative evolution. The initial
program has eight executions per target; each policy has 32 (four selected
programs on eight seeds). Endpoints retain those denominators. The n=13,15
transfer outcomes remain in the main text and appendix, not in Figure 4.

Both Figures 1 and 4 use the same LaTeX Times family as Figure 2. Figure 4 is
data-derived TikZ loaded directly into the manuscript; it no longer uses a
Matplotlib fallback font. Figure 1 explicitly uses the roman family, preserving
its existing sizes and logo artwork.

Run `python3 scripts/eaqecc_ablation/make_figure.py` from the repository root.
It needs Tectonic and Poppler to export standalone PDF, SVG and PNG alongside
`hitl_ablation_content.tex`. The main manuscript inputs the generated TikZ.
Run `python3 scripts/make_pipeline_overview.py --out-dir paper/iclr2027/paper`
to regenerate Figure 1 with the same family. Raw study data are unchanged.

Figure 1 is placed immediately after the pipeline introduction (around review
line 124), using an in-place float. Figure 3 has an independently typeset,
footnote-size legend so enlarging the text does not shrink the panels. Its three
construction markers are defined by c relative to n-q-1, not by optimality or
exclusive provenance. Checked exclusions, unsuccessful searches, the historical
reference line and unmarked cells are defined separately. The target is distance
at least n-1. The plotted cell and axis commands are unchanged.

To regenerate the Figure 3 data and source against the paper's frozen snapshot:

```bash
python3 scripts/build_bound_map.py --out ../checks/bound_map.json
python3 scripts/make_bound_map_figure.py --data ../checks/bound_map.json --out-dir ../checks/figure3
```

The output is `fig_boundmap_iclr.tex`. Pass the positional argument `latest` to
`build_bound_map.py` only for an explicitly updated comparison, not paper replay.
Figure 2 is the historical construction lineage in `fig_program.tex`; the
controlled comparison and Algorithm 1 describe a separate preserved program.

## Figures embedded in the README

The README uses PNG previews of all four paper figures, with PDF/SVG companions
under `paper/iclr2027/figures/`. Figures 1 and 4 use their existing generators.
Run `python3 scripts/make_readme_figures.py` to export Figures 2 and 3 from the
current manuscript TeX. These exports omit the paper captions and replace the
external appendix reference with “archived prompts”; plotted content and the
complete Figure 3 legend are preserved. No experimental results are regenerated.
