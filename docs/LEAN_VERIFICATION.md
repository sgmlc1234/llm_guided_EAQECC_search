# Lean verification of Theorem 1

The formal artifact is in [`formal/eaqecc/`](../formal/eaqecc/README.md).
Appendix D presents only Theorem 1, the general construction derived from the
pipeline's mathematical discoveries. Lemma 2's independent Lean proof is kept
in the codebase as support for SAT normalization.

The original definitions, proof modules, separate Comparator challenges and
solutions, and pinned dependency files are preserved without edits. The source
manifest covers 13 supplied files. Exact goal and final proof-body excerpts in
the paper are generated from those files with:

```bash
python3 scripts/make_lean_excerpt.py
python3 scripts/audit_lean_certificate.py
```

The first command only typesets source excerpts; the second is an offline
integrity check. Neither claims a fresh Lean or Comparator execution.

A fresh macOS kernel build of both proofs and submitted Solutions passed with
Lean 4.29.0-rc6 and the supplied Mathlib commit. The supplied Linux Comparator
record reports accepted goal correspondence, axiom policy and default-kernel
checking. These are separate records: full Linux logs and the exact reported
exporter CLI patch were not part of the supplied package. Commands, tool revisions,
axiom dependencies and the precise formalization scope are in the artifact guide.
