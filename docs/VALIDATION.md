# Release validation, 2026-09-15

Validation used a separately extracted ZIP and a newly installed environment:
Python 3.12.12, NumPy 2.5.1, psutil 7.2.2 on macOS. Outputs were written outside
the immutable evidence directories. No cloud model calls were made.

| Check | Observed result |
|---|---|
| Mathematical deterministic tier | PASS: 115 core witnesses, family checks and 54 gap closures, 398 upper-bound corrections, prior intervals, novelty drift, refinement and prompt evidence |
| Latest-study offline audit | PASS: 56 analyzed proposals, 58 received sources, 235 independently verified study witness files |
| Table 1/2 evidence mapping | PASS: 18 rows linked to witnesses; all 13 historical intervals match the frozen snapshot |
| Historical program replay | PASS: 12 seeded runs; no proposal-list differences |
| Fresh selected-policy and baseline replay | PASS: 208/208 executions match archived success, evaluation count, parameters and generators; zero process errors |
| Independent policy | 21/64 test successes; 0/32 at longer lengths |
| Iterative policy | 38/64 test successes; 6/32 at longer lengths |
| Algorithm 1 | 16/16 at n=9,11; 3/4 at each of n=13,15 |
| Initial program | 0/16 on the main test seeds |
| Clean-extraction test suite | 40 passed, 1 skipped (a SAT solver is required for the skipped known-witness control) |
| Snapshot-default regression tests added after the clean-extraction check | 2 passed; default reproduces the frozen map, latest is an explicit override |
| Lint | PASS for scripts and tests |
| Paper build | PASS from the extracted source package, 19 total PDF pages |
| Figure sources | Figures 1, 3 and 4 regenerate byte-identical TeX content; Figure 4 also exports PDF/SVG/PNG |
| SAT/DRAT and Magma fresh checks | NOT RUN: tools unavailable in this validation environment; the auditor correctly reports PARTIAL/SKIPPED_NO_TOOL |

The frozen snapshot default in `build_bound_map.py` was fixed during this check.
Before the fix its numerical map matched, but its label silently changed to the
newest snapshot. The current default reads `artifacts/paper_reference.json`;
`latest` remains available as an explicit positional argument. Numerical evidence
and the archived map did not change.

The release builder scans all included text and PDF text/metadata, checks the
full-file manifest and writes the ZIP only on PASS. Identity-specific checks use
a private term list that is not distributed. The original 1,512 protected files
(model programs, complete latest-study records, witnesses, campaign records,
snapshots and certificates) remain byte-identical to the pre-cleanup snapshot.
The root archive manifest was refreshed only for anonymizing one historical log.
Raw originals, internal editorial notes and Git history remain recoverable in a
separate private archive. These local validation checks do not claim that the
remote CI jobs have run or that a public Git account/history is anonymous.
