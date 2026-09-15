"""Freeze and measure whether this evaluator can reward a useful representation edit."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / 'runtime'))
from target_execution import evaluate_target_program
from independent_verify import verify
from pilot_budget import atomic_json


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare():
    protocol_path = HERE/'calibration_protocol.json'
    if protocol_path.exists():
        return
    sys.path.insert(0, str(ROOT/'scripts/families'))
    from verify_family import family_generators, check_L_side
    import controlled_helpers as H
    (HERE/'feasibility').mkdir()
    for n in (7, 9, 11, 13, 15):
        assert check_L_side(n) == n-1
        target = dict(q=2, n=n, k=1, c=n-3, d=n-1)
        witness = HERE/'feasibility'/f'n{n}.json'
        atomic_json(witness, dict(target=target, generators=H.nullspace([H._J(v,n) for v in family_generators(n)],2*n)))
        atomic_json(witness.with_suffix('.check.json'), verify(witness, [n,1,n-1,n-3]))
        atomic_json(HERE/'feasibility'/f'target_n{n}.json', [target])
    inputs = [HERE/'initial_program.py', HERE/'controls/dual_count.py', Path(__file__), *sorted((HERE/'runtime').glob('*.py'))]
    protocol = dict(created_unix=time.time(), stage='calibration only, no paid generation',
                    targets=[7,9,11], seeds=list(range(202609141001,202609141005)),
                    controls={'initial':'initial_program.py','dual':'controls/dual_count.py'},
                    max_evals=100000, grid=[1000,3000,10000,30000,100000],
                    gate='At least one cell/budget has initial success in [0.1,0.5], dual success >=0.5 and gain >=0.25. Select its smallest passing budget. Other training cells may be initial-floor if dual success >=0.5 at their smallest such budget.',
                    training_rule='Use passing n=9 and n=11 cells; n=7 is a diagnostic only. If n=9 has no calibrated nonfloor cell, stop before model calls.',
                    note='Control callbacks do not depend on max_evals except through remaining; prefixes of a 100k run are valid calibration curves. Not an evolution effect.',
                    input_hashes={str(p.relative_to(HERE)):sha(p) for p in inputs})
    atomic_json(protocol_path, protocol)


def evaluate(control, n, seed, protocol):
    out=HERE/'calibration'/f'{control}_n{n}_seed{seed}.json'
    if out.exists():
        return
    result=evaluate_target_program((HERE/protocol['controls'][control]).read_text(),HERE/'feasibility'/f'target_n{n}.json',[seed],protocol['max_evals'],HERE/'runtime')
    case=result['runs'][0]['per_target'][0]
    if case['closed']:
        witness=out.with_suffix('.witness.json')
        atomic_json(witness,dict(target=case['target'],generators=case['generators']))
        case['independent_check']=verify(witness,[case['target'][k] for k in ('n','k','d','c')])
    atomic_json(out,result)
    print(json.dumps(dict(control=control,n=n,seed=seed,solved=case['closed'],calls=case['n_evals'],error=case.get('error'))),flush=True)


def run():
    prepare()
    protocol=json.loads((HERE/'calibration_protocol.json').read_text())
    for name,digest in protocol['input_hashes'].items():
        assert sha(HERE/name)==digest, name
    (HERE/'calibration').mkdir(exist_ok=True)
    jobs=[(control,n,seed) for n in protocol['targets'] for seed in protocol['seeds'] for control in protocol['controls']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(evaluate,*job,protocol) for job in jobs]
        for f in concurrent.futures.as_completed(futures): f.result()
    curves=[]
    for n in protocol['targets']:
        for control in protocol['controls']:
            cases=[json.loads((HERE/'calibration'/f'{control}_n{n}_seed{seed}.json').read_text())['runs'][0]['per_target'][0] for seed in protocol['seeds']]
            curves.append(dict(n=n,control=control,hits={str(b):sum(c['closed'] and c['n_evals']<=b for c in cases) for b in protocol['grid']},replicates=len(cases),errors=sum(bool(c.get('error')) for c in cases)))
    selected={}
    for n in (9,11):
        a=next(x for x in curves if x['n']==n and x['control']=='initial')
        b=next(x for x in curves if x['n']==n and x['control']=='dual')
        budgets=[q for q in protocol['grid'] if 0.1<=a['hits'][str(q)]/4<=0.5 and b['hits'][str(q)]/4>=0.5 and (b['hits'][str(q)]-a['hits'][str(q)])/4>=0.25]
        if budgets: selected[str(n)]=dict(budget=min(budgets),kind='nonfloor')
        elif n==11:
            budgets=[q for q in protocol['grid'] if b['hits'][str(q)]/4>=0.5 and a['hits'][str(q)]==0]
            if budgets: selected[str(n)]=dict(budget=min(budgets),kind='representation-onset')
    passed='9' in selected and not any(x['errors'] for x in curves)
    result=dict(state='PASSED' if passed else 'NOT_SEPARATING',protocol_sha256=sha(HERE/'calibration_protocol.json'),curves=curves,selected=selected)
    atomic_json(HERE/'calibration_summary.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__': run()
