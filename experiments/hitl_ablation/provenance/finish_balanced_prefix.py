"""Freeze the fully completed balanced prefix before any held-out data, then evaluate locally."""
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import study as S


def main():
    original=S.verify_inputs()
    cohorts=S.read(HERE/'cohorts.json')
    ledger=S.read(HERE/'budget_ledger.json')
    frozen=HERE/'balanced_prefix_protocol.json'
    if not frozen.exists():
        status=S.read(HERE/'status.json')
        assert status['state']=='STOPPED' and 'two consecutive' in status['reason']
        assert not (HERE/'validation').exists() and not (HERE/'test').exists()
        counts=[]
        for arms in cohorts.values():
            for pool in arms.values():
                count=0
                for item in pool[1:]:
                    if item.get('generation_response_unavailable'): break
                    assert item['generation']==count
                    count+=1
                counts.append(count)
        common=min(counts)
        assert common>0
        rule=dict(created_unix=time.time(),original_protocol_sha256=S.sha(HERE/'protocol.json'),
                  finish_source_sha256=S.sha(Path(__file__)),cohorts_sha256=S.sha(HERE/'cohorts.json'),ledger_sha256=S.sha(HERE/'budget_ledger.json'),
                  proposals_per_arm=common,blocks=original['blocks'],analyzed_proposals=common*original['blocks']*len(original['arms']),
                  planned_proposals=96,attempted_requests=len(ledger['calls']),received_responses=sum(c['status']=='settled' for c in ledger['calls']),
                  rule='Use the longest contiguous generation prefix fully received and evaluated in EVERY block/policy. This is determined only by completion, not score. Exclude later completed proposals symmetrically, preserve them as supplementary records. No additional paid calls. Keep original training metrics, validation selection, targets, evaluation budgets and fresh execution seeds.',
                  limitation='Infrastructure-truncated follow-up: fewer proposals than originally planned; not completion of the planned 96-candidate study. Frozen before any validation/test results.')
        S.atomic_json(frozen,rule)
        S.atomic_json(HERE/'balanced_cohorts.json',{b:{a:pool[:common+1] for a,pool in arms.items()} for b,arms in cohorts.items()})
    rule=S.read(frozen)
    assert rule['finish_source_sha256']==S.sha(Path(__file__))
    assert rule['cohorts_sha256']==S.sha(HERE/'cohorts.json') and rule['ledger_sha256']==S.sha(HERE/'budget_ledger.json')
    p={**original,'proposals_per_arm':rule['proposals_per_arm']}
    status=S.read(HERE/'status.json')
    status.update(state='BALANCED_PREFIX_HELDOUT',balanced_prefix_protocol_sha256=S.sha(frozen),analyzed_proposals=rule['analyzed_proposals'])
    S.atomic_json(HERE/'status.json',status)
    summary=S.postprocess(p,S.read(HERE/'balanced_cohorts.json'))
    summary.update(state='COMPLETED_BALANCED_PREFIX',planned_proposals=96,analyzed_proposals=rule['analyzed_proposals'],
                   proposals_per_policy_per_block=rule['proposals_per_arm'],received_responses=rule['received_responses'],attempted_requests=rule['attempted_requests'],
                   unavailable_responses=[c['id'] for c in ledger['calls'] if c['status']=='uncertain'],
                   uncertain_reserved_krw=sum(c['committed_krw'] for c in ledger['calls'] if c['status']=='uncertain'),
                   balanced_prefix_protocol_sha256=S.sha(frozen))
    S.atomic_json(HERE/'summary.json',summary)
    status.update(state='COMPLETED_BALANCED_PREFIX',finished_unix=time.time())
    S.atomic_json(HERE/'status.json',status)
    print(json.dumps(summary),flush=True)

if __name__=='__main__': main()
