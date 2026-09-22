# SAT/DRAT fresh verification — 2026-09-21

All ten archived CNFs returned UNSAT; all ten associated proofs passed drat-trim. Nine proofs were replayed from the archive. The on-demand proof for [[10,1,9;5]]₂ was generated afresh in binary DRAT format and checked. Source CNF hashes remained unchanged.

These are fresh macOS measurements, not recovered historical timings. Four performance workers ran concurrently, so wall times describe this run and are not isolated solver benchmarks. The nine decide-only timings exclude proof emission; the newly generated case includes it. Peak memory is the maximum resident set size from macOS `/usr/bin/time -l`. Proof size is uncompressed bytes.

| q,n,k,d,c | Variables | Clauses | Proof MiB | Decide / generate s | Check s | Solve RSS MiB | Check RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2,5,2,4,3 | 414 | 1,275 | 0.03 | 0.022 | 0.459 | 4.09 | 48.17 |
| 2,6,2,5,4 | 498 | 1,540 | 0.04 | 0.021 | 0.039 | 3.89 | 48.12 |
| 2,7,1,6,3 | 1,110 | 3,666 | 7.66 | 0.615 | 0.513 | 11.67 | 57.17 |
| 2,9,1,8,5 | 1,430 | 4,734 | 11.86 | 0.892 | 0.730 | 13.92 | 60.20 |
| 2,11,1,10,7 | 1,750 | 5,802 | 16.58 | 1.227 | 0.888 | 16.52 | 63.11 |
| 2,6,1,5,1 | 1,881 | 6,425 | 22.86 | 1.883 | 1.877 | 17.25 | 68.06 |
| 2,8,1,7,3 | 2,513 | 8,609 | 172.27 | 16.942 | 13.582 | 39.61 | 194.97 |
| 2,10,1,9,5 | 3,145 | 10,793 | 234.91 | 66.326 | 58.763 | 79.42 | 491.03 |
| 3,10,1,9,4 | 33,033 | 476,271 | 28.93 | 11.896 | 62.248 | 239.86 | 164.34 |
| 2,13,1,12,8 | 4,093 | 14,069 | 43.48 | 3.464 | 2.480 | 29.56 | 81.27 |

Pinned source revisions: CaDiCaL `7b99c07f0bcab5824a5a3ce62c7066554017f641`; drat-trim `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`. Binary hashes, exact commands, output logs, and resource logs are in `protocol.json` and `results.json`.

Large unpacked and regenerated proof files are retained in the local run archive. The nine original proofs remain in artifacts/refutations; the tenth is reproducible with the recorded generation command and pinned solver.
