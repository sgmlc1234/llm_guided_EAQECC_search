"""Floating-point summation changes must not mask actual ledger mutations."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/eaqecc_ablation'))
from audit import ledger_total_matches


def test_tolerates_summation_roundoff():
    assert ledger_total_matches([0.1] * 60, 6.0)
    assert ledger_total_matches([0.1] * 60, 6.0 + 1e-12)


def test_rejects_substantive_change_and_nonfinite_total():
    assert not ledger_total_matches([0.1] * 60, 6.0 + 1e-6)
    assert not ledger_total_matches([0.1] * 60, float('nan'))
