"""Export Figures 2 and 3 from manuscript TeX for the repository README.

The manuscript sources are unchanged. README exports omit captions and replace
the external appendix reference with 'archived prompts'. Requires Tectonic and
Poppler; no experiment or model call is performed.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/iclr2027/paper'
OUT = ROOT / 'paper/iclr2027/figures'
PREAMBLE = r'''\documentclass[border=2pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{times,amsmath,amssymb,tikz,xcolor,graphicx,tabularx}
\usetikzlibrary{calc,arrows.meta}
\definecolor{achieve}{RGB}{31,119,120}
\definecolor{refute}{RGB}{178,58,50}
\definecolor{bdh}{RGB}{110,110,118}
\newcommand{\vct}[1]{\boldsymbol{#1}}
\begin{document}
\begin{minipage}{17cm}
\centering
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, source in [('program_evolution', 'fig_program.tex'),
                         ('construction_map', 'fig_boundmap.tex')]:
        lines = (PAPER / source).read_text().splitlines()
        body = '\n'.join(line for line in lines if not line.lstrip().startswith(
            (r'\begin{figure}', r'\end{figure}', r'\caption{', r'\label{')))
        body = body.replace(r'App.~\ref{app:prompts}', 'archived prompts')
        body = body.replace(r'\ref{alg:search}', '1')
        with tempfile.TemporaryDirectory(prefix='eaqecc-readme-figure-') as temp:
            temp = Path(temp)
            (temp / 'figure.tex').write_text(PREAMBLE + body +
                                           '\n\\end{minipage}\n\\end{document}\n')
            result = subprocess.run(['tectonic', '-X', 'compile', 'figure.tex'],
                                    cwd=temp, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            pdf = OUT / f'{name}.pdf'
            shutil.copyfile(temp / 'figure.pdf', pdf)
            subprocess.run(['pdftoppm', '-singlefile', '-scale-to', '2200', '-png',
                            str(pdf), str(OUT / name)], check=True)
            subprocess.run(['pdftocairo', '-svg', str(pdf), str(OUT / f'{name}.svg')], check=True)
        print(f'{source} -> {name}.pdf/png/svg')


if __name__ == '__main__':
    main()
