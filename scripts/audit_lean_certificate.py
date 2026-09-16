"""Check preserved Lean sources, exact goal text and Comparator configuration.

This is an offline integrity check, not a Lean kernel or Comparator execution.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'formal/eaqecc'
MODULES = Path('CodingTheoryLib/Research/ICLR2027EAQECC')
AXIOMS = {'propext', 'Quot.sound', 'Classical.choice'}


def audit(root=ROOT):
    root = Path(root)
    count = 0
    for line in (root / 'SOURCE_MANIFEST.sha256').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Lean source missing or changed: {name}')
        count += 1
    base = root / MODULES
    for name, other in [('Theorem1', 'Lemma2'), ('Lemma2', 'Theorem1')]:
        config = json.loads((base / f'Comparator/{name}.json').read_text())
        if set(config['permitted_axioms']) != AXIOMS or config['enable_nanoda']:
            raise ValueError(f'Unexpected Comparator configuration: {name}')
        challenge = (base / f'Comparator/{name}Challenge.lean').read_text()
        solution = (base / f'Comparator/{name}Solution.lean').read_text()
        def goal(text):
            return text[text.index('theorem '):text.index(':= by')].strip()
        if goal(challenge) != goal(solution):
            raise ValueError(f'Challenge and solution goal differ: {name}')
        proof = (base / f'{name}.lean').read_text()
        if any(other in line for line in proof.splitlines() if line.startswith('import ')):
            raise ValueError(f'Unexpected cross-import: {name}')
    return {'status': 'PASS', 'source_files': count,
            'exact_goal_pairs': 2, 'proof_modules_independent': True,
            'kernel_execution': 'NOT_RUN', 'comparator_execution': 'NOT_RUN'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(audit(args.root), indent=2))


if __name__ == '__main__':
    main()
