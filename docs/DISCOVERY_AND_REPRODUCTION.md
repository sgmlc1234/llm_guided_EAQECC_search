# Discovery stages and reproducible outputs

The pipeline produces mathematical constructions, a general theorem, and executable search programs. These have different supporting records.

| Stage | Evidence | What can be checked |
|---|---|---|
| Initial qubit discovery | Early campaign logs and code matrices; `artifacts/campaigns/prompts/campaign1.txt` | The initial instructions suggest construction directions without supplying the later family formula. The logs record finite qubit discoveries. |
| Researcher generalization | Later task `campaign3.txt`, Appendix A.2 and the general-family implementations | The later task explicitly records the researcher-derived qubit family. The paper extends it to prime powers and proves the parameter formula. |
| Formal checking | `formal/eaqecc/`, Appendix D | The coefficient map, Gram/radical structure, dimensions and distance are checked in Lean. The paper supplies the standard stabilizer interpretation. |
| Later program evolution | Algorithm 1 and `artifacts/campaigns/run9_top_programs/rank05_1001000.py` | This retained program builds on the family-informed campaign seed. It is not identified as the source of every early discovery. |
| Complementary finite-field search | `artifacts/construction_provenance/nonbinary/` | q=4,5 matrices, archived annealing routines, target-level logs and a fresh identical replay; all 23 matrices have the verified fixed-pair form. |
| Fixed-program replay | `scripts/eaqecc_baselines/search_fingerprint.json` | The original twelve-list determinism record covers B0, B1f and B2 on four seeds each. B2 is rank01, not the Algorithm 1 program. Algorithm 1 has a separate execution command in the reviewer guide. |
| Controlled generation and reevaluation | `experiments/hitl_ablation/` and `experiments/hitl_followup/` | Preserved proposals, parent relationships, validation selection, fixed-program outcomes and independently checked matrices. |

Recomputing code parameters, constructing a family instance and rerunning preserved program bytes are reproducible operations. The mathematical proof establishes the whole admissible family. Campaign event logs document discovery history, but do not pair every initial finding with a surviving source file. The preserved source replay is not relabeled as the original model-sampling trajectory.

## Two evaluation roles in the construction campaign

Inside a candidate program, `E.evaluate` computes exact parameters of intermediate matrices. The program uses them in its own search decisions. Algorithm 1 minimizes `5000*abs(c-c_target) + 1000*abs(k-k_target) + offending`, with a large cost for an evaluator error.

After execution, `scripts/alphaevolve_eaqecc/evaluate.py` re-evaluates each returned matrix in the controller. A matching signature scores `1000-offending`, with a `10^6` bonus for a target newly achieved in the archive. A mismatch scores `-5000*abs(c-c_target)-1000`. The best proposal score becomes the program's evolutionary feedback. Both stages use the exact parameter implementation, while the Magma stage recomputes from exported bases using a separate implementation. Parameter validity and improvement against the reference bounds are checked separately.

These campaign scores are distinct from the normalized success-curve utility in the controlled study. Its call quotas and program-selection rules are specified in the study protocol and Appendix C.

## Exact evaluator scope and computational cost

Let `s = n-k+c` be the generator-space dimension and `r = 2n-s = n+k-c`
the dual dimension. The dual has `q^r` vectors; `q^(n-k-c)` belong to the
radical. Exact distance is the minimum weight among the remaining vectors.
The representation being mutated does not change these dimensions for a
fixed target signature. Invalid intermediate candidates can have different
ranks or parameters and must be evaluated at their actual signature.

The preserved implementations have different enumeration workloads:

| Implementation | Enumerated spaces | Binary dual-dimension cap |
|---|---|---:|
| Historical `scripts/alphaevolve_eaqecc/helpers_eaqecc.py` | Both S and its dual, then filter S by orthogonality | 22 |
| Controlled `experiments/hitl_ablation/runtime/controlled_helpers.py` | Dual and radical; obtain the radical from the Gram kernel | 20 |

The historical implementation processes `2^s + 2^r` vectors before filtering;
the cap on `r` alone does not bound all of its work. The controlled implementation
avoids enumerating S. These counts describe enumerated vectors, not a complete
runtime complexity bound: linear algebra, orthogonality tests, membership,
weight computation and matrix width also contribute.

The historical helper's preserved docstring says `2^20`, but its executable
cutoff is **22**. The original 68-target list has dual dimensions 4–20.
The separate, residual 309-cell list has dimensions 5–22, including three
cells above 20. The source is retained unchanged for faithful replay; this
note corrects its stale description. The later campaign task's 329-cell count
refers to an earlier stage, not the residual file.

The 115 core code records have the following signatures:

| q | Codes | Dual dimensions | Largest dual | Codes with k > 1 |
|---|---:|---:|---:|---:|
| 2 | 65 | 4–13 | 8,192 | 29 (k = 2–6) |
| 3 | 27 | 4–6 | 729 | 0 |
| 4 | 13 | 4–7 | 16,384 | 0 |
| 5 | 10 | 4–8 | 390,625 | 0 |

These are retained-code counts, not proposal counts or results attributable
to one search method. The general family has `r=q+2`, independent of length
at fixed q. All four binary ablation lengths (9, 11, 13, 15) have `r=4`:
16 dual vectors, 4 radical vectors and 12 non-radical vectors. The improvement
in this implementation removes unnecessary generator-space enumeration;
it does not approximate the distance oracle.

A differential check on 22 September 2026 evaluated 54 full-rank matrices,
covering every nonzero rank at lengths 2–7, with both preserved implementations.
All shared outputs (`n,s,c,iso,k,d,offending`) agreed. This is a finite regression
check, not a proof of equivalence or a timing benchmark. Existing code and
Magma verification records provide the checks of reported constructions.

The [scope inventory](../artifacts/evaluator_audit/2026-09-22/evaluation_scope.json)
records all 115 code paths, hashes and dimensions. The
[differential-check receipt](../artifacts/evaluator_audit/2026-09-22/oracle_equivalence.json)
records evaluator source hashes, all 54 input generator lists and their outputs.
