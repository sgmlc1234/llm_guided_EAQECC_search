# Certificate for the qutrit exclusion

The archive excludes `[[10,1,9;4]]_3` using a coordinate-normalized
free-radical SAT encoding. Together with the archived `[[10,1,9;5]]_3`
witness and ebit lifting, this gives minimum entanglement 5 at `(n,k,d)=(10,1,9)`.

## Why the normalization is complete

Let `L` be the normalizer-side space and `R=rad(L)`. Assume `dim L=dim R+2`,
`dim R>2`, and every vector in `L\R` has symplectic weight at least `n-1`.
These conditions apply to the target above, whose radical dimension is 5.

Let `pi_i` project onto the two field components at coordinate `i`, and
`pi_ih` onto a pair of distinct coordinates. Any vector of `L` vanishing
at both coordinates must belong to `R`; otherwise its weight is at most
`n-2`. Consequently the kernels of `pi_ih` on `L` and `R` coincide.
Rank-nullity gives

```
dim pi_ih(L) - dim pi_ih(R) = dim L - dim R = 2.
```

The pair image is a subspace of `F_q^4`, so `dim pi_ih(R) <= 2`.
Suppose `dim pi_i(R)=2` for some `i`. For each `h != i`, the pair image
then has dimension 2 and projects isomorphically onto `pi_i(R)`.
Thus a radical vector vanishing at `i` vanishes at every coordinate.
This makes `pi_i` injective on `R`, contradicting `dim R>2`.
Every single-coordinate radical image therefore has dimension at most 1.

At each coordinate, a determinant-one linear map sends a nonzero radical
image line to the Z-axis; use the identity when the image is zero.
These local maps preserve the symplectic form and all supports. They make
every radical X component zero. Row reduction preserves those zeros,
so an RREF radical basis with this property exists for every possible code.
This is the coordinate-normalization lemma in the manuscript appendix.

This argument establishes completeness of the representative CNF. The DRAT
checker verifies that CNF's unsatisfiability; it does not check the lemma
or assert that the appended units are entailed by the unnormalized CNF.

## Released evidence

All files are under `artifacts/refutations/` with prefix `q3_n10_k1_c4_d9`:

- `.cnf`: 33,033 variables and 476,271 clauses.
- `.drat.gz`: compressed binary DRAT; 30,331,150 bytes before compression.
- `.checker.log`: independent DRAT-trim output with `s VERIFIED`.
- `.solver.log` and `.generation.json`: current UNSAT output and generation timing.
- `.normalization.json`: target, unit clauses and source/normalized SHA-256 hashes.
- `registry.json`: solver, checker timing and historical decision record.

The older `.log` file records the historical unnormalized decision; it is
retained as history and is not the current certificate-generation log.

The transformation appends 50 positive unit literals, one for each radical
X digit being zero, to the original 476,221-clause CNF. For zero-based
radical row `i` and coordinate `t`, the literal is `1 + 3*(20*i + 2*t)`.
The auditor removes this suffix and restores the original header to check
the recorded source hash. A regression test also regenerates the normalized
CNF byte for byte from the production encoder.

In the recorded generation run, CaDiCaL 3.0.0 took 14.2 seconds and DRAT-trim
took 84.8 seconds. Timing is environment-dependent. CaDiCaL was built from
commit `7b99c07f0bcab5824a5a3ce62c7066554017f641`; DRAT-trim from
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`.

## Regenerate and check

With CaDiCaL and DRAT-trim installed, run from the artifact root:

```bash
python3 scripts/refutations/sat_free_radical_q3.py 10 4 9 \
  --coordinate-normalize --binary-proof --proof --timeout 180 \
  --out /tmp/eaqecc_qutrit
```

The encoder returns 20 for UNSAT, following the solver convention. Then run:

```bash
drat-trim /tmp/eaqecc_qutrit/q3_n10_k1_c4_d9.cnf \
  /tmp/eaqecc_qutrit/q3_n10_k1_c4_d9.drat
python3 scripts/reproduce_eaqecc.py --claim refutations
```

`CADICAL_PATH` and `DRAT_TRIM_PATH` can specify tool paths. Supply
`EAQECC_PROOF_CACHE` as documented in README.md to include the separate large
qubit proof. Missing tools or that cache produce a partial full-registry audit.

The positive-control test fixes the normalized `(10,1,9;5)` encoding to an
existing archived witness and requires a real SAT solver to return SAT.
This checks that the implementation accepts a known code; it is not a
substitute for the completeness proof.

```bash
python3 -m pytest tests/test_qutrit_normalization.py
```
