import CodingTheoryLib.Research.ICLR2027EAQECC.Theorem1

set_option autoImplicit false
set_option backward.isDefEq.respectTransparency false

namespace ICLR2027EAQECC.Comparator

universe u

theorem theorem1_exact_goal
    {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail]
    (hcase : 3 ≤ Fintype.card 𝔽 ∨
      (Fintype.card 𝔽 = 2 ∧ Odd (2 * Fintype.card 𝔽 + tail))) :
    ∃ z₂ lam : 𝔽, lam ≠ 0 ∧ 1 + z₂ ≠ 0 ∧
      Nonempty (NormalizerSideCertificate 𝔽 tail z₂ lam) := by
  exact theorem1_exact hcase

#print axioms theorem1_exact_goal

end ICLR2027EAQECC.Comparator
