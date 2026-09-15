"""Replay a preserved program in fresh OS-sandboxed processes, without cloud calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from common import BUNDLE,read,code_hash

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--program',required=True); ap.add_argument('--split',choices=['test','transfer'],default='test')
    ap.add_argument('--out',type=Path,required=True); ap.add_argument('--bundle',type=Path,default=BUNDLE)
    args=ap.parse_args(); b=args.bundle.resolve(); args.out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(b/'runtime'))
    from target_execution import evaluate_target_program
    from independent_verify import verify
    p=read(b/'protocol.json'); code=(b/'initial_program.py' if args.program=='initial' else b/'candidates'/args.program/'program.py').read_text()
    lengths=p['train_lengths'] if args.split=='test' else p['transfer_lengths']
    seeds=p[args.split+'_seeds']; budget=p[args.split+'_budget']
    original=b/args.split/code_hash(code)/'evaluation.json'
    reference=read(original)['cases'] if original.exists() else []
    def one(job):
        n,seed=job
        result=evaluate_target_program(code,b/'feasibility'/f'target_n{n}.json',[seed],budget,b/'runtime')
        c=result['runs'][0]['per_target'][0]
        # Preserve process diagnostics even when archive comparison fails.
        (args.out/f'n{n}_seed{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
        if c.get('error'):
            raise RuntimeError(f"target n={n}, seed={seed}: {c['error']}")
        if c['closed']:
            path=args.out/f'n{n}_seed{seed}.witness.json'; t={**c['target'],'d':c['parameters']['d']}
            path.write_text(json.dumps(dict(target=t,generators=c['generators']))+'\n'); verify(path,[t[k] for k in ('n','k','d','c')])
        old=next((x for x in reference if x['target']['n']==n and x['seed']==c['seed']),None)
        if old:
            assert all(c.get(k)==old.get(k) for k in ('closed','n_evals','parameters','generators')), (n,seed)
        return dict(n=n,seed=seed,success=c['closed'],calls=c['n_evals'],matches_archive=old is not None,error=c.get('error'))
    with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(one,[(n,s) for n in lengths for s in seeds]))
    result=dict(program=args.program,split=args.split,records=rows,successes=sum(x['success'] for x in rows))
    (args.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
