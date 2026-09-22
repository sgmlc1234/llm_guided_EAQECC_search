"""Frozen, budget-accounted comparison of shared-HITL independent and iterative generation."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import signal

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'runtime'))
from target_execution import evaluate_target_program
from independent_verify import verify as verify_witness
from pilot_budget import atomic_json, BudgetExceeded
from capped_budget import CappedLedger
from run_controlled_pilot import generate


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def code_hash(code): return hashlib.sha256(code.encode()).hexdigest()

def rank_key(item):
    e=item['evaluation']
    return (e['mean_utility'],e['success_fraction'],e['mean_distance_ratio'],-item['generation'])

def ranked(pool):
    output=[]; seen=set()
    for item in sorted(pool,key=rank_key,reverse=True):
        h=code_hash(item['code'])
        if h not in seen: output.append(item); seen.add(h)
    return output


def evaluate(code, lengths, seeds, budget, folder):
    folder.mkdir(parents=True,exist_ok=True)
    def one(n,seed):
        path=folder/f'n{n}_seed{seed}.json'
        if path.exists():
            result=read(path)
            assert result['code_sha256']==code_hash(code)
            assert result['runs'][0]['per_target'][0]['allocated_evals']==budget
            return result['runs'][0]['per_target'][0]
        result=evaluate_target_program(code,HERE/'feasibility'/f'target_n{n}.json',[seed],budget,HERE/'runtime')
        case=result['runs'][0]['per_target'][0]
        if case['closed']:
            witness=path.with_suffix('.witness.json')
            # Checker verifies the actually attained distance, which may exceed target d.
            target={**case['target'],'d':case['parameters']['d']}
            atomic_json(witness,dict(target=target,generators=case['generators']))
            case['independent_check']=verify_witness(witness,[target[k] for k in ('n','k','d','c')])
        atomic_json(path,result)
        return case
    cases=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[pool.submit(one,n,seed) for n in lengths for seed in seeds]
        for f in as_completed(jobs): cases.append(f.result())
    cases.sort(key=lambda c:(c['target']['n'],c['seed']))
    for c in cases:
        c['utility']=1-c['n_evals']/budget if c['closed'] and not c.get('error') else 0.0
    result=dict(code_sha256=code_hash(code),mean_utility=sum(c['utility'] for c in cases)/len(cases),
                success_fraction=sum(c['closed'] for c in cases)/len(cases),
                mean_distance_ratio=sum(c['distance_ratio'] for c in cases)/len(cases),
                errors=sum(bool(c.get('error')) for c in cases),cases=cases)
    atomic_json(folder/'evaluation.json',result)
    return result


def feedback(e):
    return {k:e[k] for k in ('mean_utility','success_fraction','mean_distance_ratio','errors')} | {
        'cases':[dict(n=c['target']['n'],seed=c['seed'],success=c['closed'],calls=c['n_evals'],
                      distance=c.get('parameters',{}).get('d'),offending=c.get('parameters',{}).get('offending'),
                      error=c.get('error'),termination=c['termination']) for c in e['cases']]}


def payload(p,parent,last,block,generation,arm):
    text=(HERE/'task.txt').read_text()+'\nTraining targets:\n'+json.dumps([read(HERE/'feasibility'/f'target_n{n}.json')[0] for n in p['train_lengths']])
    text+='\nStarting code:\n'+parent['code']+'\nTraining feedback:\n'+json.dumps(feedback(parent['evaluation']))
    if last is not None:
        text+='\nMost recent attempt (possibly rejected):\n'+last['code']+'\nIts training feedback:\n'+json.dumps(feedback(last['evaluation']))
    return {'contents':[{'role':'user','parts':[{'text':text}]}],
            'generationConfig':{'maxOutputTokens':p['max_output_tokens'],'candidateCount':1,
                                'thinkingConfig':{'thinkingLevel':'LOW'},'seed':p['model_seed_base']+block*100+generation,
                                'responseMimeType':'application/json','responseSchema':{'type':'OBJECT','properties':{'code':{'type':'STRING'}},'required':['code']}},
            'labels':{'experiment':'eaqecc-hitl-v4','arm':arm}}


def freeze():
    raise RuntimeError('Use the prepared approved replication protocol; no historical freeze.')


def verify_inputs():
    p=read(HERE/'protocol.json')
    assert sha(HERE/'protocol.json')==read(HERE/'status.json')['protocol_sha256']
    for name,digest in p['input_hashes'].items(): assert sha(HERE/name)==digest,name
    for name,digest in p['prior_ledgers'].items(): assert sha(ROOT/name)==digest,name
    assert sha(HERE/'private_execution.json')==p['private_execution_sha256']
    return p


def postprocess(p,cohorts):
    selected={}
    for block,pools in cohorts.items():
        selected[block]={}
        for arm,pool in pools.items():
            short=ranked(pool)[:3]
            validations={}
            for item in short:
                h=code_hash(item['code'])
                validations[h]=evaluate(item['code'],p['train_lengths'],p['validation_seeds'],p['validation_budget'],HERE/'validation'/h)
            winner=max(short,key=lambda x:(validations[code_hash(x['code'])]['mean_utility'],validations[code_hash(x['code'])]['success_fraction'],validations[code_hash(x['code'])]['mean_distance_ratio'],rank_key(x)))
            selected[block][arm]=dict(program_id=winner['id'],code=winner['code'],code_sha256=code_hash(winner['code']),shortlist=[x['id'] for x in short])
            atomic_json(HERE/'selected_programs.json',selected)
    results={}
    for block,arms in selected.items():
        results[block]={}
        for arm,item in arms.items():
            h=item['code_sha256']
            test=evaluate(item['code'],p['train_lengths'],p['test_seeds'],p['test_budget'],HERE/'test'/h)
            transfer=evaluate(item['code'],p['transfer_lengths'],p['transfer_seeds'],p['transfer_budget'],HERE/'transfer'/h)
            results[block][arm]=dict(program_id=item['program_id'],test=test,transfer=transfer)
            atomic_json(HERE/'heldout_results.json',results)
            print(json.dumps({'heldout_block':block,'arm':arm,'utility':test['mean_utility'],'success':test['success_fraction'],'transfer_success':transfer['success_fraction']}),flush=True)
    initial=(HERE/'initial_program.py').read_text()
    evaluate(initial,p['train_lengths'],p['test_seeds'],p['test_budget'],HERE/'test'/code_hash(initial))
    differences=[arms['evolution']['test']['mean_utility']-arms['independent']['test']['mean_utility'] for arms in results.values()]
    ledger=read(HERE/'budget_ledger.json')
    summary=dict(state='COMPLETED',blocks=len(results),block_differences=differences,mean_difference=sum(differences)/len(differences),
                 arms={arm:{metric:sum(arms[arm]['test'][metric] for arms in results.values())/len(results) for metric in ('mean_utility','success_fraction','mean_distance_ratio')} for arm in p['arms']},
                 new_estimated_model_krw=ledger['estimated_model_krw'],new_committed_krw=ledger['committed_krw'],aggregate_committed_krw=p['prior_committed_krw']+ledger['committed_krw'])
    atomic_json(HERE/'summary.json',summary)
    return summary


def run():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession,Request
    p=verify_inputs()
    def wall_limit(signum, frame):
        raise TimeoutError('Approved 24-hour wall limit reached')
    signal.signal(signal.SIGALRM,wall_limit)
    signal.alarm(int(p['max_wall_hours']*3600))
    lock=(HERE/'authorization.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (HERE/'budget_ledger.json').exists(),'automatic billed restart prohibited'
    project=read(HERE/'private_execution.json')['project']
    assert os.environ.get('GOOGLE_CLOUD_PROJECT',project)==project
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    credentials=credentials.with_quota_project(project); credentials.refresh(Request())
    session=AuthorizedSession(credentials,max_refresh_attempts=0)
    endpoint=f'https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/publishers/google/models/{p["model"]}'
    prices=read(HERE/'prices.json')
    ledger=CappedLedger(HERE/'budget_ledger.json',p['remaining_service_cap_krw'],prices['input']['krw_per_token'],prices['output']['krw_per_token'],1.25)
    status=read(HERE/'status.json'); status['started_unix']=time.time()
    def state(**updates):
        status.update(updates,new_committed_krw=ledger.data['committed_krw'],aggregate_committed_krw=p['prior_committed_krw']+ledger.data['committed_krw'])
        atomic_json(HERE/'status.json',status)
    initial={'id':'initial','generation':-1,'code':(HERE/'initial_program.py').read_text()}
    cohorts={}
    try:
        state(state='BASELINE_EVALUATION')
        initial['evaluation']=evaluate(initial['code'],p['train_lengths'],p['train_seeds'],p['train_budget'],HERE/'baseline_train')
        cohorts={str(b):{arm:[initial] for arm in p['arms']} for b in range(p['blocks'])}
        # Round-robin blocks prevent a budget stop from spending everything on an early block.
        for generation in range(p['proposals_per_arm']):
            for block in range(p['blocks']):
                if (HERE/'STOP').exists(): raise RuntimeError('user STOP file')
                pools=cohorts[str(block)]; requests={}
                for arm,pool in pools.items():
                    parent=initial if arm=='independent' else ranked(pool)[0]
                    last=None if arm=='independent' or not generation else pool[-1]
                    request=payload(p,parent,last,block,generation,arm)
                    counted=session.post(endpoint+':countTokens',json={'contents':request['contents']},timeout=30)
                    counted.raise_for_status()
                    assert counted.json()['totalTokens']<=p['max_input_tokens'],'prompt cap'
                    requests[arm]=(request,parent,last)
                ledger.ensure(sum(ledger.bound(len(json.dumps(x[0],ensure_ascii=False).encode())) for x in requests.values()))
                order=p['arms'] if (block+generation)%2==0 else p['arms'][::-1]
                for arm in order:
                    request,parent,last=requests[arm]
                    call_id=f'b{block:02d}_{arm}_g{generation:02d}'
                    folder=HERE/'candidates'/call_id
                    state(state='GENERATING',block=block,generation=generation,arm=arm)
                    code=generate(session,endpoint,request,folder,ledger,call_id)
                    (folder/'program.py').write_text(code)
                    atomic_json(folder/'parentage.json',dict(parent=parent['id'],latest=last['id'] if last else None))
                    state(state='TRAIN_EVALUATION')
                    result=evaluate(code,p['train_lengths'],p['train_seeds'],p['train_budget'],folder/'train')
                    pools[arm].append(dict(id=call_id,generation=generation,code=code,evaluation=result))
                    atomic_json(HERE/'cohorts.json',cohorts)
                    state(completed_candidates=status['completed_candidates']+1)
                    print(json.dumps(dict(candidate=call_id,utility=result['mean_utility'],success=result['success_fraction'],errors=result['errors'],aggregate_committed_krw=status['aggregate_committed_krw'])),flush=True)
        state(state='VALIDATION_AND_HELDOUT')
        summary=postprocess(p,cohorts)
        state(state='COMPLETED',finished_unix=time.time())
        print(json.dumps(summary),flush=True)
    except BaseException as exc:
        state(state='STOPPED',reason=f'{type(exc).__name__}: {str(exc)[:400]}',stopped_unix=time.time())
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['freeze','run','postprocess'])
    args=parser.parse_args()
    if args.stage=='freeze': freeze()
    elif args.stage=='run': run()
    else:
        p=verify_inputs(); cohorts=read(HERE/'cohorts.json')
        assert all(len(pool)==p['proposals_per_arm']+1 for arms in cohorts.values() for pool in arms.values())
        summary=postprocess(p,cohorts)
        status=read(HERE/'status.json'); status.update(state='COMPLETED',finished_unix=time.time()); atomic_json(HERE/'status.json',status)
        print(json.dumps(summary))
