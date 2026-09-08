# EAQECC reproduction report

Snapshot: `2026-07-17` (available: 2026-07-17)  ·  Python 3.12.12  ·  Overall: **PASS**

| Claim | Tier | Status | Detail |
|---|---|---|---|
| `archive-integrity` | deterministic | PASS | 227 archived files listed; 0 missing, 0 altered, 0 present but unlisted |
| `witnesses` | deterministic | PASS | 114 archived witnesses re-derived (q=2: 64, q=3: 27, q=4: 13, q=5: 10); 0 mismatches |
| `families` | deterministic | PASS | q2: rc=0 All checks passed.; unified: rc=0 All checks passed.; families settle 54 listed-open cells (q=2: 29, q=3: 25) in 2026-07-17 |
| `table-correction` | deterministic | PASS | 398 corrected upper bounds recomputed from the 2026-07-17 snapshot; 0 disagree |
| `openness` | deterministic | PASS | 8 closed q=2 cells were listed-and-open and 56 were absent from the table in 2026-07-17; 0 were not open (q=3 witnesses: 15 listed-and-open, 11 absent, 1 not open) |
| `novelty-drift` | deterministic | SKIPPED_NO_DATA | only 1 snapshot(s) present (2026-07-17); add a newer dated directory to measure drift |
| `refutations` | external | PASS | 7 certified (CNF + DRAT shipped), 1 certified on demand (CNF shipped, proof regenerable), 1 solver decisions on record only [q3_n10_k1_c4_d9]; 8/8 CNFs re-decided UNSAT; no DRAT checker (drat-trim) found, proofs not replayed |
| `magma-crosscheck` | external | SKIPPED_NO_TOOL | no Magma binary on PATH; read the archived log instead (evidence we ran it, not a reproduction): 122 of 122 exported records verified, 0 mismatches [Magma V2.28-20 (verified via GetVersion on magma-lab, 2026-08-14)] |
| `search-determinism` | search | PASS | 12 seeded searches re-run at 5000 evaluations (B0, B1f, B2); 0 differ from the stored proposal lists |
