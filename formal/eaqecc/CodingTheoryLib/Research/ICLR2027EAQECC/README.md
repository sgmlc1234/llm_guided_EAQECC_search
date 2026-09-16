# ICLR 2027 EAQECC Lean certificate

The formalization is split into three independent layers:

- `Definitions.lean`: shared symplectic vocabulary and the normalizer-side certificate. It imports
  only Mathlib and contains no named theorem result.
- `Theorem1.lean`: the complete proof of Theorem 1. It imports `Definitions.lean`, but not
  `Lemma2.lean`.
- `Lemma2.lean`: the complete proof of Lemma 2. It imports `Definitions.lean`, but not
  `Theorem1.lean`.

The `Comparator` directory contains a separate Challenge, Solution, and JSON configuration for
each result. The Challenge imports only `Definitions.lean`; the Solution imports exactly the proof
module that it submits.

## Exact goals

`ICLR2027EAQECC.theorem1_exact` constructs `z₂` and nonzero `λ` under the paper's two field-size branches.
Its `NormalizerSideCertificate` proves generator injectivity, the restricted Gram formula, the exact
radical, actual finranks `q+2` and `q`, exact non-radical distance `n-1`, the resulting EAQECC
parameters, and BDH excess `q-2`.

`ICLR2027EAQECC.lemma2_coordinate_normalization` assumes `R ≤ L`, `dim L = dim R + 2`,
`dim R > 2`, and
non-radical symplectic weight at least `n-1`. It constructs coordinatewise local symplectic
equivalences that send all of `R` to Z-type.

## Local kernel builds

From the archive root:

```sh
lake exe cache get
lake build \
  CodingTheoryLib.Research.ICLR2027EAQECC.Definitions \
  CodingTheoryLib.Research.ICLR2027EAQECC.Theorem1 \
  CodingTheoryLib.Research.ICLR2027EAQECC.Lemma2

lake build \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Theorem1Challenge \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Theorem1Solution \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Lemma2Challenge \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Lemma2Solution
```

The only `sorry` declarations are the intentionally unproved statements in the two Challenge
files. The proof and Solution files contain no `private`, `sorry`, `admit`, or user-defined axiom.

## Comparator checks

With compatible `comparator`, `lean4export`, and `landrun` binaries in `PATH`:

```sh
lake env /path/to/comparator \
  CodingTheoryLib/Research/ICLR2027EAQECC/Comparator/Theorem1.json

lake env /path/to/comparator \
  CodingTheoryLib/Research/ICLR2027EAQECC/Comparator/Lemma2.json
```

Both configurations permit only `propext`, `Quot.sound`, and `Classical.choice`.

## Verified Linux runs

Both configurations were checked separately on 2026-09-16 in an isolated Ubuntu/aarch64 Lima VM
with Lean `4.29.0-rc6`, Comparator `v4.29.0-rc6` at commit
`a4f696825c583ed8a5b4060d9a0faa5b882d365b`, and lean4export at commit
`048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d`.

Theorem 1:

```text
Running Lean default kernel on solution.
Lean default kernel accepts the solution
Your solution is okay!
```

Lemma 2:

```text
Running Lean default kernel on solution.
Lean default kernel accepts the solution
Your solution is okay!
```

`landrun v0.1.17` consumes the child command's `--` separator. The verification environment used
the same lean4export source with only its CLI split restored after the single module argument; no
export, declaration, axiom-checking, or kernel logic was changed.

## Source hashes used in the Linux checks

```text
1b428a3a2f8a59f7e4e84e7d6ded1eba7ee087eeff04cd23d376e92eabf3eea4  Definitions.lean
0876587ffec57b030814434b923051fddace8d538569dcef21ae9c317d69df6b  Theorem1.lean
4a51c971dfb9441d96013fbdbee5c4656d60ae5eabea47107f42b403de8618fc  Lemma2.lean
9ffb404c963ab87ccfb6b4c6f4cd57e94e37f85479baba6092f9a12f653064dc  Comparator/Theorem1Challenge.lean
efa11a54cd267de3cf4847231a4e405b07905b1318a3b7d3a10acc3ba16240a4  Comparator/Theorem1Solution.lean
ee36db729fdb8a1514db95606a2c7b6666604ed4b41c64c6a0b28099035c073f  Comparator/Theorem1.json
79678f9ee9f3d8159d784c0c40852455edf881c8ccedcf0ba28c0c4b2f46a324  Comparator/Lemma2Challenge.lean
94a59d89cbbff5893b42ac1cd37e8de1b3ab31f15b9cab98e3879d3e77da763b  Comparator/Lemma2Solution.lean
d37f6eabe8e45667c4b98cdf9b9379c9a288875c0fd5cc8119c073fe92f98ea0  Comparator/Lemma2.json
```
