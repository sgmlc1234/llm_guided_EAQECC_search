"""Render the longer-code portion of the frozen-program repeat in the paper's Times font."""
import argparse
import shutil
import subprocess
from common import ROOT, read
from make_figure import step_coordinates


def render(all_lengths=False):
    bundle=ROOT/'experiments/hitl_followup';out=ROOT/'paper/iclr2027/figures'
    rows=read(bundle/'results.json');protocol=read(bundle/'protocol.json')
    assert read(bundle/'status.json')['state']=='COMPLETED' and len(rows)==1560
    stem='hitl_followup_all_lengths' if all_lengths else 'hitl_followup'
    panels=[(9,0,4.3,'a'),(11,7.2,4.3,'b'),(13,0,0,'c'),(15,7.2,0,'d')] if all_lengths else [(13,0,0,'a'),(15,7.2,0,'b')]
    lines=[r'\definecolor{hfinitial}{HTML}{A37545}',r'\definecolor{hfind}{HTML}{78818E}',r'\definecolor{hfevo}{HTML}{00858B}',r'\definecolor{hfcontrol}{HTML}{B55D32}',r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize]',fr'\path[use as bounding box] (-1,-1.70) rectangle (13.3,{7.7 if all_lengths else 3.7});']
    W,H=5.65,2.8
    for n,x,y,label in panels:
        budget=10000 if n<13 else 30000
        lines += [fr'\begin{{scope}}[xshift={x}cm,yshift={y}cm]',fr'\node[font=\scriptsize\bfseries] at (2.825,3.2) {{({label}) $n={n},\ d={n-1}$}};']
        for pc in [0,25,50,75,100]:
            height=H*pc/100;lines += [fr'\draw[black!12,line width=.35pt] (0,{height})--({W},{height});',fr'\node[anchor=east] at (-.12,{height}) {{{pc}}};']
        lines += [fr'\draw[black!40] (0,{H})--(0,0)--({W},0);',r'\node[rotate=90] at (-.72,1.4) {Success rate (\%)};',r'\node at (2.825,-.60) {Exact evaluations};']
        ticks=[0,5000,10000] if n<13 else [0,10000,20000,30000]
        for call in ticks:lines.append(fr'\node[anchor=north] at ({W*call/budget},-.10) {{{"0" if call==0 else str(call//1000)+"k"}}};')
        for arm,color,dash in [('independent','hfind',''),('evolution','hfevo',''),('classical_dual','hfcontrol',',dash pattern=on 4pt off 1.5pt'),('initial','hfinitial',',dash pattern=on 3pt off 2pt')]:
            cases=[r for r in rows if r['phase']=='fresh' and r['n']==n and protocol['programs'][r['program']]['arm']==arm]
            assert len(cases)==(128 if arm in ['independent','evolution'] else 32)
            lines.append(fr'\draw[{color},line width=1.0pt{dash}] '+step_coordinates(cases,budget,W,H)+';')
        lines.append(r'\end{scope}')
    for x,y,text,color,dash in [(1,-1.1,'Initial program','hfinitial',True),(7.1,-1.1,'Classical L-side control','hfcontrol',True),(1,-1.53,'Independent proposals','hfind',False),(7.1,-1.53,'Iterative evolution','hfevo',False)]:
        style=',dash pattern=on 3pt off 2pt' if dash else ''
        lines += [fr'\draw[{color},line width=1pt{style}] ({x},{y})--({x+.55},{y});',fr'\node[anchor=west] at ({x+.65},{y}) {{{text}}};']
    lines.append(r'\end{tikzpicture}')
    (out/f'{stem}_content.tex').write_text('\n'.join(lines)+'\n')
    (out/f'{stem}_standalone.tex').write_text(r'''\documentclass[border=1pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{times,amsmath,amssymb,tikz,xcolor}
\begin{document}
\input{hitl_followup_content}
\end{document}
'''.replace('hitl_followup_content',stem+'_content'))
    subprocess.run(['tectonic','-X','compile',f'{stem}_standalone.tex'],cwd=out,check=True,capture_output=True)
    shutil.move(out/f'{stem}_standalone.pdf',out/f'{stem}.pdf')
    subprocess.run(['pdftoppm','-singlefile','-scale-to','1900','-png',str(out/f'{stem}.pdf'),str(out/stem)],check=True)
    subprocess.run(['pdftocairo','-svg',str(out/f'{stem}.pdf'),str(out/f'{stem}.svg')],check=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-lengths',action='store_true',help='Export the complete four-panel record separately.')
    render(parser.parse_args().all_lengths)
