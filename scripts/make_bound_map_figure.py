#!/usr/bin/env python3
"""Emit the (n,c) feasibility map of the published artifact as a TikZ figure.

Reads artifacts/tables/bound_map.json, written by scripts/build_bound_map.py,
so the figure cannot drift from the data.  One panel per local dimension, rows
are lengths n, columns are ebits c, all at k=1 and distance d=n-1.

Cell classes:
  thm    closed-form family, c = n-q-1
  deep   construction at c < n-q-1; not a minimum-entanglement claim
  lift   construction at c > n-q-1; direct witnesses or ebit lifting
  ref    complete refutation: no code of distance n-1 exists here
  wall   search found nothing (q=4,5) — the frontier, not a proof
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--target", default="iclr", choices=["iclr", "pra", "both"],
                help="which layout to emit (default iclr)")
ap.add_argument("--data", default=str(ROOT / "artifacts" / "tables" / "bound_map.json"))
ap.add_argument("--out-dir", default=str(ROOT / "figures"),
                help="directory for fig_boundmap_<target>.tex")
ARGS = ap.parse_args()
D = json.loads(Path(ARGS.data).read_text())
REFUTATIONS = json.loads((ROOT / "artifacts/refutations/registry.json").read_text())

NLO, NHI = 5, 16          # rows shown
CHI = 15                  # columns shown, c = 0..CHI

# ---------------------------------------------------------------- collect
# grid[(q,n,c)] = class
grid = {}


def put(q, n, c, kind, rank):
    """Higher rank wins, so a refutation is never overwritten by a lift."""
    key = (q, n, c)
    if key not in grid or rank > grid[key][1]:
        grid[key] = (kind, rank)


RANK = {"lift": 1, "wall": 2, "deep": 3, "thm": 4, "ref": 5}


def pos(q, n, c):
    """Class of a constructed cell by its position relative to c=n-q-1.
    The class records position relative to the line, not an exclusive
    provenance method. Above-line cells can have direct witnesses or lifting."""
    d = n - q - 1
    return "thm" if c == d else ("deep" if c < d else "lift")


# q = 2, 3 come from the codetables cross-reference
for cell in D["cells"]:
    q, n, k, c = cell["q"], cell["n"], cell["k"], cell["c"]
    if k != 1 or not (NLO <= n <= NHI) or c > CHI:
        continue
    lo, up = cell["lower"], cell["upper"]
    if up and up["d"] == n - 1:
        put(q, n, c, "ref", RANK["ref"])
    if lo and lo["d"] == n - 1:
        k2 = pos(q, n, c)
        put(q, n, c, k2, RANK[k2])

# q = 4, 5 have no table; the builder already classified every cell
for e in D["q45"]:
    q, n, c = e["q"], e["n"], e["c"]
    if not (NLO <= n <= NHI) or c > CHI:
        continue
    k = "wall" if e["kind"] == "wall" else pos(q, n, c)
    put(q, n, c, k, RANK[k])

# ebit lifting: a construction at c gives one at every larger c (Lemma:
# ebit lifting applies while c <= n-k-1 = n-2, so the whole row is covered),
# and a refutation at c rules out every smaller c by contraposition.
for q in (2, 3, 4, 5):
    for n in range(NLO, NHI + 1):
        built = [c for c in range(CHI + 1)
                 if grid.get((q, n, c), ("", 0))[0] in ("thm", "deep")]
        if built:
            for c in range(min(built), min(n - 1, CHI) + 1):
                put(q, n, c, "lift", RANK["lift"])
        refs = [c for c in range(CHI + 1)
                if grid.get((q, n, c), ("", 0))[0] == "ref"]
        if refs:
            for c in range(0, max(refs) + 1):
                put(q, n, c, "ref", RANK["ref"])


# ---------------------------------------------------------------- emit
# Two targets share one grid: the PRA figure* and the ICLR single-column
# figure, which relabels the same classes in the pipeline's own vocabulary.
FILL = {"thm": "achieve", "deep": "achieve", "lift": "achieve",
        "ref": "refute", "wall": "refute"}
OPACITY = {"thm": "1", "deep": "1", "lift": "0.22", "ref": "0.55",
           "wall": "0.0"}

# The two targets want opposite shapes. PRA figures span both columns, so
# a flat strip of four panels fits the page width and costs only a band of
# height. The ICLR figure is single-column, where a strip would shrink the
# cells past legibility, so it gets the 2x2 block.
PANEL_GRID = {2: (0, 0), 3: (1, 0), 4: (0, 1), 5: (1, 1)}
PANEL_ROW = {2: (0, 0), 3: (1, 0), 4: (2, 0), 5: (3, 0)}
# per target: panels, x-pitch, y-pitch, cell size, legend columns.
LAYOUT = {"pra":  (PANEL_ROW,  18.4, 0.0, "2.02mm", 3),
          "iclr": (PANEL_GRID, 20.5, -16.0, "3.05mm", 3)}

LEGEND = {
    "pra": [
        ("thm", r"closed-form family, $c=n-q-1$"),
        ("deep", r"deepest verified codes, $c=n-q-2$"),
        ("lift", r"implied by ebit lifting"),
        ("ref", r"refuted: no code of distance $n-1$"),
        ("wall", r"search wall --- \emph{not} a proof"),
        ("bdh", r"BDH diagonal $c=n-3$"),
    ],
    "iclr": [
        ("thm", r"Code exists: $c=n-q-1$"),
        ("deep", r"Code exists: $c<n-q-1$"),
        ("lift", r"Code exists: $c>n-q-1$"),
        ("ref", r"Nonexistence certified, including implications at smaller $c$"),
        ("wall", r"No code found; nonexistence unproved"),
        ("bdh", r"Reference $c=n-3$; not a general bound"),
    ],
}

SWATCH = {
    "thm": (r"\fill[achieve] (0,0) rectangle (0.9,0.9); "
            r"\draw[white,line width=0.35pt] (0.3,0.45)--(0.6,0.45);"),
    "deep": r"\fill[achieve] (0,0) rectangle (0.9,0.9);",
    "lift": r"\fill[achieve,opacity=0.22] (0,0) rectangle (0.9,0.9);",
    "ref": r"\fill[refute,opacity=0.55] (0,0) rectangle (0.9,0.9);",
    "wall": (r"\draw[refute,line width=0.45pt,densely dotted] "
             r"(0.05,0.05) rectangle (0.85,0.85);"),
    "bdh": r"\draw[bdh,line width=0.7pt,densely dashed] (0,0.45)--(0.9,0.45);",
}

CAPTION = {
    "pra": r"""\caption{Provenance map of the entanglement floor at $k=1$,
  $d=n-1$: rows are lengths $n$, columns ebits $c$. No table of best-known
  codes is published at $q=4,5$, so every filled cell there is new. The key
  is below the panels and Sec.~\ref{sec:tables} reads the map.}""",
    "iclr": r"""\caption{Linear stabilizer EAQECCs at $k=1$, target distance $n-1$.}""",
}


def emit(target):
    panels, DX, DY, unit, legend_cols = LAYOUT[target]
    L = []
    A = L.append
    A("% GENERATED by scripts/make_bound_map_figure.py "
      "from artifacts/tables/bound_map.json")
    A("% — do not edit; re-run the script instead.")
    if target == "pra":
        A(r"\begin{figure*}[!t]")
        A(r"\centering")
    else:
        A(r"\begin{figure}[!ht]")
        A(r"\centering")
        A(r"\resizebox{0.80\linewidth}{!}{%")
        # Center the panels and legend independently. A shared TikZ
        # bounding box lets the wide legend displace the panel grid.

    A(f"\\begin{{tikzpicture}}[x={unit}, y={unit}, line width=0.3pt,")
    A(r"    ax/.style={font=\tiny, inner sep=1pt, text=black!62},")
    A(r"    hd/.style={font=\small, inner sep=1pt},")
    A(r"    lg/.style={font=\scriptsize, inner sep=1pt}]")

    for q, (px, py) in panels.items():
        ox, oy = px * DX, py * DY
        A("")
        A(f"  % ---------------- q = {q}")
        A(f"  \\begin{{scope}}[shift={{({ox},{oy})}}]")
        A(f"    \\foreach \\n in {{{NLO},...,{NHI}}} {{")
        A(r"      \pgfmathtruncatemacro{\cm}{min(\n-1,%d)}" % CHI)
        A(r"      \fill[black!5] (-0.5,\n-0.5) rectangle (\cm+0.5,\n+0.5);")
        A(r"    }")
        for n in range(NLO, NHI + 1):
            for c in range(0, min(n - 1, CHI) + 1):
                kind = grid.get((q, n, c), (None, 0))[0]
                if target == "iclr" and kind == "ref" and not any(
                    e["q"] == q and e["n"] == n and e["k"] == 1
                    and e["d"] == n - 1 and e["c"] >= c for e in REFUTATIONS
                ):
                    continue  # no released direct refutation or lifting consequence

                if kind is None:
                    continue
                if kind == "wall":
                    A(f"    \\draw[refute, line width=0.45pt, densely dotted]"
                      f" ({c-0.42},{n-0.42}) rectangle ({c+0.42},{n+0.42});")
                else:
                    A(f"    \\fill[{FILL[kind]}, opacity={OPACITY[kind]}]"
                      f" ({c-0.5},{n-0.5}) rectangle ({c+0.5},{n+0.5});")
                if kind == "thm":
                    A(f"    \\draw[white, line width=0.35pt]"
                      f" ({c-0.16},{n}) -- ({c+0.16},{n});")
        seg = (f"({NLO-3-0.5},{NLO-0.5}) -- "
               f"({min(NHI-3,CHI)+0.5},{min(NHI,CHI+3)+0.5})")
        A(f"    \\draw[white, opacity=0.6, line width=1.2pt] {seg};")
        A(f"    \\draw[bdh, line width=0.8pt, densely dashed] {seg};")
        flat = target == "pra"
        for n in ((NLO, NHI) if flat else (NLO, 10, NHI)):
            A(f"    \\node[ax, anchor=east] at (-0.7,{n}) {{${n}$}};")
        if not flat:
            A(f"    \\node[ax, anchor=south, rotate=90]"
              f" at (-3.3,{(NLO+NHI)/2}) {{$n$}};")
        for c in ((0, 15) if flat else (0, 5, 10, 15)):
            A(f"    \\node[ax, anchor=north] at ({c},{NLO-0.75}) {{${c}$}};")
        if not flat:
            A(f"    \\node[ax, anchor=north] at ({CHI/2},{NLO-1.7}) {{$c$}};")
        A(f"    \\node[hd, anchor=west, inner xsep=0pt, outer sep=0pt] at (-0.5,{NHI+1.5}) {{$q={q}$}};")
        A(r"  \end{scope}")

    if target == "iclr":
        # Balance the left-side axis labels with equal empty space on
        # the right, so the four plotted blocks themselves are centered.
        A(f"\\coordinate (panel-center) at ({(DX + CHI) / 2},0);")
        A(r"\path let \p1=(current bounding box.south west),")
        A(r"          \p2=(current bounding box.north east), \p3=(panel-center)")
        A(r"      in ({2*\x3-\x1},\y2);")
        A(r"\end{tikzpicture}}\par\vspace{1.5mm}")
        # The legend is typeset at the document's footnote size, outside the
        # plot's resizebox: larger labels must not shrink the entire figure.
        A(r"\begingroup\footnotesize")
        A(r"\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.18}")
        A(r"\begin{tabularx}{\linewidth}{@{}lX@{\hspace{1em}}lX@{}}")
        entries = LEGEND[target]
        for j in range(0, len(entries), 2):
            cells=[]
            for key, label in entries[j:j+2]:
                swatch=r"\tikz[baseline=-.6ex,x=2.7mm,y=2.7mm]{"+SWATCH[key]+"}"
                cells.extend([swatch,label])
            A(" & ".join(cells)+r"\\[1pt]")
        A(r"\tikz[baseline=-.6ex]{\fill[black!5] (0,0) rectangle (2.4mm,2.4mm);} & \multicolumn{3}{l}{Unmarked gray cell: no result asserted in this figure.}")
        A(r"\end{tabularx}\endgroup")
        A(CAPTION[target])
        A(r"\label{fig:map}")
        A(r"\end{figure}")
        return "\n".join(L) + "\n"

    A("")
    A(r"  % ---------------- legend")
    # Legend sits under the last panel row. With the single-row conference
    # layout that is the first row, so keying it to DY would leave a band
    # of empty space the height of a panel.
    ly = (NLO - 4.3) if target == "pra" else 0.0
    for i, (key, txt) in enumerate(LEGEND[target]):
        col, row = i % 3, i // 3
        x, y = col * (24.0 if target == "pra" else 19.4), ly - row * 1.75
        A(f"  \\begin{{scope}}[shift={{({x},{y})}}] {SWATCH[key]} "
          f"\\end{{scope}}")
        A(f"  \\node[lg, anchor=west] at ({x+1.15},{y+0.45}) {{{txt}}};")

    A(r"\end{tikzpicture}")
    if target != "pra":
        A(r"\end{tabular}")
        A(r"}")
    A(CAPTION[target])
    A(r"\label{fig:map}")
    A(r"\end{figure*}" if target == "pra" else r"\end{figure}")
    return "\n".join(L) + "\n"


out_dir = Path(ARGS.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
for target in (["iclr", "pra"] if ARGS.target == "both" else [ARGS.target]):
    dst = out_dir / f"fig_boundmap_{target}.tex"
    dst.write_text(emit(target))
    print(f"{target}: {len(grid)} cells -> {dst}")
