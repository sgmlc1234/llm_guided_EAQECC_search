import CodingTheoryLib.Research.ICLR2027EAQECC.Definitions

/-!
# Standalone verification of Theorem 1

This file formalizes Theorem 1 from Appendix A.2 of
`ICLR2027_EAQECC_v12_B.pdf`.  Apart from its companion definitions module, its dependency closure
imports only Mathlib: no declaration from the library's `core` is used.  The small amount of
reusable symplectic infrastructure was copied into that companion module so that the certificate
can be checked in isolation and shared with the trusted Theorem 1 Comparator challenge.

The paper's phrase “normalizer side of an EAQECC” is represented by
`NormalizerSideCertificate`: it records the non-radical quotient dimension, the radical
dimension, the symplectic rank, the exact minimum symplectic weight, and the resulting
`[[n,k,d;c]]` parameters.  Thus the formal statement exposes, rather than hides, the parameter
calculation used by the stabilizer construction.
-/

open BigOperators

namespace ICLR2027EAQECC

universe u

/-- If a word has at most one zero coordinate, its symplectic weight is at least `n-1`. -/
lemma weight_ge_card_sub_one_of_unique_zero
    {𝔽 : Type u} [Zero 𝔽] {ι : Type*} [Fintype ι] [DecidableEq ι] [DecidableEq 𝔽]
    (x : PauliVector 𝔽 ι)
    (hzero : ∀ i j, x i = 0 → x j = 0 → i = j) :
    Fintype.card ι - 1 ≤ symplecticWeight x := by
  classical
  let Z : Finset ι := Finset.univ.filter fun i => x i = 0
  have hZ : Z.card ≤ 1 := by
    rw [Finset.card_le_one]
    intro i hi j hj
    exact hzero i j (Finset.mem_filter.mp hi).2 (Finset.mem_filter.mp hj).2
  have hpartition : symplecticWeight x + Z.card = Fintype.card ι := by
    rw [symplecticWeight, ← Finset.card_union_of_disjoint]
    · congr 1
      ext i
      by_cases hi : x i = 0 <;> simp [Z, hi]
    · simp [Finset.disjoint_left, Z]
  omega

/-- If a word has exactly one zero coordinate, its weight is exactly `n-1`. -/
lemma weight_eq_card_sub_one_of_unique_zero
    {𝔽 : Type u} [Zero 𝔽] {ι : Type*} [Fintype ι] [DecidableEq ι] [DecidableEq 𝔽]
    (x : PauliVector 𝔽 ι) (i₀ : ι) (hi₀ : x i₀ = 0)
    (hzero : ∀ i j, x i = 0 → x j = 0 → i = j) :
    symplecticWeight x = Fintype.card ι - 1 := by
  classical
  let Z : Finset ι := Finset.univ.filter fun i => x i = 0
  have hZ : Z = {i₀} := by
    ext i
    simp only [Z, Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_singleton]
    constructor
    · intro hi
      exact hzero i i₀ hi hi₀
    · intro hi
      simpa [hi] using hi₀
  have hpartition : symplecticWeight x + Z.card = Fintype.card ι := by
    rw [symplecticWeight, ← Finset.card_union_of_disjoint]
    · congr 1
      ext i
      by_cases hi : x i = 0 <;> simp [Z, hi]
    · simp [Finset.disjoint_left, Z]
  rw [hZ] at hpartition
  simp only [Finset.card_singleton] at hpartition
  omega

/-! ## The closed-form family (Theorem 1) -/

