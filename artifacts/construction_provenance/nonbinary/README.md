# Nonbinary construction provenance

The 13 archived q=4 codes and ten q=5 codes belong to complementary finite-field simulated-annealing searches. They are separate from the managed qubit evolution campaigns. The preserved matrices all have j=n−1−c fixed, disjoint Z-pair rows followed by two variable vectors. The routines mutate those two vectors and count low-weight non-radical combinations by exact finite-field enumeration. Rank and nonzero-pairing checks prune proposals; a final parameter check validates k,c,d before saving.

All 23 archived JSON files match their original search-directory files byte for byte. Historical success logs match 22 parameter tuples. For the remaining [[8,1,7;5]]₄ file, a fresh execution of the preserved q=4 routine reproduced the entire archived JSON file byte for byte in approximately 0.17 seconds. This is a new replay, not a recovered historical log. The source scripts and logs are preserved unchanged; the registry provides hashes and mappings. Source chronology for individual historical runs is not inferred from filenames.

The scripts call fixed rows radical generators in comments, but they do not explicitly enforce all of their pairings on every intermediate proposal. Successful distance-(n−1) outputs force each fixed weight-two row into the radical. The structural audit verifies this property for all archived matrices, along with independence and the final nonzero pairing. It is separate from exact-distance verification in the main artifact audit and the archived independent Magma check.

`sa_gamma4.py` is specialized to q=4. `sa_gammaq.py` retains an old q=4 header, but reads the `GQ` environment variable to choose q=4 or q=5. Its evaluation uses chunked enumeration. Historical log lines saying `floor>=` after an unsuccessful search are search observations, not certified nonexistence bounds; use only the separately checked refutations as exclusions.

## Inspect

From the repository root:

```bash
python3 scripts/audit_nonbinary_provenance.py
```

## Optional bounded search replay

Use an empty output directory so no archived files are overwritten. Copy the three preserved Python files into a `scripts/` directory there. With NumPy available, from that directory run:

```bash
python3 scripts/sa_gamma4.py 8 5 30
```

This searches for 30 seconds at most, followed by the final parameter check when successful, and writes `artifacts/gamma4/SOLUTION4_n8_k1_c5_d7.json`. The saved seed is determined by the target. The supplied fresh replay used Python 3.12.12 and NumPy 2.5.1. Recorded wall time is a run observation, not a timing guarantee. The q-ary routine uses `GQ=4` or `GQ=5` with the same arguments; general wall-clock searches are distinct from the virtual-clock binary program replay.
