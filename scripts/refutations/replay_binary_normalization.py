#!/usr/bin/env python3
"""Check Lemma-2 normalization separately from the preserved binary certificates."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time

from sat_normal_form_q2 import H, build, write_cnf

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [(6, 1), (7, 3), (8, 3), (9, 5), (10, 5), (11, 7), (13, 8)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--solver', required=True)
    ap.add_argument('--checker', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + 600
    result = {'state': 'RUNNING', 'wall_limit_s': 600,
              'output_limit_bytes': 1_000_000_000,
              'per_file_limit_bytes': 100_000_000,
              'solver_sha256': digest(Path(args.solver)),
              'checker_sha256': digest(Path(args.checker)),
              'builder_sha256': digest(Path(__file__).with_name('sat_normal_form_q2.py')),
              'cases': []}

    def save():
        (args.out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')

    def limit():
        resource.setrlimit(resource.RLIMIT_FSIZE, (100_000_000, 100_000_000))

    def run(command, log):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {'status': 'GLOBAL_TIMEOUT'}
        t0 = time.monotonic()
        try:
            proc = subprocess.run(command, capture_output=True, text=True,
                                  timeout=min(45, remaining), preexec_fn=limit)
            log.write_text(proc.stdout + proc.stderr)
            return {'returncode': proc.returncode,
                    'seconds': time.monotonic() - t0}
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b'') + (exc.stderr or b'')
            log.write_bytes(output)
            return {'status': 'TIMEOUT', 'seconds': time.monotonic() - t0}

    for n, c in TARGETS + [(6, 2)]:
        positive = (n, c) == (6, 2)
        j = n - 1 - c
        assert j > 2
        tag = f'q2_n{n}_k1_c{c}_d{n-1}'
        b, basis = build(n, 1, c, n - 1)
        original = args.out / (tag + '.base.cnf')
        write_cnf(b, original)
        base_hash = digest(original)
        if not positive:
            assert base_hash == digest(ROOT / 'artifacts/refutations' / (tag + '.cnf'))
        units = [-basis[row][2*i] for row in range(j) for i in range(n)
                 if [-basis[row][2*i]] not in b.clauses]
        before = len(b.clauses)
        b.clauses.extend([[lit] for lit in units])
        cnf = args.out / (tag + '.cnf')
        write_cnf(b, cnf)
        original.unlink()  # Temporary regenerated copy only; preserved originals are untouched.
        proof = args.out / (tag + '.drat')
        command = [args.solver, str(cnf)] + ([] if positive else [str(proof)])
        decision = run(command, args.out / (tag + '.solver.log'))
        record = {'n': n, 'k': 1, 'c': c, 'd': n-1, 'j': j,
                  'positive_control': positive, 'base_sha256': base_hash,
                  'normalized_sha256': digest(cnf), 'variables': b.counter,
                  'base_clauses': before, 'unit_literals': units,
                  'normalized_clauses': len(b.clauses), 'decision': decision}
        if decision.get('returncode') == 20 and not positive:
            check_log = args.out / (tag + '.checker.log')
            record['check'] = run([args.checker, str(cnf), str(proof)], check_log)
            record['verified'] = (record['check'].get('returncode') == 0
                                  and 's VERIFIED' in check_log.read_text())
            record['proof_bytes'] = proof.stat().st_size
            record['proof_sha256'] = digest(proof)
        elif decision.get('returncode') == 10 and positive:
            model = set()
            for line in (args.out / (tag + '.solver.log')).read_text().splitlines():
                if line.startswith('v '):
                    model.update(int(x) for x in line[2:].split() if x != '0')
            logical = [sum(1 << i for i, lit in enumerate(row) if lit in model)
                       for row in basis]
            generators = H.nullspace([H._J(v, n) for v in logical], 2*n)
            parameters = H.evaluate(n, generators, n-1)
            record.update(L_basis=logical, generators=generators, parameters=parameters)
            record['verified'] = (parameters.get('k') == 1 and parameters.get('c') == c
                                  and parameters.get('d', 0) >= n-1
                                  and parameters.get('offending') == 0)
        else:
            record['verified'] = False
        result['cases'].append(record)
        save()
        print(tag, decision, 'verified', record['verified'], flush=True)
        if sum(p.stat().st_size for p in args.out.iterdir()) >= 1_000_000_000:
            result['state'] = 'OUTPUT_LIMIT'
            break
    if result['state'] == 'RUNNING':
        result['state'] = 'PASS' if len(result['cases']) == 8 and all(
            x['verified'] for x in result['cases']) else 'INCOMPLETE'
    result['elapsed_s'] = time.monotonic() - started
    save()


if __name__ == '__main__':
    main()