@[simp] lemma closedWord_pair_false {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (c : ClosedCoeff 𝔽) (u : 𝔽) :
    closedWord (tail := tail) z₂ lam c (Sum.inl (u, false)) =
      (c.1 + c.2.1 * u, c.2.1 + c.2.2 u) := rfl

@[simp] lemma closedWord_pair_true {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (c : ClosedCoeff 𝔽) (u : 𝔽) :
    closedWord (tail := tail) z₂ lam c (Sum.inl (u, true)) =
      (c.1 + c.2.1 * u, c.2.1 * z₂ - c.2.2 u) := rfl

@[simp] lemma closedWord_tail_zero {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (c : ClosedCoeff 𝔽) :
    closedWord (tail := tail) z₂ lam c (Sum.inr 0) = (c.1, c.2.1 * lam) := by
  simp [closedWord]

/-- The displayed generators are independent. -/
lemma closedWord_injective {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) :
    Function.Injective (closedWord (tail := tail) z₂ lam) := by
  intro c d hcd
  have htail := congrFun hcd (Sum.inr (0 : Fin tail))
  simp only [closedWord_tail_zero, Prod.mk.injEq] at htail
  have hα : c.1 = d.1 := htail.1
  have hβ : c.2.1 = d.2.1 := by
    exact mul_right_cancel₀ hlam htail.2
  apply Prod.ext hα
  apply Prod.ext hβ
  funext u
  have hp := congrFun hcd (Sum.inl (u, false))
  simp only [closedWord_pair_false, Prod.mk.injEq] at hp
  simpa [hα, hβ] using hp.2

/-- The radical coefficient space is canonically the `q`-dimensional function space `𝔽 → 𝔽`. -/
def closedRadicalEquiv {𝔽 : Type u} [Field 𝔽] :
    closedRadicalCoefficients 𝔽 ≃ₗ[𝔽] (𝔽 → 𝔽) where
  toFun c := c.1.2.2
  invFun t := ⟨(0, 0, t), by simp [closedRadicalCoefficients, IsRadicalCoeff]⟩
  left_inv c := by
    apply Subtype.ext
    rcases c with ⟨⟨α, β, t⟩, hc⟩
    rcases hc with ⟨hα, hβ⟩
    change α = 0 at hα
    change β = 0 at hβ
    change (0, 0, t) = (α, β, t)
    rw [hα, hβ]
  right_inv _ := rfl
  map_add' _ _ := rfl
  map_smul' _ _ := rfl

/-- The displayed normalizer has the claimed dimension `q+2`. -/
lemma closedNormalizer_finrank {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) :
    Module.finrank 𝔽 (closedNormalizer (tail := tail) z₂ lam) = Fintype.card 𝔽 + 2 := by
  rw [closedNormalizer, LinearMap.finrank_range_of_inj]
  · simp [ClosedCoeff, Module.finrank_fintype_fun_eq_card]
    omega
  · simpa [closedWordLinearMap] using closedWord_injective z₂ lam hlam

/-- The displayed radical coefficient space has the claimed dimension `q`. -/
lemma closedRadicalCoefficients_finrank {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] :
    Module.finrank 𝔽 (closedRadicalCoefficients 𝔽) = Fintype.card 𝔽 := by
  rw [closedRadicalEquiv.finrank_eq]
  exact Module.finrank_fintype_fun_eq_card 𝔽

/-- The Gram entry is `(n-1)·1 + λ`; the `2q` contribution vanishes in `𝔽`. -/
lemma closedDelta_eq_cast_length_sub_one_add
    {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) :
    closedDelta (tail := tail) z₂ lam =
      ((2 * Fintype.card 𝔽 + tail - 1 : ℕ) : 𝔽) + lam := by
  classical
  cases tail with
  | zero => exact (NeZero.ne 0 rfl).elim
  | succ m =>
      simp [closedDelta, symplecticProduct, closedWord, aCoeff, bCoeff,
        Fintype.sum_sum_type, Fintype.sum_prod_type, Fintype.sum_bool,
        Fin.sum_univ_succ, Nat.cast_card_eq_zero]
      push_cast
      ring

/-- The restricted Gram form has one alternating `2 × 2` block. -/
lemma closedWord_symplecticProduct
    {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (c d : ClosedCoeff 𝔽) :
    symplecticProduct (closedWord (tail := tail) z₂ lam c)
        (closedWord (tail := tail) z₂ lam d) =
      (c.1 * d.2.1 - c.2.1 * d.1) * closedDelta (tail := tail) z₂ lam := by
  classical
  let pairingTerm (e f : ClosedCoeff 𝔽) (k : ClosedCoord 𝔽 tail) : 𝔽 :=
    (closedWord z₂ lam e k).1 * (closedWord z₂ lam f k).2 -
      (closedWord z₂ lam e k).2 * (closedWord z₂ lam f k).1
  change (∑ k, pairingTerm c d k) =
    (c.1 * d.2.1 - c.2.1 * d.1) *
      ∑ k, pairingTerm (aCoeff (𝔽 := 𝔽)) (bCoeff (𝔽 := 𝔽)) k
  have hpair : (∑ ub : 𝔽 × Bool, pairingTerm c d (Sum.inl ub)) =
      (c.1 * d.2.1 - c.2.1 * d.1) *
        ∑ ub : 𝔽 × Bool,
          pairingTerm (aCoeff (𝔽 := 𝔽)) (bCoeff (𝔽 := 𝔽)) (Sum.inl ub) := by
    simp only [Fintype.sum_prod_type, Fintype.sum_bool, Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro u _
    simp [pairingTerm, closedWord, aCoeff, bCoeff]
    ring
  have htail : (∑ j : Fin tail, pairingTerm c d (Sum.inr j)) =
      (c.1 * d.2.1 - c.2.1 * d.1) *
        ∑ j : Fin tail,
          pairingTerm (aCoeff (𝔽 := 𝔽)) (bCoeff (𝔽 := 𝔽)) (Sum.inr j) := by
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro j _
    simp only [pairingTerm, closedWord, aCoeff, bCoeff]
    split_ifs <;> simp <;> ring
  simp only [Fintype.sum_sum_type]
  rw [hpair, htail]
  ring

/-- If the Gram entry is nonzero, the radical is exactly `α=β=0`. -/
lemma closedWord_radical_iff
    {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽)
    (hδ : closedDelta (tail := tail) z₂ lam ≠ 0) (c : ClosedCoeff 𝔽) :
    (∀ d : ClosedCoeff 𝔽,
      symplecticProduct (closedWord (tail := tail) z₂ lam c)
        (closedWord (tail := tail) z₂ lam d) = 0) ↔ IsRadicalCoeff c := by
  constructor
  · intro h
    have ha := h (aCoeff (𝔽 := 𝔽))
    have hb := h (bCoeff (𝔽 := 𝔽))
    rw [closedWord_symplecticProduct] at ha hb
    simp only [aCoeff, bCoeff, mul_one, mul_zero, sub_zero, zero_mul, zero_sub] at ha hb
    exact ⟨(mul_eq_zero.mp hb).resolve_right hδ,
      neg_eq_zero.mp ((mul_eq_zero.mp ha).resolve_right hδ)⟩
  · rintro ⟨hα, hβ⟩ d
    rw [closedWord_symplecticProduct, hα, hβ]
    simp

/-- A non-radical closed-form word has at most one zero coordinate. -/
lemma closedWord_unique_zero {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) (hz₂ : 1 + z₂ ≠ 0)
    (c : ClosedCoeff 𝔽) (hc : ¬ IsRadicalCoeff c) :
    ∀ i j, closedWord (tail := tail) z₂ lam c i = 0 →
      closedWord (tail := tail) z₂ lam c j = 0 → i = j := by
  have zero_data : ∀ k, closedWord (tail := tail) z₂ lam c k = 0 →
      c.2.1 ≠ 0 ∧ ∃ b : Bool, k = Sum.inl (-c.1 / c.2.1, b) := by
    intro k hk
    cases k with
    | inl ub =>
        rcases ub with ⟨u, b⟩
        have hx : c.1 + c.2.1 * u = 0 := by
          cases b <;> simpa [closedWord] using congrArg Prod.fst hk
        have hβ : c.2.1 ≠ 0 := by
          intro hβ
          have hα : c.1 = 0 := by simpa [hβ] using hx
          exact hc ⟨hα, hβ⟩
        refine ⟨hβ, b, ?_⟩
        congr 2
        rw [eq_div_iff hβ]
        linear_combination hx
    | inr k =>
        have hα : c.1 = 0 := by
          simpa [closedWord] using congrArg Prod.fst hk
        have hz : (if k = 0 then lam else 1) ≠ 0 := by
          split_ifs <;> simp_all
        have hβ : c.2.1 = 0 := by
          have := congrArg Prod.snd hk
          simp only [closedWord, Prod.snd_zero] at this
          exact (mul_eq_zero.mp this).resolve_right hz
        exact (hc ⟨hα, hβ⟩).elim
  intro i j hi hj
  rcases zero_data i hi with ⟨hβ, b, rfl⟩
  rcases zero_data j hj with ⟨_, b', rfl⟩
  congr 2
  cases b <;> cases b'
  · rfl
  · exfalso
    have hz0 := congrArg Prod.snd hi
    have hz1 := congrArg Prod.snd hj
    simp only [closedWord_pair_false, closedWord_pair_true, Prod.snd_zero] at hz0 hz1
    apply hz₂
    apply (mul_eq_zero.mp ?_).resolve_left hβ
    calc
      c.2.1 * (1 + z₂) =
          (c.2.1 + c.2.2 (-c.1 / c.2.1)) +
            (c.2.1 * z₂ - c.2.2 (-c.1 / c.2.1)) := by ring
      _ = 0 := by rw [hz0, hz1, zero_add]
  · exfalso
    have hz1 := congrArg Prod.snd hi
    have hz0 := congrArg Prod.snd hj
    simp only [closedWord_pair_false, closedWord_pair_true, Prod.snd_zero] at hz0 hz1
    apply hz₂
    apply (mul_eq_zero.mp ?_).resolve_left hβ
    calc
      c.2.1 * (1 + z₂) =
          (c.2.1 + c.2.2 (-c.1 / c.2.1)) +
            (c.2.1 * z₂ - c.2.2 (-c.1 / c.2.1)) := by ring
      _ = 0 := by rw [hz0, hz1, zero_add]
  · rfl

/-- The lower bound `d ≥ n-1` in Theorem 1. -/
theorem closedWord_weight_ge {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) (hz₂ : 1 + z₂ ≠ 0)
    (c : ClosedCoeff 𝔽) (hc : ¬ IsRadicalCoeff c) :
    2 * Fintype.card 𝔽 + tail - 1 ≤
      symplecticWeight (closedWord (tail := tail) z₂ lam c) := by
  simpa [Fintype.card_sum, Fintype.card_prod, Nat.mul_comm] using
    weight_ge_card_sub_one_of_unique_zero (closedWord (tail := tail) z₂ lam c)
      (closedWord_unique_zero z₂ lam hlam hz₂ c hc)

/-- The lower bound is attained by the coefficient choice from the paper. -/
theorem closedWord_weight_attained {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) (hz₂ : 1 + z₂ ≠ 0)
    (u₀ : 𝔽) :
    ∃ c : ClosedCoeff 𝔽, ¬ IsRadicalCoeff c ∧
      symplecticWeight (closedWord (tail := tail) z₂ lam c) =
        2 * Fintype.card 𝔽 + tail - 1 := by
  let c : ClosedCoeff 𝔽 := (-u₀, 1, fun u => if u = u₀ then -1 else 0)
  have hc : ¬ IsRadicalCoeff c := by simp [IsRadicalCoeff, c]
  have hzero : closedWord (tail := tail) z₂ lam c (Sum.inl (u₀, false)) = 0 := by
    simp [closedWord, c]
  refine ⟨c, hc, ?_⟩
  simpa [Fintype.card_sum, Fintype.card_prod, Nat.mul_comm] using
    weight_eq_card_sub_one_of_unique_zero (closedWord (tail := tail) z₂ lam c)
      (Sum.inl (u₀, false)) hzero
      (closedWord_unique_zero z₂ lam hlam hz₂ c hc)

/--
**Theorem 1, closed-form normalizer certificate (geometric core).**

For every nonempty tail, a nonzero `λ`, and the paper's condition `1+z₂ ≠ 0`, the
displayed family has independent coefficients and exact non-radical distance `n-1`.
Its dimensions give `[[n,1,n-1;n-q-1]]_q`, since here `n=2q+tail` and hence
`n-q-1=q+tail-1`.  The BDH excess is exactly `q-2`.
-/
theorem theorem1_closed_form {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (hlam : lam ≠ 0) (hz₂ : 1 + z₂ ≠ 0)
    (hδ : closedDelta (tail := tail) z₂ lam ≠ 0) :
    Nonempty (NormalizerSideCertificate 𝔽 tail z₂ lam) := by
  exact ⟨{
    encodeInjective := closedWord_injective z₂ lam hlam
    deltaNonzero := hδ
    gramFormula := closedWord_symplecticProduct z₂ lam
    radicalIff := closedWord_radical_iff z₂ lam hδ
    normalizerFinrank := closedNormalizer_finrank z₂ lam hlam
    radicalFinrank := closedRadicalCoefficients_finrank
    distanceLower := closedWord_weight_ge z₂ lam hlam hz₂
    distanceAttained := closedWord_weight_attained z₂ lam hlam hz₂ 0
  }⟩

/-- A field with at least three elements contains a scalar avoiding two forbidden values. -/
lemma exists_nonzero_add_ne_zero {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    (hcard : 3 ≤ Fintype.card 𝔽) (a : 𝔽) :
    ∃ lam : 𝔽, lam ≠ 0 ∧ a + lam ≠ 0 := by
  classical
  by_contra h
  push_neg at h
  have hall : ∀ x : 𝔽, x = 0 ∨ a + x = 0 := by
    intro x
    by_cases hx : x = 0
    · exact Or.inl hx
    · exact Or.inr (h x hx)
  let f : 𝔽 → Bool := fun x => decide (x = 0)
  have hf : Function.Injective f := by
    intro x y hxy
    by_cases hx : x = 0
    · have hy : y = 0 := by
        by_contra hy
        simpa [f, hx, hy] using hxy
      simpa [hx, hy]
    · have hy : y ≠ 0 := by
        intro hy
        simpa [f, hx, hy] using hxy
      rcases hall x with hx0 | hax
      · exact (hx hx0).elim
      rcases hall y with hy0 | hay
      · exact (hy hy0).elim
      linear_combination hax - hay
  have hle := Fintype.card_le_of_injective f hf
  simp only [Fintype.card_bool] at hle
  omega

/-- The paper's odd-length binary branch makes `(n-1)·1 + 1` nonzero. -/
lemma binary_odd_delta_ne_zero
    {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (hcard : Fintype.card 𝔽 = 2)
    (hodd : Odd (2 * Fintype.card 𝔽 + tail)) :
    (((2 * Fintype.card 𝔽 + tail - 1 : ℕ) : 𝔽) + 1) ≠ 0 := by
  obtain ⟨m, hm⟩ := hodd
  have htwo : (2 : 𝔽) = 0 := by
    simpa [hcard] using Nat.cast_card_eq_zero 𝔽
  rw [hm]
  push_cast
  simp [htwo]

/--
**Theorem 1 (exact goal).**  Under precisely the two parameter branches stated in the
paper, there are choices of `z₂` and nonzero `λ` for which the full normalizer-side
certificate exists.
-/
theorem theorem1_exact {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail]
    (hcase : 3 ≤ Fintype.card 𝔽 ∨
      (Fintype.card 𝔽 = 2 ∧ Odd (2 * Fintype.card 𝔽 + tail))) :
    ∃ z₂ lam : 𝔽, lam ≠ 0 ∧ 1 + z₂ ≠ 0 ∧
      Nonempty (NormalizerSideCertificate 𝔽 tail z₂ lam) := by
  let z₂ : 𝔽 := if (2 : 𝔽) = 0 then 0 else 1
  have hz₂ : 1 + z₂ ≠ 0 := by
    dsimp [z₂]
    split_ifs with htwo
    · simp
    · simpa [one_add_one_eq_two] using htwo
  rcases hcase with hlarge | ⟨hcard, hodd⟩
  · obtain ⟨lam, hlam, hδbase⟩ := exists_nonzero_add_ne_zero hlarge
        (((2 * Fintype.card 𝔽 + tail - 1 : ℕ) : 𝔽))
    have hδ : closedDelta (tail := tail) z₂ lam ≠ 0 := by
      rw [closedDelta_eq_cast_length_sub_one_add]
      exact hδbase
    exact ⟨z₂, lam, hlam, hz₂, theorem1_closed_form z₂ lam hlam hz₂ hδ⟩
  · let lam : 𝔽 := 1
    have hlam : lam ≠ 0 := one_ne_zero
    have hδ : closedDelta (tail := tail) z₂ lam ≠ 0 := by
      rw [closedDelta_eq_cast_length_sub_one_add]
      exact binary_odd_delta_ne_zero hcard hodd
    exact ⟨z₂, lam, hlam, hz₂, theorem1_closed_form z₂ lam hlam hz₂ hδ⟩

#print axioms theorem1_closed_form
#print axioms theorem1_exact

end ICLR2027EAQECC

