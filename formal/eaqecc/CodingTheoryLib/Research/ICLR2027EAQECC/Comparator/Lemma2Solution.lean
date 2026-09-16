import CodingTheoryLib.Research.ICLR2027EAQECC.Lemma2

set_option autoImplicit false
set_option backward.isDefEq.respectTransparency false

namespace ICLR2027EAQECC.Comparator

universe u

theorem lemma2_coordinate_normalization_goal
    {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (L R : Submodule 𝔽 (PauliVector 𝔽 ι)) (hRL : R ≤ L)
    (hdim : Module.finrank 𝔽 L = Module.finrank 𝔽 R + 2)
    (hRdim : 2 < Module.finrank 𝔽 R)
    (hdistance : ∀ v : L, v.1 ∉ R →
      Fintype.card ι - 1 ≤ symplecticWeight v.1) :
    IsLocallyZNormalizable R := by
  exact lemma2_coordinate_normalization L R hRL hdim hRdim hdistance

#print axioms lemma2_coordinate_normalization_goal

end ICLR2027EAQECC.Comparator
