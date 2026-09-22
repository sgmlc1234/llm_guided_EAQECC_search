# Selected-source review

All 16 sources maintain and mutate L and convert it to S for the charged exact evaluator.

No selected source enumerates logical weights or calls a private distance evaluator.

The only E helper calls are evaluate, nullspace, _J and gf2_basis.

Incumbent access before the first search evaluation receives None because protected initialization is disabled.

b05_evolution_g05 changes the basis without evaluating the unchanged subspace; this is not a hidden candidate-distance test.

Sources are preserved without repairs, including ineffective or redundant search operations.

Hashes and program identifiers are in SOURCE_REVIEW.json. The offline audit reconstructs prompts, parentage and selection separately; source review alone does not establish performance or a causal effect of an individual edit.
