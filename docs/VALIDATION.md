# Final post-review validation, 2026-09-22

The final public tree adds the prospective eight-block replication, the
frozen-program repeat, fresh SAT/DRAT resource records, binary-normalization
certificates, nonbinary construction provenance and the Linux Comparator replay.
Private host configuration and operational notes remain under the ignored
`notes/private/` directory.

| Check | Observed result |
|---|---|
| Mathematical deterministic tier | PASS: 115 core code records, 54 family gap closures and 398 EA-Plotkin corrections |
| Prospective generation audit | PASS: 111 received proposals in eight blocks, 16 validation selections, 3,136 execution records and 1,171 independently rechecked successful records |
| Prospective policy result | Test curve-area difference +0.0987 in 5/8 positive blocks; descriptive sign-flip $p=0.3281$ |
| Unseen lengths 13 and 15 | Independent 50/256 and 8/256; iterative 118/256 and 81/256 |
| Frozen-program repeat | PASS: 1,560 runs, 545 independently verified successful records, zero execution errors |
| Binary normalization | PASS: seven normalized UNSAT instances with checked DRAT proofs; feasible `[[6,1,5;2]]_2` positive control remains SAT and independently verifies |
| Original exclusions | PASS: all ten decisions and DRAT certificates checked; on-demand binary proof regenerated |
| Nonbinary provenance | PASS: all 23 q=4,5 matrices mapped to preserved search evidence; the missing historical q=4 record was reconstructed byte-identically |
| Magma | PASS in the preserved V2.28-20 record: 148/148 objects, zero mismatches |
| Lean | PASS: 13 source hashes and two exact goal pairs; fresh macOS kernel build and Linux Comparator replays for Theorem 1 and supporting Lemma 2 |
| Paper and editable package | PASS: nine main pages, 25 total pages, Results on page 5; single-TeX `v17_B` package independently compiles and parses on all pages |
| Public-bundle replay | PASS: 64/64 executions of a selected new-cohort program match the sanitized archive |
| CI portability | The macOS replay uses standalone uv-managed Python 3.12.12 inside the OS sandbox and uploads from a workspace-local path. Python 3.9 checks the deterministic tier but excludes the preserved 3.12-only controlled-study runtime test; Python 3.12 runs the full suite and audits the new replication, follow-up and nonbinary evidence |

The manuscript reports the new eight-block cohort as a separate prospective
replication. Generation blocks, not repeated execution seeds, are the inference
units. The original four-block cohort and its fresh-seed repeat remain available
for transparency without being pooled into the new result. Longer-code outcomes
are secondary endpoints.

# Historical release validation, 2026-09-15

Validation used a separately extracted ZIP and a newly installed environment:
Python 3.12.12, NumPy 2.5.1, psutil 7.2.2 on macOS. Outputs were written outside
the immutable evidence directories. No cloud model calls were made.

| Check | Observed result |
|---|---|
| Mathematical deterministic tier | PASS: 115 core codes, family checks and 54 gap closures, 398 upper-bound corrections, prior intervals, novelty drift, refinement and prompt evidence |
| Latest-study offline audit | PASS: 56 analyzed proposals, 58 received sources, 235 independently verified study code records |
| Table 1/2 evidence mapping | PASS: 18 rows linked to codes; all 13 historical intervals match the frozen snapshot |
| Historical program replay | PASS: 12 seeded runs; no proposal-list differences |
| Algorithm 1 (rank05) direct replay | PASS: two executions at seed 20260814 and nominal N=5,000 produce identical proposal lists and evaluation counts; this is not a performance comparison |
| Fresh selected-policy and baseline replay | PASS: 208/208 executions match archived success, evaluation count, parameters and generators; zero process errors |
| Independent policy | 21/64 test successes; 0/32 at longer lengths |
| Iterative policy | 38/64 test successes; 6/32 at longer lengths |
| Supplementary program (now Algorithm 2) | 16/16 at n=9,11; 3/4 at each of n=13,15 |
| Initial program | 0/16 on the main test seeds |
| Clean-extraction test suite | 40 passed, 1 skipped (a SAT solver is required for the skipped known-code control) |
| Snapshot-default regression tests added after the clean-extraction check | 2 passed; default reproduces the frozen map, latest is an explicit override |
| Lint | PASS for scripts and tests |
| Paper build | PASS; the current manuscript compiles with nine research pages. The added appendix algorithm increases the total PDF length |
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
(model programs, complete latest-study records, codes, campaign records,
snapshots and certificates) remain byte-identical to the pre-cleanup snapshot.
The root archive manifest was refreshed only for anonymizing one historical log.
Raw originals, internal editorial notes and Git history remain recoverable in a
separate private archive. These local validation checks do not claim that the
remote CI jobs have run or that a public Git account/history is anonymous.

