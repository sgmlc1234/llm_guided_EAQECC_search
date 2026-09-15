"""Map every row of Tables 1 and 2 to an archived witness and prior interval.

This checks the manuscript-to-record links. Use the mathematical and ablation
auditors to recompute distances from the linked matrices.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def index(root):
    table = (root / 'paper/iclr2027/paper/tab_results.tex').read_text()
    pattern = (r'\[\[(\d+),(\d+),(\d+)(?:\\text\{--\}(\d+))?;(\d+)\]\]_(\d+)'
               r'\$ & \$(?:\\mathbf\{)?(\d+)')
    rows = re.findall(pattern, table)
    assert len(rows) == 18, 'unexpected manuscript table coverage'
    snapshots = {q: json.loads((root / f'artifacts/codetables_snapshots/2026-07-17/{name}.json').read_text())
                 for q, name in ((2, 'qubit'), (3, 'qutrit'))}
    witnesses = []
    for q in range(2, 6):
        for p in sorted((root / f'artifacts/witnesses/q{q}').glob('*.json')):
            t = json.loads(p.read_text())['target']
            witnesses.append((q, t, p))
    b = root / 'experiments/hitl_ablation'
    selected = json.loads((b / 'selected_programs.json').read_text())['2']['evolution']
    assert selected['program_id'] == 'b02_evolution_g02'
    for p in sorted((b / 'transfer' / selected['code_sha256']).glob('*.witness.json')):
        witnesses.append((2, json.loads(p.read_text())['target'], p))
    result = []
    for ns, ks, lows, highs, cs, qs, ds in rows:
        n, k, low, c, q, d = map(int, (ns, ks, lows, cs, qs, ds))
        matches = [p for wq, t, p in witnesses
                   if (wq, t['n'], t['k'], t['c'], t['d']) == (q, n, k, c, d)]
        assert matches, (q, n, k, c, d)
        previous = None
        if highs:
            previous = [low, int(highs)]
            snap = [r for r in snapshots[q] if (r['n'], r['k'], r['c']) == (n, k, c)]
            assert len(snap) == 1 and [snap[0]['dl'], snap[0]['du']] == previous
        else:
            assert low == d and q in (4, 5)
        result.append(dict(table=1 if q == 2 else 2, q=q, n=n, k=k, c=c, d=d,
                           previous_interval=previous,
                           witnesses=[{'path': p.relative_to(root).as_posix(),
                                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                                      for p in matches]))
    return {'status': 'PASS', 'rows': result,
            'note': 'Witness metadata and prior-interval links checked; distances are recomputed by the auditors.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    text = json.dumps(index(args.root.resolve()), indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end='')
