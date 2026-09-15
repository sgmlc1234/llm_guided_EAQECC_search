"""Render the three preserved search curves in the manuscript's Times/TikZ font."""
import argparse
import shutil
import subprocess
from pathlib import Path
from common import BUNDLE, ROOT, read, code_hash


def step_coordinates(cases, budget=10000, width=5.65, height=3.65):
    calls=sorted({c['n_evals'] for c in cases if c['closed']})
    points=[(0.0,0.0)]; previous=0.0
    for call in calls:
        success=sum(c['closed'] and c['n_evals']<=call for c in cases)/len(cases)
        x=width*call/budget
        points.extend([(x,height*previous),(x,height*success)])
        previous=success
    points.append((width,height*previous))
    return ' -- '.join(f'({x:.5f},{y:.5f})' for x,y in points)


def render(bundle, out):
    out.mkdir(parents=True,exist_ok=True)
    result=read(bundle/'heldout_results.json')
    initial=read(bundle/'test'/code_hash((bundle/'initial_program.py').read_text())/'evaluation.json')
    lines=[r'% Data-derived TikZ; the main document supplies the same font as Figure 2.',
           r'\definecolor{hcinitial}{HTML}{A37545}',r'\definecolor{hcind}{HTML}{78818E}',r'\definecolor{hcevo}{HTML}{00858B}',
           r'\begin{tikzpicture}[x=1cm,y=1cm,font=\scriptsize,baseline]',
           r'\path[use as bounding box] (-1.05,-1.32) rectangle (13.15,4.35);']
    for n,offset,panel in [(9,0,'a'),(11,7.2,'b')]:
        lines += [f'\\begin{{scope}}[xshift={offset}cm]',
                  f'\\node[font=\\scriptsize\\bfseries] at (2.825,4.14) {{({panel}) $n={n},\\ d={n-1}$}};']
        for value in (0,.25,.5,.75,1):
            y=3.65*value
            lines += [f'\\draw[black!12,line width=.35pt] (0,{y})--(5.65,{y});',
                      f'\\node[anchor=east] at (-.12,{y}) {{{int(value*100)}}};']
        lines += [r'\draw[black!40,line width=.4pt] (0,3.65)--(0,0)--(5.65,0);',
                  r'\node[rotate=90] at (-.72,1.825) {Success rate (\%)};',
                  r'\node at (2.825,-.66) {Exact evaluations};']
        for x,label in [(0,'0'),(2.825,'5k'),(5.65,'10k')]:lines.append(f'\\node[anchor=north] at ({x},-.12) {{{label}}};')
        for arm,color in [('independent','hcind'),('evolution','hcevo')]:
            cases=[c for block in result.values() for c in block[arm]['test']['cases'] if c['target']['n']==n]
            assert len(cases)==32
            hits=sum(c['closed'] for c in cases); rate=hits/len(cases)
            lines.append(f'\\draw[{color},line width=1.15pt] '+step_coordinates(cases)+';')
            dy=-.21 if n==9 and arm=='independent' else .17
            lines.append(f'\\node[anchor=east,text={color},font=\\scriptsize\\bfseries] at (5.60,{3.65*rate+dy:.5f}) {{{hits}/{len(cases)}}};')
        cases=[c for c in initial['cases'] if c['target']['n']==n]
        assert len(cases)==8 and all(c['allocated_evals']==10000 for c in cases)
        hits=sum(c['closed'] for c in cases)
        lines.append(r'\draw[hcinitial,line width=.9pt,dash pattern=on 3pt off 2pt] '+step_coordinates(cases)+';')
        lines.append(f'\\node[anchor=south east,text=hcinitial] at (5.60,{3.65*hits/len(cases)+.04:.5f}) {{{hits}/{len(cases)}}};')
        lines.append(r'\end{scope}')
    for x,label,color,dashed in [(0,'Initial program','hcinitial',True),(3.9,'Independent proposals','hcind',False),(9.0,'Iterative evolution','hcevo',False)]:
        style=',dash pattern=on 3pt off 2pt' if dashed else ''
        lines += [f'\\draw[{color},line width=1pt{style}] ({x},-1.12)--({x+.55},-1.12);',
                  f'\\node[anchor=west] at ({x+.65},-1.12) {{{label}}};']
    lines.append(r'\end{tikzpicture}')
    content=out/'hitl_ablation_content.tex';content.write_text('\n'.join(lines)+'\n')
    wrapper=out/'hitl_ablation_standalone.tex'
    wrapper.write_text(r'''\documentclass[border=1pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{times,amsmath,amssymb,tikz,xcolor}
\begin{document}
\input{hitl_ablation_content}
\end{document}
''')
    subprocess.run(['tectonic','-X','compile',wrapper.name],cwd=out,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    pdf=out/'hitl_ablation.pdf';shutil.move(out/'hitl_ablation_standalone.pdf',pdf)
    subprocess.run(['pdftoppm','-singlefile','-scale-to','1900','-png',str(pdf),str(out/'hitl_ablation')],check=True)
    subprocess.run(['pdftocairo','-svg',str(pdf),str(out/'hitl_ablation.svg')],check=True)
    # Keep the standalone curve filenames as aliases, with identical information.
    for ext in ('pdf','png','svg'):shutil.copyfile(out/f'hitl_ablation.{ext}',out/f'hitl_success_curves.{ext}')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle',type=Path,default=BUNDLE)
    ap.add_argument('--out',type=Path,default=ROOT/'paper/iclr2027/figures')
    args=ap.parse_args();render(args.bundle.resolve(),args.out.resolve())
