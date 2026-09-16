"""A changed formal goal must not pass the archive's integrity check."""
import importlib.util
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lean_audit', ROOT / 'scripts/audit_lean_certificate.py')
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)


def test_preserved_lean_package():
    result = AUDIT.audit()
    assert result['exact_goal_pairs'] == 2
    assert result['kernel_execution'] == 'NOT_RUN'


def test_changed_formal_goal_is_rejected(tmp_path):
    project = tmp_path / 'certificate'
    shutil.copytree(AUDIT.ROOT, project, ignore=shutil.ignore_patterns('.lake'))
    solution = project / AUDIT.MODULES / 'Comparator/Theorem1Solution.lean'
    solution.write_text(solution.read_text().replace('3 ≤ Fintype.card', '4 ≤ Fintype.card'))
    with pytest.raises(ValueError, match='missing or changed'):
        AUDIT.audit(project)
