"""Operational recovery: never resend an ambiguous request; finish remaining planned slots."""
import fcntl
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import study as S
from capped_budget import CappedLedger
from run_controlled_pilot import generate


def main():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession,Request
    p=S.verify_inputs()
    lock=(HERE/'authorization.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    status=S.read(HERE/'status.json')
    if not (HERE/'operational_amendment.json').exists():
        assert status['state']=='STOPPED' and 'uncertain' in status['reason']
        assert not (HERE/'validation').exists() and not (HERE/'test').exists()
        S.atomic_json(HERE/'transport_stop.json',status)
        S.atomic_json(HERE/'operational_amendment.json',dict(created_unix=time.time(),original_protocol_sha256=S.sha(HERE/'protocol.json'),
            recovery_source_sha256=S.sha(Path(__file__)),
            rule='An already attempted request with unavailable response consumes its proposal slot and retains the full monetary reservation. It is never sent again. Its explicitly marked unavailable-source placeholder receives zero utility and failure feedback. Continue only unattempted planned slots with unchanged targets, seeds, policies, budgets and selection. Apply the same rule to either policy. Stop on a second consecutive unavailable response. This operational amendment precedes all validation/test observations.',
            sensitivity='Also report the paired mean contrast excluding any campaign block with an unavailable generation response; do not replace the primary all-block contrast.',
            deviation='The original runner stopped on transport uncertainty. This separately frozen recovery continues the remaining unique slots instead of truncating the comparison.'))
    else:
        assert S.read(HERE/'operational_amendment.json')['recovery_source_sha256']==S.sha(Path(__file__))
    prices=S.read(HERE/'prices.json')
    ledger=CappedLedger(HERE/'budget_ledger.json',p['remaining_service_cap_krw'],prices['input']['krw_per_token'],prices['output']['krw_per_token'],1.25)
    project=S.read(HERE/'private_execution.json')['project']
    creds,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    creds=creds.with_quota_project(project); creds.refresh(Request())
    session=AuthorizedSession(creds,max_refresh_attempts=0)
    endpoint=f'https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/publishers/google/models/{p["model"]}'
    cohorts=S.read(HERE/'cohorts.json')
    initial=cohorts['0']['independent'][0]
    unavailable=[]
    def state(**updates):
        status.update(updates,new_committed_krw=ledger.data['committed_krw'],aggregate_committed_krw=p['prior_committed_krw']+ledger.data['committed_krw'],operational_amendment_sha256=S.sha(HERE/'operational_amendment.json'))
        S.atomic_json(HERE/'status.json',status)
    consecutive=0
    try:
        for generation in range(p['proposals_per_arm']):
            for block in range(p['blocks']):
                if (HERE/'STOP').exists(): raise RuntimeError('user STOP file')
                pools=cohorts[str(block)]
                order=p['arms'] if (block+generation)%2==0 else p['arms'][::-1]
                pending={}
                for arm in order:
                    ident=f'b{block:02d}_{arm}_g{generation:02d}'
                    if any(x['id']==ident for x in pools[arm]): continue
                    assert len(pools[arm])==generation+1
                    parent=initial if arm=='independent' else S.ranked(pools[arm])[0]
                    last=None if arm=='independent' or not generation else pools[arm][-1]
                    request=S.payload(p,parent,last,block,generation,arm)
                    entry=next((x for x in ledger.data['calls'] if x['id']==ident),None)
                    if entry is None:
                        counted=session.post(endpoint+':countTokens',json={'contents':request['contents']},timeout=30)
                        counted.raise_for_status(); assert counted.json()['totalTokens']<=p['max_input_tokens']
                    else:
                        assert entry['status']=='uncertain'
                        assert S.read(HERE/'candidates'/ident/'request.json')==request
                    pending[arm]=(ident,parent,last,request,entry)
                ledger.ensure(sum(ledger.bound(len(json.dumps(x[3],ensure_ascii=False).encode())) for x in pending.values() if x[4] is None))
                for arm in order:
                    if arm not in pending: continue
                    ident,parent,last,request,entry=pending[arm]
                    folder=HERE/'candidates'/ident
                    state(state='GENERATING',block=block,generation=generation,arm=arm)
                    if entry is None:
                        try:
                            code=generate(session,endpoint,request,folder,ledger,ident)
                            consecutive=0
                        except RuntimeError:
                            entry=next(x for x in ledger.data['calls'] if x['id']==ident)
                            if entry['status']!='uncertain': raise
                    if entry is not None:
                        consecutive+=1; unavailable.append(ident)
                        S.atomic_json(folder/'unavailable_response.json',dict(reason='transport timeout; no source received',request_sha256=S.sha(folder/'request.json'),reserved_krw=entry['committed_krw'],retried=False))
                        code='# UNAVAILABLE RESPONSE PLACEHOLDER, NOT MODEL-GENERATED CODE.\n'
                        if consecutive>1: raise RuntimeError('two consecutive unavailable responses; stop remaining paid requests')
                    (folder/'program.py').write_text(code)
                    S.atomic_json(folder/'parentage.json',dict(parent=parent['id'],latest=last['id'] if last else None))
                    state(state='TRAIN_EVALUATION')
                    result=S.evaluate(code,p['train_lengths'],p['train_seeds'],p['train_budget'],folder/'train')
                    item=dict(id=ident,generation=generation,code=code,evaluation=result)
                    if entry is not None: item['generation_response_unavailable']=True
                    pools[arm].append(item)
                    S.atomic_json(HERE/'cohorts.json',cohorts)
                    state(completed_candidates=status['completed_candidates']+1)
                    print(json.dumps(dict(candidate=ident,utility=result['mean_utility'],success=result['success_fraction'],errors=result['errors'],response_unavailable=entry is not None,aggregate_committed_krw=status['aggregate_committed_krw'])),flush=True)
        state(state='VALIDATION_AND_HELDOUT')
        summary=S.postprocess(p,cohorts)
        summary['unavailable_responses']=[x['id'] for x in ledger.data['calls'] if x['status']=='uncertain']
        summary['uncertain_reserved_krw']=sum(x['committed_krw'] for x in ledger.data['calls'] if x['status']=='uncertain')
        S.atomic_json(HERE/'summary.json',summary)
        state(state='COMPLETED',finished_unix=time.time())
        print(json.dumps(summary),flush=True)
    except BaseException as exc:
        state(state='STOPPED',reason=f'{type(exc).__name__}: {str(exc)[:400]}',stopped_unix=time.time())
        raise

if __name__=='__main__':main()
