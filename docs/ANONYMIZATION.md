# Before the supplementary upload

The public repository is not anonymous; the ICLR supplementary zip must be.
Run through this list on a fresh clone.

- [ ] `LICENSE` copyright line → "The Authors"
- [ ] `CITATION.cff` authors → anonymous (already), `repository-code` → remove
- [ ] `README.md` → remove the GitHub URL
- [ ] `grep -rn "imds\|jhbaek\|sgmlc\|Kim\|Baek" .` → nothing
- [ ] `artifacts/campaigns/*.log` → grep for project ids, hostnames, user paths
- [ ] `artifacts/ablation/**/summary.json` → the `program` field holds an absolute path
- [ ] `.git/` → do not ship history; zip the working tree only
- [ ] `.env` → must not exist in the tree (it is gitignored, but check the zip)
