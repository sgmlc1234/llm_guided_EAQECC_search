"""Verify nonbinary provenance hashes and the shared fixed-pair construction form."""
from pathlib import Path
import hashlib
import json
from helpers_eaqecc_fq import Fq, fq_rank

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'artifacts/construction_provenance/nonbinary'

def audit():
    for name,expected in json.loads((BUNDLE/'MANIFEST.sha256.json').read_text()).items():
        assert hashlib.sha256((BUNDLE/name).read_bytes()).hexdigest()==expected,name
    records=json.loads((BUNDLE/'registry.json').read_text())['records']
    assert len(records)==23
    historical=0
    for rec in records:
        path=ROOT/rec['published'];assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['sha256']
        code=json.loads(path.read_text());t=code['target'];n=t['n'];q=t['q'];j=n-1-t['c'];F=Fq(q);L=code['L_basis']
        fixed=[]
        for i in range(j):
            row=[0]*(2*n);row[4*i+1]=row[4*i+3]=1;fixed.append(row)
        assert L[:j]==fixed and len(L)==j+2 and fq_rank(F,L)==j+2
        assert all(F.sform(row,v,n)==0 for row in fixed for v in L)
        assert F.sform(L[-2],L[-1],n)!=0
        needle=f"[[{n},1,{t['d']};{t['c']}]]_{q} FOUND"
        for log in rec['historical_success_logs']:assert needle in (BUNDLE/log).read_text()
        historical+=bool(rec['historical_success_logs'])
        if rec.get('fresh_replay'):
            replay=json.loads((BUNDLE/rec['fresh_replay']).read_text())
            assert replay['exit']==0 and replay['byte_identical'] and replay['output_sha256']==rec['sha256']
    assert historical==22
    return {'status':'PASS','codes':23,'fixed_pair_shape_and_signature':23,'historical_success_log_matches':22,'fresh_byte_identical_replays':1,'distance_scope':'Distances are covered by the artifact code verification and independent Magma records; this audit checks hashes and construction structure.'}

if __name__=='__main__':print(json.dumps(audit(),indent=2))