## Manuscript and README update, 2026-09-16

The revised paper explains how finite evolved constructions led to the general
family and distinguishes the proof from finite computational checks. Appendix B.3
now separates researcher proposals, tasks and evaluation feedback as native text.
Appendix C places Table 3 with its discussion and Algorithm 2 above the complete
longer-code outcomes. PDF rendering was checked on every appendix page: the paper
has nine research pages and 20 pages overall, without overfull boxes or unresolved
references. README links, figure paths and the family verification command were
checked against the repository.

The Python 3.12.12 deterministic tier passed again: 115 codes, 54 family gap
closures and 398 bound corrections. The study audit verified 235 saved records;
the table evidence map, archive manifest and lint checks also passed. These checks
did not generate new model proposals or rerun SAT/Magma.

The preceding remote workflow at commit `2194124` had two unresolved environment
issues: Python 3.9 cannot execute the study helper's `int.bit_count`, and the
macOS runner could not install the pinned Python 3.12.12 build. Its replay-artifact
upload also rejected a relative parent-directory path. The Python 3.12
deterministic job, external solver/checker job, historical replay, lint and
anonymous-release jobs passed. This documentation/layout update does not change
those workflow settings or the preserved experimental runtime.

## Lean certificate integration, 2026-09-16

All 13 supplied package files are preserved byte-identically in `formal/eaqecc/`.
The nine hashes in the supplied Linux verification record match the imported
proofs, definitions, challenge/solution files and configurations. Theorem 1 and
Lemma 2 import only their shared definitions, not each other's proof modules.

A fresh isolated build using Lean 4.29.0-rc6 and the lockfile's Mathlib commit
`1ea3462986d06c85c98fb18c10082274043405e4` passed on macOS arm64. Both proofs and
both submitted Solutions report only `propext`, `Classical.choice`, `Quot.sound`;
no `sorryAx` is present. The original lockfile was not updated. Build output and
a machine-readable result are preserved in `formal/eaqecc/verification/`.

At the September 16 integration, Linux Comparator evidence was limited to the
supplied verification excerpts; full raw logs and the historical CLI patch
were unavailable. The September 21 fresh replay below now supplies full logs
and a newly documented compatibility patch. Source-integrity/goal-pair checks
and a negative control that changes the formal goal pass locally. Appendix D
presents only Theorem 1, with explicit formalization scope; Lemma 2 remains
supporting codebase evidence. PDF rendering keeps nine research pages and
22 total pages. No new search or model-generation experiment was run.

## Title and figure alignment release, 2026-09-17

The paper, README and citation metadata use the title “Researcher-in-the-loop
Evolutionary Discovery of entanglement-assisted quantum code families”. Figure 1
stage headings are centered in their panels; Figure 3 field-size labels align
with the gray panel edges. Only figure geometry and editorial text changed.
The PDF retains nine main pages and 22 total pages; title and figure pages were
rendered and visually checked. The shortened AI use statement is included.

The protected archive manifest and Lean source audit pass. The latest-study
audit and table evidence mapping pass; five focused release/Lean tests and lint
pass. README file and image links resolve. This release does not claim a fresh
Lean, SAT/Magma or model-generation run.

## Fresh Linux Comparator replay, 2026-09-21

Both Theorem 1 and the supporting Lemma 2 passed Comparator and its Lean-kernel
replay on Linux x86_64. All thirteen original package files remain unchanged,
and all ten dependency revisions match the original lockfile. The full logs,
binary hashes, failed unpatched attempt and one-line landrun CLI repair are in
[the verification record](../formal/eaqecc/verification/linux-2026-09-21/README.md).
The patch inserts an argument separator before the sandboxed executable; no
exporter, comparison, axiom-policy or kernel-checking logic was changed. The
optional nanoda checker was not enabled. Private server addresses and raw
unredacted operational logs are excluded from Git.
