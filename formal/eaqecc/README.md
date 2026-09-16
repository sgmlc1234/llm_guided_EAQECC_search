# Lean certificates for the EAQECC paper

Theorem 1 is the paper's formalized discovery result. Its exact goal and solution
are presented in Appendix D. Lemma 2 is retained here as supporting verification
for the SAT normalization; it is not an additional pipeline-discovery claim.
The two proof modules independently import the shared definitions.

The supplied package is preserved byte for byte, including its lockfile and
[original verification record](CodingTheoryLib/Research/ICLR2027EAQECC/README.md).
`SOURCE_MANIFEST.sha256` covers those 13 original files. Repository integration
adds this guide and the separate `verification/` records.

## Files

| File under `CodingTheoryLib/Research/ICLR2027EAQECC/` | Purpose |
|---|---|
| `Definitions.lean` | Pauli vectors, symplectic product/weight, the concrete construction and certificate type |
| `Theorem1.lean` | General construction proof, including `theorem1_exact` |
| `Lemma2.lean` | Independent coordinate-normalization proof retained for completeness |
| `Comparator/Theorem1Challenge.lean` | Statement-only trusted target |
| `Comparator/Theorem1Solution.lean` | Same declaration, proved by `theorem1_exact` |
| `Comparator/Theorem1.json` | Permitted axioms and comparator settings |
| Corresponding `Lemma2` files | Supporting result's independent goal and solution |

The `sorry` in each Challenge file deliberately leaves the target unproved.
Challenge modules are not imported by the proofs or submitted Solutions. Kernel
builds of the Solutions report only `propext`, `Classical.choice` and `Quot.sound`.

## Check the preserved package without Lean

From the repository root:

```bash
python3 scripts/audit_lean_certificate.py
```

This checks source hashes, the two exact goal texts and the Comparator settings.
It does not execute Lean or Comparator.

## Rebuild with the pinned Lean toolchain

Install [elan](https://github.com/leanprover/elan), then run from this directory:

```bash
lake exe cache get
lake build \
  CodingTheoryLib.Research.ICLR2027EAQECC.Definitions \
  CodingTheoryLib.Research.ICLR2027EAQECC.Theorem1 \
  CodingTheoryLib.Research.ICLR2027EAQECC.Lemma2 \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Theorem1Solution \
  CodingTheoryLib.Research.ICLR2027EAQECC.Comparator.Lemma2Solution
```

Lean is pinned to `4.29.0-rc6`; Mathlib is locked to
`1ea3462986d06c85c98fb18c10082274043405e4`. Preserve `lake-manifest.json` and do not
run `lake update`: the supplied lakefile's tag differs from the manifest's
recorded input reference, and Lake may warn that the manifest is out of date.
The replay uses the lockfile's exact commit. Build caches remain in `.lake/`
and are excluded from Git and the anonymous release.

## Verification status

- **Fresh kernel replay:** PASS on macOS arm64 with the pinned Lean and Mathlib.
  See [JSON record](verification/kernel-build-macos.json) and
  [build output](verification/kernel-build-macos.log). Both proof modules and
  both submitted Solutions build; no `sorryAx` occurs in their dependencies.
- **Supplied Linux Comparator record:** the original package README records
  acceptance of both separate challenges on Ubuntu/aarch64, using Comparator
  `a4f696825c583ed8a5b4060d9a0faa5b882d365b` and lean4export
  `048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d`. This integration did not rerun Linux
  Comparator; the original package contains output excerpts rather than full
  raw run logs. Its configurations disable the optional nanoda checker.

Comparator requires Linux `landrun` and compatible `comparator` and `lean4export`
binaries. The original record documents a CLI adjustment because landrun 0.1.17
consumed the separator after the module argument; it states that export and
kernel logic were unchanged. The exact original patch is not supplied. Preserve
and document this adjustment when reproducing that Linux run; the pinned
[exporter CLI](https://github.com/leanprover/lean4export/blob/048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d/Main.lean)
parses module names before `--` and declaration names after it.

With those compatible binaries available, from this directory run:

```bash
lake env comparator CodingTheoryLib/Research/ICLR2027EAQECC/Comparator/Theorem1.json
lake env comparator CodingTheoryLib/Research/ICLR2027EAQECC/Comparator/Lemma2.json
```

## Mathematical scope

The proof-bearing certificate fields establish an injective generator map,
nonzero restricted Gram entry, Gram formula, radical condition, finranks and
exact non-radical distance. The displayed parameter record, dimension labels
and BDH excess are default data fields, not separate proofs connecting those
labels to quantum-code semantics. Appendix D explains the coding-theoretic
interpretation using the standard stabilizer correspondence. The distinguished
lambda coordinate is first in the formal tail and last in the displayed paper
construction; a coordinate permutation relates these conventions.
