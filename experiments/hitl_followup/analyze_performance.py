"""Summarize the fixed local follow-up after completion; no selection or tuning."""
from pathlib import Path
import json
import math
import statistics
import itertools
O=Path(__file__).resolve().parent
p=json.loads((O/'protocol.json').read_text());state=json.loads((O/'status.json').read_text())
assert state['state']=='COMPLETED',state
rows=json.loads((O/'results.json').read_text());assert len(rows)==1560
assert len({r['id'] for r in rows})==1560

def wilson(s,n):
 z=1.959963984540054;v=s/n;den=1+z*z/n;center=(v+z*z/(2*n))/den;half=z*math.sqrt(v*(1-v)/n+z*z/(4*n*n))/den
 return [center-half,center+half]
def metric(rs):
 n=len(rs);hits=sum(r['closed'] for r in rs)
 return {'successes':hits,'runs':n,'rate':hits/n,'wilson95_execution_interval_descriptive':wilson(hits,n),'mean_curve_area':statistics.mean(r['utility'] for r in rs),'mean_charged_evals':statistics.mean(r['n_evals'] if r['closed'] else r['budget'] for r in rs),'errors':sum(bool(r.get('error')) for r in rs),'mean_wall_s':statistics.mean(r.get('elapsed_s',0) for r in rs)}
programs={}
for program,meta in p['programs'].items():
 programs[program]={**meta,'by_length':{str(n):metric([r for r in rows if r['phase']=='fresh' and r['program']==program and r['n']==n]) for n in [9,11,13,15]}}
blocks={}
for b in range(4):
 arms={arm:next(n for n,m in p['programs'].items() if m['arm']==arm and m['block']==b) for arm in ['independent','evolution']}
 blocks[str(b)]={}
 for split,lengths in [('test',[9,11]),('transfer',[13,15])]:
  ma={arm:metric([r for r in rows if r['phase']=='fresh' and r['program']==name and r['n'] in lengths]) for arm,name in arms.items()}
  blocks[str(b)][split]={'programs':arms,'metrics':ma,'auc_difference':ma['evolution']['mean_curve_area']-ma['independent']['mean_curve_area']}
pooled={}
for arm in ['initial','classical_dual','independent','evolution']:
 pooled[arm]={str(n):metric([r for r in rows if r['phase']=='fresh' and p['programs'][r['program']]['arm']==arm and r['n']==n]) for n in [9,11,13,15]}
# Primary policy uncertainty is described across the original four generation blocks.
diffs=[blocks[str(b)]['test']['auc_difference'] for b in range(4)];mean=statistics.mean(diffs)
permutation=sum(abs(sum(s*d for s,d in zip(signs,diffs))/4)>=abs(mean)-1e-12 for signs in itertools.product([-1,1],repeat=4))/16
result={'status':'PASS' if not any(r.get('error') for r in rows) else 'COMPLETE_WITH_ERRORS','fixed_program_results':programs,'pooled_execution_results':pooled,'block_comparison':blocks,'mean_test_auc_difference':mean,'descriptive_four_block_sign_flip_p':permutation,'archived_control':{str(n):metric([r for r in rows if r['phase']=='archived_baseline' and r['n']==n]) for n in [9,11,13,15]},'interpretation':'Fresh seed repeat of already selected programs, not fresh generation replication. Pooled Wilson intervals do not measure uncertainty of generation-policy superiority. Lineage was chosen after earlier performance; edits are not causally isolated.'}
(O/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# Local fixed-program follow-up','',result['interpretation'],'','## Fresh seeds (32 per program and length)','','| Program / arm | n=9 | n=11 | n=13 | n=15 |','|---|---:|---:|---:|---:|']
for name,d in programs.items():lines.append('| '+name+' | '+' | '.join(f"{d['by_length'][str(n)]['successes']}/32" for n in [9,11,13,15])+' |')
lines+=['','## Policy-level execution aggregates','','| Arm | n=9 | n=11 | n=13 | n=15 |','|---|---:|---:|---:|---:|']
for arm,d in pooled.items():lines.append('| '+arm+' | '+' | '.join(f"{d[str(n)]['successes']}/{d[str(n)]['runs']}" for n in [9,11,13,15])+' |')
lines+=['',f'Paired mean test curve-area difference: {mean:.6f}. Descriptive sign-flip p over four original blocks: {permutation:.4f}.','', 'All successful records were checked with the separate binary linear-algebra verifier.']
(O/'RESULTS.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
