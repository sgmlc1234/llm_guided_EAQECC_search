"""Portable analysis of the latest preserved study; no cloud dependencies."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/hitl_ablation'

def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def code_hash(code): return hashlib.sha256(code.encode()).hexdigest()

def rank_key(item):
    e=item['evaluation']
    return e['mean_utility'],e['success_fraction'],e['mean_distance_ratio'],-item['generation']

def ranked(pool):
    seen=set(); result=[]
    for x in sorted(pool,key=rank_key,reverse=True):
        h=code_hash(x['code'])
        if h not in seen: result.append(x); seen.add(h)
    return result

def feedback(e):
    return {k:e[k] for k in ('mean_utility','success_fraction','mean_distance_ratio','errors')} | {'cases':[
        dict(n=c['target']['n'],seed=c['seed'],success=c['closed'],calls=c['n_evals'],
             distance=c.get('parameters',{}).get('d'),offending=c.get('parameters',{}).get('offending'),
             error=c.get('error'),termination=c['termination']) for c in e['cases']]}

def expected_prompt(bundle,p,parent,last):
    text=(bundle/'task.txt').read_text()+'\nTraining targets:\n'+json.dumps([read(bundle/'feasibility'/f'target_n{n}.json')[0] for n in p['train_lengths']])
    text+='\nStarting code:\n'+parent['code']+'\nTraining feedback:\n'+json.dumps(feedback(parent['evaluation']))
    if last is not None: text+='\nMost recent attempt (possibly rejected):\n'+last['code']+'\nIts training feedback:\n'+json.dumps(feedback(last['evaluation']))
    return text
