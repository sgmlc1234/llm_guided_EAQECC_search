"""Release checks must reject identity leaks, local files and damaged contents."""
import hashlib
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('release_audit', Path(__file__).resolve().parents[1] / 'scripts/release/audit.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def manifest(root):
    lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n'
             for p in sorted(root.iterdir()) if p.is_file() and p.name != 'RELEASE_MANIFEST.sha256']
    (root / 'RELEASE_MANIFEST.sha256').write_text(''.join(lines))


def test_release_detects_mutation_and_unlisted_data(tmp_path):
    p = tmp_path / 'README.md'
    p.write_text('anonymous artifact\n')
    manifest(tmp_path)
    assert MODULE.audit(tmp_path)['status'] == 'PASS'
    p.write_text('changed result\n')
    assert MODULE.audit(tmp_path)['status'] == 'FAIL'
    manifest(tmp_path)
    (tmp_path / 'extra.json').write_text('{}')
    assert MODULE.audit(tmp_path)['status'] == 'FAIL'


def test_release_detects_private_identity_and_excluded_files(tmp_path):
    p = tmp_path / 'README.md'
    p.write_text('private-review-test-person')
    manifest(tmp_path)
    result = MODULE.audit(tmp_path, ['private-review-test-person'])
    assert any(x['category'] == 'private identity term' for x in result['findings'])
    p.write_text('/' + 'Users' + '/' + 'review-test-person' + '/data')
    manifest(tmp_path)
    assert MODULE.audit(tmp_path)['status'] == 'FAIL'
    p.write_text('anonymous')
    (tmp_path / '.env').write_text('')
    manifest(tmp_path)
    assert MODULE.audit(tmp_path)['status'] == 'FAIL'


def test_release_rejects_symlinks(tmp_path):
    (tmp_path / 'source').write_text('anonymous')
    (tmp_path / 'link').symlink_to('source')
    manifest(tmp_path)
    assert MODULE.audit(tmp_path)['status'] == 'FAIL'
