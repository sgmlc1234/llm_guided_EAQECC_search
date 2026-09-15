# EAQECC reproduction report

Snapshot: `2026-07-17` (available: 2026-07-17, 2026-09-10)  ·  Python 3.12.12  ·  Overall: **PASS**

| Claim | Tier | Status | Detail |
|---|---|---|---|
| `archive-integrity` | deterministic | PASS | 310 archived files listed; 0 missing, 0 altered, 0 present but unlisted |
| `witnesses` | deterministic | PASS | 115 archived witnesses re-derived (q=2: 65, q=3: 27, q=4: 13, q=5: 10); 0 mismatches |
| `families` | deterministic | PASS | q2: rc=0 All checks passed.; unified: rc=0 All checks passed.; families settle 54 listed-open cells (q=2: 29, q=3: 25) in 2026-07-17 |
| `table-correction` | deterministic | PASS | 398 corrected upper bounds recomputed from the 2026-07-17 snapshot; 0 disagree |
| `solver-refinement` | deterministic | PASS | two refinement witnesses independently re-derived; distance 9 matches EA-Plotkin, distance 11 links to the archived d>=12 certificate (fresh replay is reported by refutations) |
| `openness` | deterministic | PASS | 65 q=2 witness files: 9 listed-and-open, 56 absent; 61 unique cells (8 listed, 53 absent) in 2026-07-17; 0 were not open (q=3 witnesses: 15 listed-and-open, 11 absent, 1 not open) |
| `novelty-drift` | deterministic | PASS | 2026-07-17 -> 2026-09-10: q=2,3 comparison; 0 changed bounds; 0 witness cells newly matched by listed bounds; independent discovery is not inferred from a table update |
| `refutations` | external | PASS | 9 CNF/proof pairs, 1 on-demand proof, 0 decision-only record; 10/10 CNFs re-decided UNSAT; 10/10 available certificates replayed; unperformed checks are listed per entry |
| `magma-crosscheck` | external | PASS | re-ran Magma over SSH: 148/148 records verified, 0 mismatches |
| `search-determinism` | search | PASS | 12 seeded searches re-run at 5000 evaluations (B0, B1f, B2); 0 differ from the stored proposal lists |
| `prompt-provenance` | deterministic | PASS | 4 archived task specifications; campaigns 1-2 share one text; campaign 1 offers the cyclic-shift symmetry ansatz as a direction, campaign 3 states the finding |
