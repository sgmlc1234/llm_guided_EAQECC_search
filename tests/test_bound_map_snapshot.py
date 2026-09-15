"""New snapshots must not silently replace the paper's fixed comparison."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_default_bound_map_reproduces_paper_archive(tmp_path):
    out = tmp_path / 'map.json'
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_bound_map.py'), '--out', str(out)],
                   check=True, capture_output=True)
    assert out.read_bytes() == (ROOT / 'artifacts/tables/bound_map.json').read_bytes()


def test_latest_snapshot_requires_explicit_selection(tmp_path):
    out = tmp_path / 'map.json'
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_bound_map.py'), 'latest', '--out', str(out)],
                   check=True, capture_output=True)
    dates = sorted(p.name for p in (ROOT / 'artifacts/codetables_snapshots').iterdir()
                   if p.is_dir() and (p / 'qubit.json').exists())
    assert json.loads(out.read_text())['snapshot'] == 'codetables.de, ' + dates[-1]
