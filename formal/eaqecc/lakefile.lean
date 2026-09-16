import Lake
open Lake DSL

package CodingTheoryLib where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "v4.29.0-rc6"

require repl from git
  "https://github.com/leanprover-community/repl.git" @ "v4.29.0-rc6"

@[default_target]
lean_lib CodingTheoryLib where
  srcDir := "."

/-- Sorried statement-only modules consumed by Comparator, not a default build
target and never imported by the trusted library. -/
lean_lib ComparatorChallenges where
  srcDir := "."
