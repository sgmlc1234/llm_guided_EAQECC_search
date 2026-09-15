"""Check release boundaries, text/PDF anonymity and the full-file manifest.

Identity-specific terms can be supplied from a private file outside the release.
Findings report paths and categories, never matched values or credential bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BLOCKED = {'.git', '.env', '.venv', '__pycache__', '.pytest_cache', '.ruff_cache',
           '.DS_Store', 'private_execution.json', 'application_default_credentials.json'}
PATTERNS = {
    'personal filesystem path': r'/(?:Users|home)/[A-Za-z0-9_.-]+/',
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'access token': r'(?:AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}|ya29\.[A-Za-z0-9_-]{20,})',
    'cloud account': r'[\w.-]+@[\w.-]+\.iam\.gserviceaccount\.com',
    'numeric cloud project': r'projects/[0-9]{8,}/',
}


def audit(root, identifiers=(), require_manifest=True):
    root = Path(root).resolve()
    findings, warnings = [], []
    files = []
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if p.name in BLOCKED or (p.name.startswith('.env.') and p.name != '.env.example'):
            findings.append({'path': rel, 'category': 'excluded local file'})
        if p.is_symlink():
            findings.append({'path': rel, 'category': 'symlink'})
            continue
        if not p.is_file():
            continue
        files.append(p)
        if p.suffix == '.pdf':
            if not all(shutil.which(x) for x in ('pdftotext', 'pdfinfo')):
                warnings.append({'path': rel, 'category': 'PDF inspection requires Poppler'})
                continue
            text = subprocess.check_output(['pdftotext', str(p), '-'], text=True)
            text += subprocess.check_output(['pdfinfo', str(p)], text=True)
            # pdfinfo prints no input filename, so it adds no machine-local path.
        else:
            try:
                text = p.read_text(encoding='utf-8')
            except UnicodeError:
                continue
        for category, pattern in PATTERNS.items():
            if re.search(pattern, text):
                findings.append({'path': rel, 'category': category})
        if any(term.casefold() in text.casefold() for term in identifiers if term):
            findings.append({'path': rel, 'category': 'private identity term'})
        if p.name == 'CITATION.cff' and re.search(r'^repository-code:', text, re.M):
            findings.append({'path': rel, 'category': 'identified repository metadata'})
    manifest = root / 'RELEASE_MANIFEST.sha256'
    if require_manifest:
        if not manifest.exists():
            findings.append({'path': manifest.name, 'category': 'missing release manifest'})
        else:
            expected = {}
            for line in manifest.read_text().splitlines():
                digest, name = line.split('  ', 1)
                expected[name] = digest
            actual = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in files if p != manifest}
            for name in sorted(set(expected) | set(actual)):
                if expected.get(name) != actual.get(name):
                    findings.append({'path': name, 'category': 'manifest mismatch'})
    return {'status': 'FAIL' if findings else ('PARTIAL' if warnings else 'PASS'),
            'files_checked': len(files), 'findings': findings, 'warnings': warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root', type=Path)
    ap.add_argument('--identifiers-file', type=Path)
    args = ap.parse_args()
    terms = args.identifiers_file.read_text().splitlines() if args.identifiers_file else []
    result = audit(args.root, terms)
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result['findings'] else 0)


if __name__ == '__main__':
    main()
