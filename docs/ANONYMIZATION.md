# Anonymous release procedure

The working-tree release uses anonymous copyright/citation metadata, neutral
paths and sanitized operational logs. Bibliographic citations and third-party
license notices are preserved. The original Git history and public repository
identity are not made anonymous by these file edits.

The ICLR 2027 author guidelines require anonymity in both the main paper and
supplementary material: https://iclr.cc/Conferences/2027/AuthorGuidelines
The reviewer guide, paper and numerical artifacts are bundled without `.git/`.

## Build an inspectable, history-free package

```bash
python3 scripts/make_manifest.py --check
python3 scripts/eaqecc_ablation/audit.py
python3 scripts/release/build.py --out ../anonymous-release
python3 scripts/release/audit.py ../anonymous-release
```

For an identity-specific check, pass `--identifiers-file` to either release command.
This must be a private text file outside the release, one exact name, account ID,
email or other identifying phrase per line. It is not copied into the package and
matches are reported only by category and filename. Review bibliographic matches
in context; a third-person citation is not an author declaration.

The builder copies explicit source directories, rejects symlinks, omits local
caches, credentials, auxiliary TeX files and Git history, and includes only the
current `experiments/hitl_ablation/` study. It writes a full-file manifest, scans
text and rendered PDF text/metadata, and creates a ZIP only after the checks pass.
Poppler must be available to complete the PDF inspection. ZIP metadata uses fixed
timestamps and neutral file permissions, without local owner/group information.

Inspect the generated ZIP and verify a fresh extraction, not the development
checkout. Do not upload a clone containing `.git` or use the identified repository
URL as an anonymous supplement. The scripts prepare local files; they never push,
publish, rewrite Git history or submit an OpenReview form.

Automated checks are scoped to recognizable patterns and supplied identity terms;
they do not prove that already-public results cannot be associated with authors.
Keep the current release and its ZIP checksum together when submitting.
