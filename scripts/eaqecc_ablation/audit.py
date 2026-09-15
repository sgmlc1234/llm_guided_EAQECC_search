"""Verify latest-study sources, prompts, selection, witnesses and reported metrics offline."""
import argparse
import json
import math
from pathlib import Path
from statistics import mean
import sys
from common import BUNDLE, read, sha, code_hash, ranked, rank_key, expected_prompt


def ledger_total_matches(values, recorded):
    """Allow sub-nanowon summation roundoff, not substantive ledger changes."""
    return math.isclose(math.fsum(values), recorded, rel_tol=0.0, abs_tol=1e-9)


def audit(bundle):
    sys.path.insert(0,str(bundle/'runtime'))
    from independent_verify import verify
    manifest=bundle/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            digest,name=line.split('  ',1)
            assert sha(bundle/name)==digest,name
    p=read(bundle/'protocol.json'); prefix=read(bundle/'balanced_prefix_protocol.json')
    cohorts=read(bundle/'balanced_cohorts.json'); selected=read(bundle/'selected_programs.json')
    ledger=read(bundle/'budget_ledger.json'); heldout=read(bundle/'heldout_results.json')
    assert len(ledger['calls'])==60 and len({x['id'] for x in ledger['calls']})==60
    assert sum(x['status']=='settled' for x in ledger['calls'])==58
    assert sum(x['status']=='uncertain' for x in ledger['calls'])==2
    assert prefix['analyzed_proposals']==56 and prefix['proposals_per_arm']==7
    included=[]
    for block,arms in cohorts.items():
        for arm,pool in arms.items():
            assert len(pool)==8
            for i,item in enumerate(pool[1:],1):
                folder=bundle/'candidates'/item['id']; previous=pool[:i]
                assert (folder/'program.py').read_text()==item['code']
                assert code_hash(item['code'])==item['evaluation']['code_sha256']
                parent=pool[0] if arm=='independent' else ranked(previous)[0]
                last=None if arm=='independent' or i==1 else previous[-1]
                req=read(folder/'request.json')
                assert req['contents'][0]['parts'][0]['text']==expected_prompt(bundle,p,parent,last)
                assert req['generationConfig']['seed']==p['model_seed_base']+int(block)*100+i-1
                assert read(folder/'parentage.json')==dict(parent=parent['id'],latest=last['id'] if last else None)
                included.append(item['id'])
            shortlist=ranked(pool)[:3]
            def selection_key(x):
                v=read(bundle/'validation'/code_hash(x['code'])/'evaluation.json')
                return v['mean_utility'],v['success_fraction'],v['mean_distance_ratio'],rank_key(x)
            assert max(shortlist,key=selection_key)['id']==selected[block][arm]['program_id']
    for call in ledger['calls']:
        folder=bundle/'candidates'/call['id']
        if call['status']=='settled':
            response=read(folder/'response.json')
            parts=response['candidates'][0]['content']['parts']
            code=json.loads(''.join(x.get('text','') for x in parts if not x.get('thought')))['code']
            assert (folder/'program.py').read_text()==code
            assert response['usageMetadata']==call['usage']
        else:
            assert not (folder/'response.json').exists()
            assert read(folder/'unavailable_response.json')['retried'] is False
    checked=0
    for path in sorted(bundle.rglob('*.witness.json')):
        record=read(path); t=record['target']; verify(path,[t[k] for k in ('n','k','d','c')]); checked+=1
    # Recompute every candidate/validation/test summary, not only headline values.
    for path in sorted(bundle.rglob('evaluation.json')):
        e=read(path)
        if 'cases' not in e: continue
        for c in e['cases']:
            assert c['allocated_evals'] in (10000,30000)
            if c['n_evals'] is not None: assert 0<=c['n_evals']<=c['allocated_evals']
            utility=1-c['n_evals']/c['allocated_evals'] if c['closed'] and not c.get('error') else 0
            assert abs(c['utility']-utility)<1e-12
        assert abs(e['mean_utility']-mean(c['utility'] for c in e['cases']))<1e-12
        assert abs(e['success_fraction']-mean(c['closed'] for c in e['cases']))<1e-12
    arm_metrics={}; diffs=[]
    for arm in p['arms']:
        test=[c for arms in heldout.values() for c in arms[arm]['test']['cases']]
        transfer=[c for arms in heldout.values() for c in arms[arm]['transfer']['cases']]
        for block in cohorts:
            h=selected[block][arm]['code_sha256']
            assert heldout[block][arm]['test']==read(bundle/'test'/h/'evaluation.json')
            assert heldout[block][arm]['transfer']==read(bundle/'transfer'/h/'evaluation.json')
        arm_metrics[arm]=dict(test_success=sum(c['closed'] for c in test),test_executions=len(test),
                             curve_area=mean(c['utility'] for c in test),transfer_success=sum(c['closed'] for c in transfer),transfer_executions=len(transfer),
                             by_length={str(n):sum(c['closed'] for c in test if c['target']['n']==n) for n in (9,11)})
    for arms in heldout.values(): diffs.append(arms['evolution']['test']['mean_utility']-arms['independent']['test']['mean_utility'])
    summary=read(bundle/'summary.json')
    assert abs(mean(diffs)-summary['mean_difference'])<1e-12
    assert ledger_total_matches((c['committed_krw'] for c in ledger['calls']), ledger['committed_krw'])
    assert p['prior_committed_krw']+ledger['committed_krw']<24000
    return dict(status='PASS',included_requests=len(included),received_sources=58,witnesses_verified=checked,
                arms=arm_metrics,block_area_differences=diffs,mean_area_difference=mean(diffs),
                selected_transfer_program=selected['2']['evolution']['program_id'],
                committed_krw_including_prior=p['prior_committed_krw']+ledger['committed_krw'])

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--bundle',type=Path,default=BUNDLE); ap.add_argument('--out',type=Path)
    args=ap.parse_args(); result=audit(args.bundle.resolve()); text=json.dumps(result,indent=2)+'\n'
    if args.out: args.out.write_text(text)
    print(text)
