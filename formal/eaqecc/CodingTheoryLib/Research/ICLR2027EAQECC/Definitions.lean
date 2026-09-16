import Mathlib

/-!
# Shared definitions for the ICLR 2027 EAQECC exact goals

This module contains no named theorem results and imports only Mathlib.  It is the trusted,
shared vocabulary imported independently by the Comparator challenge and the proof; the proof
terms inside definitions establish only their required linear-map and submodule structure laws.
-/

open BigOperators

namespace ICLR2027EAQECC

universe u

/-- A Pauli vector, written coordinatewise as `(X,Z)` pairs. -/
abbrev PauliVector (𝔽 : Type u) (ι : Type*) := ι → 𝔽 × 𝔽

/-- The standard symplectic product on coordinatewise `(X,Z)` pairs. -/
def symplecticProduct {𝔽 : Type u} [CommRing 𝔽] {ι : Type*} [Fintype ι]
    (x y : PauliVector 𝔽 ι) : 𝔽 :=
  ∑ i : ι, ((x i).1 * (y i).2 - (x i).2 * (y i).1)

/-- The symplectic weight is the number of nonzero coordinate pairs. -/
def symplecticWeight {𝔽 : Type u} [Zero 𝔽] {ι : Type*} [Fintype ι]
    [DecidableEq 𝔽] (x : PauliVector 𝔽 ι) : ℕ :=
  (Finset.univ.filter fun i => x i ≠ 0).card

/-- Coordinates: two qudits for each field element, followed by a nonempty tail. -/
abbrev ClosedCoord (𝔽 : Type u) (tail : ℕ) := Sum (𝔽 × Bool) (Fin tail)

/-- Coefficients `(α,β,(tᵢ))` of `αa + βb + ∑ᵢ tᵢρᵢ`. -/
abbrev ClosedCoeff (𝔽 : Type u) := 𝔽 × 𝔽 × (𝔽 → 𝔽)

/-- The radical coefficients are precisely those with `α=β=0`. -/
def IsRadicalCoeff {𝔽 : Type u} [Zero 𝔽] (c : ClosedCoeff 𝔽) : Prop :=
  c.1 = 0 ∧ c.2.1 = 0

/-- The paper's closed-form word. -/
def closedWord {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) (c : ClosedCoeff 𝔽) :
    PauliVector 𝔽 (ClosedCoord 𝔽 tail)
  | Sum.inl (u, false) => (c.1 + c.2.1 * u, c.2.1 + c.2.2 u)
  | Sum.inl (u, true) => (c.1 + c.2.1 * u, c.2.1 * z₂ - c.2.2 u)
  | Sum.inr j => (c.1, c.2.1 * if j = 0 then lam else 1)

/-- The closed-form generators, packaged as a linear encoding map. -/
def closedWordLinearMap {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) :
    ClosedCoeff 𝔽 →ₗ[𝔽] PauliVector 𝔽 (ClosedCoord 𝔽 tail) where
  toFun := closedWord (tail := tail) z₂ lam
  map_add' c d := by
    funext k
    cases k with
    | inl ub =>
        rcases ub with ⟨u, b⟩
        cases b <;> ext <;> simp [closedWord] <;> ring
    | inr j =>
        ext <;> simp [closedWord] <;> split_ifs <;> ring
  map_smul' a c := by
    funext k
    cases k with
    | inl ub =>
        rcases ub with ⟨u, b⟩
        cases b <;> ext <;> simp [closedWord] <;> ring
    | inr j =>
        ext <;> simp [closedWord] <;> split_ifs <;> ring

/-- The actual normalizer-side subspace spanned by the displayed generators. -/
def closedNormalizer {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) :
    Submodule 𝔽 (PauliVector 𝔽 (ClosedCoord 𝔽 tail)) :=
  LinearMap.range (closedWordLinearMap (tail := tail) z₂ lam)

/-- The coefficient subspace of the displayed radical generators. -/
def closedRadicalCoefficients (𝔽 : Type u) [Field 𝔽] :
    Submodule 𝔽 (ClosedCoeff 𝔽) where
  carrier := { c | IsRadicalCoeff c }
  zero_mem' := by simp [IsRadicalCoeff]
  add_mem' := by
    rintro c d ⟨hc₁, hc₂⟩ ⟨hd₁, hd₂⟩
    simp [IsRadicalCoeff, hc₁, hc₂, hd₁, hd₂]
  smul_mem' := by
    rintro a c ⟨hc₁, hc₂⟩
    simp [IsRadicalCoeff, hc₁, hc₂]

/-- Coefficients of the two hyperbolic generators `a` and `b`. -/
def aCoeff {𝔽 : Type u} [Field 𝔽] : ClosedCoeff 𝔽 := (1, 0, 0)

def bCoeff {𝔽 : Type u} [Field 𝔽] : ClosedCoeff 𝔽 := (0, 1, 0)

/-- The single potentially nonzero Gram entry `⟪a,b⟫`. -/
def closedDelta {𝔽 : Type u} [Field 𝔽] [Fintype 𝔽] [DecidableEq 𝔽]
    {tail : ℕ} [NeZero tail] (z₂ lam : 𝔽) : 𝔽 :=
  symplecticProduct
    (closedWord (tail := tail) z₂ lam (aCoeff (𝔽 := 𝔽)))
    (closedWord (tail := tail) z₂ lam (bCoeff (𝔽 := 𝔽)))

