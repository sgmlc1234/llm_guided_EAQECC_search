"""Build a history-free anonymous release from explicit source directories.

Existing destinations are never overwritten. ZIP timestamps and permission bits
are normalized; original identities and Git history are not copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from audit import audit, BLOCKED

ROOT = Path(__file__).resolve().parents[2]
DIRECTORIES = ('scripts', 'tests', 'docs', 'assets', 'paper', 'artifacts',
               'experiments/hitl_ablation', '.github')
TOP_FILES = ('README.md', 'LICENSE', 'CITATION.cff', 'Makefile', 'pyproject.toml',
             '.gitignore', '.env.example', 'MANIFEST.sha256')
EXCLUDE_SUFFIXES = {'.pyc', '.pyo', '.aux', '.out', '.blg'}


def source_files(root):
    candidates = [root / x for x in TOP_FILES] + list(root.glob('requirements*.txt'))
    for name in DIRECTORIES:
        candidates.extend((root / name).rglob('*'))
    for p in sorted(set(candidates)):
        rel = p.relative_to(root)
        if any(x in BLOCKED for x in rel.parts) or p.suffix in EXCLUDE_SUFFIXES:
            continue
        if rel.parts[0] == 'paper' and p.suffix == '.log':
            continue
        if rel.as_posix() == 'artifacts/reproduce_eaqecc/reproduction_report.json':
            continue
        if p.is_symlink():
            raise ValueError(f'symlink in release input: {rel}')
        if p.is_file():
            yield p


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--identifiers-file', type=Path)
    args = ap.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if out == root or root in out.parents:
        ap.error('place the release outside the source repository')
    archive = out.with_suffix('.zip')
    if out.exists() or archive.exists():
        ap.error('destination or ZIP already exists; choose a new path')
    if args.identifiers_file and out in args.identifiers_file.resolve().parents:
        ap.error('private identity terms must remain outside the release')
    out.mkdir(parents=True)
    for p in source_files(root):
        dest = out / p.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
    entries = []
    for p in sorted(out.rglob('*')):
        if p.is_file():
            entries.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}\n')
    (out / 'RELEASE_MANIFEST.sha256').write_text(''.join(entries))
    terms = args.identifiers_file.read_text().splitlines() if args.identifiers_file else []
    result = audit(out, terms)
    if result['status'] != 'PASS':
        print(json.dumps(result, indent=2))
        raise SystemExit('Release was not zipped; resolve the findings in the source.')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():
                info = zipfile.ZipInfo('eaqecc_artifact/' + p.relative_to(out).as_posix(),
                                       date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())
    result.update(zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  zip_bytes=archive.stat().st_size)
    archive.with_suffix('.verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
