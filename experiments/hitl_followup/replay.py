"""Re-execute any frozen follow-up jobs using the preserved sandbox runtime."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parent

def read(path):return json.loads(path.read_text())
def main():
    p=read(ROOT/'protocol.json')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--program',choices=list(p['programs']))
    ap.add_argument('--length',type=int,choices=[9,11,13,15])
    ap.add_argument('--phase',choices=['all','fresh','archived_baseline'],default='all')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    jobs=[j for j in p['jobs'] if (not args.program or j['program']==args.program) and (not args.length or j['n']==args.length) and (args.phase=='all' or j['phase']==args.phase)]
    for name,expected in p['input_sha256'].items():
        assert hashlib.sha256((ROOT/'inputs'/name).read_bytes()).hexdigest()==expected,name
    if args.dry_run:
        print(json.dumps({'jobs':len(jobs),'maximum_evaluator_calls':sum(j['budget'] for j in jobs),'max_workers':4,'paid_calls':False},indent=2));return
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'selected_jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
    sys.path.insert(0,str(ROOT/'inputs/runtime'))
    from target_execution import evaluate_target_program
    from independent_verify import verify
    deadline=time.monotonic()+14400
    def one(j):
        if time.monotonic()>deadline-140:raise TimeoutError('Four-hour replay limit reached')
        source=(ROOT/'inputs/programs'/f"{j['program']}.py").read_text()
        result=evaluate_target_program(source,ROOT/'inputs/feasibility'/f"target_n{j['n']}.json",[j['seed']],j['budget'],ROOT/'inputs/runtime')
        case=result['runs'][0]['per_target'][0]
        (out/f"{j['id']:04d}.json").write_text(json.dumps(result,indent=2)+'\n')
        reference=read(ROOT/'records'/f"{j['id']:04d}.json")['runs'][0]['per_target'][0]
        if case.get('error'):raise RuntimeError(f"job {j['id']}: {case['error']}")
        if case['closed']:
            target={**case['target'],'d':case['parameters']['d']};code=out/f"{j['id']:04d}.code.json"
            code.write_text(json.dumps({'target':target,'generators':case['generators']})+'\n')
            verify(code,[target[k] for k in ['n','k','d','c']])
        matched=all(case.get(k)==reference.get(k) for k in ['closed','n_evals','parameters','generators'])
        return {'job':j['id'],'matches_archive':matched,'closed':case['closed'],'calls':case['n_evals']}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,jobs))
    (out/'summary.json').write_text(json.dumps({'runs':len(rows),'matches':sum(r['matches_archive'] for r in rows),'records':rows},indent=2)+'\n')
    print(f"{len(rows)} jobs replayed; {sum(r['matches_archive'] for r in rows)} match the archive.")
    if not all(r['matches_archive'] for r in rows):raise SystemExit(1)

if __name__=='__main__':main()
