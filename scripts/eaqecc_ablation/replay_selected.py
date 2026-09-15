"""Replay both policies' eight selected programs and the initial test baseline.

Uses the archived macOS sandbox backend; never contacts a model service.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from common import BUNDLE, read


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    selected = read(BUNDLE / 'selected_programs.json')
    jobs = [('initial', 'test', 'initial')]
    for arms in selected.values():
        for arm, record in arms.items():
            jobs.extend((record['program_id'], split, arm) for split in ('test', 'transfer'))
    summaries = []
    for program, split, arm in jobs:
        dest = args.out / f'{program}-{split}'
        subprocess.run([sys.executable, str(Path(__file__).with_name('replay.py')),
                        '--program', program, '--split', split, '--out', str(dest)],
                       check=True, stdout=subprocess.DEVNULL)
        summary = read(dest / 'summary.json')
        if any(x.get('error') for x in summary['records']):
            raise RuntimeError(f'execution error in {program}/{split}; inspect saved records')
        summary['arm'] = arm
        summaries.append(summary)
        print(f'{program} {split}: {summary["successes"]}/{len(summary["records"])}', flush=True)
    result = {}
    for arm in ('initial', 'independent', 'evolution'):
        result[arm] = {}
        for split in ('test', 'transfer'):
            rows = [x for s in summaries if s['arm'] == arm and s['split'] == split for x in s['records']]
            if rows:
                result[arm][split] = {'successes': sum(x['success'] for x in rows), 'executions': len(rows)}
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
