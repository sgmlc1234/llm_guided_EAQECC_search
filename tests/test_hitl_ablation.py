"""Quota and exact-verification contracts for the active ablation runtime."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'experiments/hitl_ablation'
sys.path.insert(0,str(BUNDLE/'runtime'))
from target_driver import run_target
import controlled_helpers as H

WITNESS=json.loads((BUNDLE/'feasibility/n7.json').read_text())
TARGET=WITNESS['target']; GENERATORS=WITNESS['generators']


def test_return_verification_consumes_the_same_quota():
    result=run_target(f'def search(target,max_evals):\n    return {GENERATORS!r}\n',TARGET,1,1)
    assert result['closed'] and result['n_evals']==1
    assert result['phase_evals']['initialization']==0
    assert result['phase_evals']['final_return']==1


def test_no_free_solution_after_exhaustion():
    code=f'def search(target,max_evals):\n    E.evaluate([0])\n    return {GENERATORS!r}\n'
    result=run_target(code,TARGET,1,1)
    assert not result['closed'] and result['n_evals']==1
    assert result['termination']=='budget_exhausted'


def test_dual_conversion_produces_an_exactly_checked_code():
    dual=H.nullspace([H._J(v,7) for v in GENERATORS],14)
    code=f'def search(target,max_evals):\n    L={dual!r}\n    E.evaluate(E.nullspace([E._J(v,7) for v in L],14))\n'
    result=run_target(code,TARGET,1,1)
    assert result['closed'] and result['nullspace_calls']==1
    assert result['parameters']['d']==TARGET['d']