/-- The EAQECC parameter record used by the standalone certificate. -/
structure EAQECCParameters where
  length : ℕ
  logical : ℕ
  distance : ℕ
  entanglement : ℕ
  deriving DecidableEq, Repr

/-- Kernel-checkable normalizer-side data for Theorem 1. -/
structure NormalizerSideCertificate (𝔽 : Type u) [Field 𝔽] [Fintype 𝔽]
    [DecidableEq 𝔽] (tail : ℕ) [NeZero tail] (z₂ lam : 𝔽) where
  encodeInjective : Function.Injective (closedWord (tail := tail) z₂ lam)
  deltaNonzero : closedDelta (tail := tail) z₂ lam ≠ 0
  gramFormula : ∀ c d : ClosedCoeff 𝔽,
    symplecticProduct (closedWord (tail := tail) z₂ lam c)
        (closedWord (tail := tail) z₂ lam d) =
      (c.1 * d.2.1 - c.2.1 * d.1) * closedDelta (tail := tail) z₂ lam
  radical : ClosedCoeff 𝔽 → Prop := IsRadicalCoeff
  radicalIff : ∀ c,
    (∀ d, symplecticProduct (closedWord (tail := tail) z₂ lam c)
      (closedWord (tail := tail) z₂ lam d) = 0) ↔ radical c
  normalizerFinrank :
    Module.finrank 𝔽 (closedNormalizer (tail := tail) z₂ lam) = Fintype.card 𝔽 + 2
  radicalFinrank :
    Module.finrank 𝔽 (closedRadicalCoefficients 𝔽) = Fintype.card 𝔽
  normalizerDimension : ℕ := Fintype.card 𝔽 + 2
  radicalDimension : ℕ := Fintype.card 𝔽
  symplecticRank : ℕ := 2
  distanceLower : ∀ c, ¬ radical c →
    2 * Fintype.card 𝔽 + tail - 1 ≤
      symplecticWeight (closedWord (tail := tail) z₂ lam c)
  distanceAttained : ∃ c, ¬ radical c ∧
    symplecticWeight (closedWord (tail := tail) z₂ lam c) =
      2 * Fintype.card 𝔽 + tail - 1
  parameters : EAQECCParameters :=
    { length := 2 * Fintype.card 𝔽 + tail
      logical := 1
      distance := 2 * Fintype.card 𝔽 + tail - 1
      entanglement := Fintype.card 𝔽 + tail - 1 }
  bdhExcess : ℤ := (Fintype.card 𝔽 : ℤ) - 2

/-- Coordinate projection from a Pauli vector to one `(X,Z)` pair. -/
def coordinateMap {𝔽 : Type u} [Field 𝔽] {ι : Type*} (i : ι) :
    PauliVector 𝔽 ι →ₗ[𝔽] 𝔽 × 𝔽 where
  toFun v := v i
  map_add' _ _ := rfl
  map_smul' _ _ := rfl

/-- Projection onto two named coordinates. -/
def coordinatePairMap {𝔽 : Type u} [Field 𝔽] {ι : Type*} (i h : ι) :
    PauliVector 𝔽 ι →ₗ[𝔽] (𝔽 × 𝔽) × (𝔽 × 𝔽) where
  toFun v := (v i, v h)
  map_add' _ _ := rfl
  map_smul' _ _ := rfl

/-- “Entirely Z-type” means that every radical vector has zero X-component. -/
def IsZType {𝔽 : Type u} [Field 𝔽] {ι : Type*}
    (R : Submodule 𝔽 (PauliVector 𝔽 ι)) : Prop :=
  ∀ r : R, ∀ i, (r.1 i).1 = 0

/-- A local coordinate map with the defining symplectic-preservation law. -/
structure LocalSymplecticMap (𝔽 : Type u) [Field 𝔽] where
  toLinearEquiv : (𝔽 × 𝔽) ≃ₗ[𝔽] (𝔽 × 𝔽)
  preserves : ∀ x y,
    (toLinearEquiv x).1 * (toLinearEquiv y).2 -
        (toLinearEquiv x).2 * (toLinearEquiv y).1 =
      x.1 * y.2 - x.2 * y.1

/-- Apply one local symplectic equivalence independently at every coordinate. -/
def applyLocal {𝔽 : Type u} [Field 𝔽] {ι : Type*}
    (T : ι → LocalSymplecticMap 𝔽) :
    PauliVector 𝔽 ι ≃ₗ[𝔽] PauliVector 𝔽 ι :=
  LinearEquiv.piCongrRight fun i => (T i).toLinearEquiv

/-- A product of local symplectic maps makes `R` entirely Z-type. -/
def IsLocallyZNormalizable {𝔽 : Type u} [Field 𝔽] {ι : Type*}
    (R : Submodule 𝔽 (PauliVector 𝔽 ι)) : Prop :=
  ∃ T : ι → LocalSymplecticMap 𝔽,
    ∀ r : R, ∀ i, ((applyLocal T r.1) i).1 = 0

end ICLR2027EAQECC

