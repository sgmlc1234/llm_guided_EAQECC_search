# Binary normalization replay

All seven normalized binary exclusions are UNSAT with independently checked DRAT proofs. The feasible [[6,1,5;2]]2 positive control remains SAT, and its decoded generators pass the independent matrix checker.

The original CNFs and proofs in the parent artifact directory remain unchanged. Each new CNF is the byte-identical rebuilt original plus only the recorded radical-X unit clauses, omitting units already present. Lemma 2 justifies completeness for k=1, d=n-1 and radical dimension greater than two.

| n | c | Added units | Proof MiB | Solver s | Check s |
|---:|---:|---:|---:|---:|---:|
| 6 | 1 | 18 | 1.217 | 0.229 | 0.249 |
| 7 | 3 | 14 | 0.334 | 0.071 | 0.067 |
| 8 | 3 | 24 | 3.185 | 0.597 | 0.633 |
| 9 | 5 | 18 | 1.298 | 0.237 | 0.172 |
| 10 | 5 | 30 | 10.973 | 2.329 | 2.338 |
| 11 | 7 | 22 | 2.312 | 0.366 | 0.220 |
| 13 | 8 | 39 | 49.538 | 11.883 | 13.363 |

Timings include this run only; no matched speed comparison with the historical runs is claimed. All steps finished within the approved 600-second and 1-GB limits. Proofs are stored as deterministic gzip files; results.json records both uncompressed and compressed hashes.

To reproduce in a new directory, from the repository root:

```sh
python scripts/refutations/replay_binary_normalization.py --solver /path/to/cadical --checker /path/to/drat-trim --out /new/output/directory
```

The script has no paid-service dependencies. Supply the externally installed CaDiCaL and DRAT-trim binaries described in docs/EXTERNAL_VERIFICATION.md. To recheck a saved proof, decompress the corresponding .drat.gz into a temporary file and run DRAT-trim with the adjacent .cnf and that temporary proof.
