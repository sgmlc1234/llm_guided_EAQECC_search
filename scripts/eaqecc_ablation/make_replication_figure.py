"""Render the prospective generation and longer-code curves in the paper font."""
import shutil
import subprocess

from common import ROOT, read
from make_figure import step_coordinates


def render():
    bundle = ROOT / 'experiments/hitl_replication'
    out = ROOT / 'paper/iclr2027/figures'
    held = read(bundle / 'heldout_results.json')
    controls = read(bundle / 'matched_controls/results.json')
    assert read(bundle / 'matched_controls/status.json')['state'] == 'COMPLETED'
    lines = [r'\definecolor{rpinitial}{HTML}{A37545}',
             r'\definecolor{rpind}{HTML}{78818E}',
             r'\definecolor{rpcontrol}{HTML}{B55D32}',
             r'\definecolor{rpevo}{HTML}{00858B}',
             r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]',
             r'\path[use as bounding box] (-1.05,-1.72) rectangle (13.15,4.65);']
    for split, offset, panel, title, lengths, budget in [
        ('test', 0, 'a', 'Program generation', '9,11', 10000),
        ('transfer', 7.2, 'b', 'Generalization to longer codes', '13,15', 30000),
    ]:
        lines += [fr'\begin{{scope}}[xshift={offset}cm]',
                  fr'\node[font=\scriptsize\bfseries] at (2.825,4.42) {{({panel}) {title}}};',
                  fr'\node at (2.825,4.06) {{$n={lengths}$}};']
        for rate in (0, .25, .5, .75, 1):
            y = 3.65 * rate
            lines += [fr'\draw[black!12,line width=.35pt] (0,{y})--(5.65,{y});',
                      fr'\node[anchor=east] at (-.12,{y}) {{{int(100*rate)}}};']
        lines += [r'\draw[black!40,line width=.4pt] (0,3.65)--(0,0)--(5.65,0);',
                  r'\node[rotate=90] at (-.72,1.825) {Success rate (\%)};',
                  r'\node at (2.825,-.66) {Exact evaluations};']
        for fraction in (0, .5, 1):
            value = int(budget*fraction)
            label = '0' if not value else f'{value//1000}k'
            lines.append(fr'\node[anchor=north] at ({5.65*fraction},-.12) {{{label}}};')
        for arm, color, style in [
            ('independent', 'rpind', ''), ('evolution', 'rpevo', ''),
            ('classical_dual', 'rpcontrol', ',dash pattern=on 4pt off 1.5pt'),
            ('initial', 'rpinitial', ',dash pattern=on 1pt off 2pt'),
        ]:
            cases = ([c for arms in held.values() for c in arms[arm][split]['cases']]
                     if arm in ('independent', 'evolution') else controls[arm][split]['cases'])
            assert len(cases) == (512 if arm in ('independent', 'evolution') else 64)
            lines.append(fr'\draw[{color},line width=1.1pt{style}] '
                         + step_coordinates(cases, budget=budget) + ';')
            if arm in ('independent', 'evolution'):
                rate = sum(c['closed'] for c in cases)/len(cases)
                lines.append(fr'\node[anchor=south east,text={color},font=\scriptsize\bfseries] '
                             fr'at (5.58,{3.65*rate+.05:.5f}) {{{100*rate:.1f}\%}};')
        lines.append(r'\end{scope}')
    for x, y, label, color, style in [
        (1, -1.10, 'Initial program', 'rpinitial', ',dash pattern=on 1pt off 2pt'),
        (7.1, -1.10, 'Classical L-side control', 'rpcontrol', ',dash pattern=on 4pt off 1.5pt'),
        (1, -1.53, 'Independent proposals', 'rpind', ''),
        (7.1, -1.53, 'Iterative evolution', 'rpevo', ''),
    ]:
        lines += [fr'\draw[{color},line width=1pt{style}] ({x},{y})--({x+.55},{y});',
                  fr'\node[anchor=west] at ({x+.65},{y}) {{{label}}};']
    lines.append(r'\end{tikzpicture}')
    (out / 'hitl_replication_content.tex').write_text('\n'.join(lines) + '\n')
    (out / 'hitl_replication_standalone.tex').write_text(r'''\documentclass[border=1pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{times,amsmath,amssymb,tikz,xcolor}
\begin{document}
\input{hitl_replication_content}
\end{document}
''')
    subprocess.run(['tectonic', '-X', 'compile', 'hitl_replication_standalone.tex'],
                   cwd=out, check=True, capture_output=True)
    pdf = out / 'hitl_replication.pdf'
    shutil.move(out / 'hitl_replication_standalone.pdf', pdf)
    subprocess.run(['pdftoppm', '-singlefile', '-scale-to', '1900', '-png', str(pdf),
                    str(out / 'hitl_replication')], check=True)
    subprocess.run(['pdftocairo', '-svg', str(pdf), str(out / 'hitl_replication.svg')], check=True)


if __name__ == '__main__':
    render()
