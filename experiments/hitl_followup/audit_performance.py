"""Check completeness, preserved inputs, budgets, and independent code checks."""
from pathlib import Path
import hashlib
import json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((O/'protocol.json').read_text());s=json.loads((O/'status.json').read_text());rows=json.loads((O/'results.json').read_text())
assert s['state']=='COMPLETED',s
assert sha(O/'protocol.json')==(O/'protocol.sha256').read_text().strip()
assert len(rows)==len(p['jobs'])==1560
assert {r['id'] for r in rows}==set(range(1560))
assert all(sha(O/'inputs'/name)==h for name,h in p['input_sha256'].items())
checked=0;errors=[]
for r in rows:
 j=p['jobs'][r['id']];assert all(r[k]==v for k,v in j.items())
 if r.get('error'):errors.append({'id':r['id'],'error':r['error']})
 if r['n_evals'] is not None:assert 0<=r['n_evals']<=r['budget']
 raw=O/'records'/f"{r['id']:04d}.json"
 if r['closed']:
  d=json.loads(raw.read_text());v=d['independent_verification'];code=O/'codes'/f"{r['id']:04d}.json"
  assert v['status']=='PASS' and v['sha256']==sha(code)
  t=json.loads(code.read_text())['target'];assert t['n']==r['n'] and t['k']==1 and t['c']==r['n']-3 and t['d']>=r['n']-1
  checked+=1
assert checked==s['successes']
a={'state':'PASS' if not errors else 'COMPLETE_WITH_ERRORS','runs':len(rows),'independently_verified_successes':checked,'execution_errors':errors,'inputs_unchanged':True,'protocol_unchanged':True,'allocated_calls':sum(r['budget'] for r in rows),'observed_calls':sum(r['n_evals'] or 0 for r in rows),'scope':'All generated codes verified in the runner with the independent bit-matrix implementation; this audit validates its saved receipts and hashes.'}
(O/'AUDIT.json').write_text(json.dumps(a,indent=2)+'\n')
print(json.dumps(a,indent=2))
