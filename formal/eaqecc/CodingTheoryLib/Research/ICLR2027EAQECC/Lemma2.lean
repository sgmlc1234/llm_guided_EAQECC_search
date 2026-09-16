import CodingTheoryLib.Research.ICLR2027EAQECC.Definitions

/-!
# Standalone verification of Lemma 2

This file formalizes the coordinate-normalization statement in Appendix B.2 of
`ICLR2027_EAQECC_v12_B.pdf`. Apart from the companion definitions module, its dependency
closure imports only Mathlib and is independent of the proof of Theorem 1.
-/

open BigOperators

namespace ICLR2027EAQECC

universe u

/-! ## Coordinate normalization (Lemma 2) -/

/-
The dimension argument and construction of the local determinant-one maps are kept as
separate public lemmas below.  This mirrors the two paragraphs of the paper proof and
makes the dependency boundary visible to `#print axioms`.
-/

/-- A one-dimensional (or zero) coordinate image can be sent to the Z-axis by an SL₂ map. -/
theorem local_normalize_line {𝔽 : Type u} [Field 𝔽]
    (P : Submodule 𝔽 (𝔽 × 𝔽)) (hP : Module.finrank 𝔽 P ≤ 1) :
    ∃ T : LocalSymplecticMap 𝔽, ∀ p : P, (T.toLinearEquiv p.1).1 = 0 := by
  classical
  by_cases hbot : P = ⊥
  · refine ⟨{ toLinearEquiv := LinearEquiv.refl 𝔽 (𝔽 × 𝔽), preserves := ?_ }, ?_⟩
    · intro x y
      rfl
    · intro p
      have : (p.1 : 𝔽 × 𝔽) = 0 := by simpa [hbot] using p.2
      simp [this]
  · obtain ⟨v, hvP, hv⟩ : ∃ v : 𝔽 × 𝔽, v ∈ P ∧ v ≠ 0 := by
      letI : Nontrivial P := Submodule.nontrivial_iff_ne_bot.mpr hbot
      obtain ⟨v, hv⟩ := exists_ne (0 : P)
      exact ⟨v.1, v.2, by
        intro hv0
        apply hv
        apply Subtype.ext
        exact hv0⟩
    have hspan : P = Submodule.span 𝔽 {v} := by
      apply le_antisymm
      · have hfin : Module.finrank 𝔽 (Submodule.span 𝔽 {v}) = 1 := by
          rw [finrank_span_singleton hv]
        have hle : Submodule.span 𝔽 {v} ≤ P :=
          Submodule.span_le.mpr (by simpa using hvP)
        have heq : Submodule.span 𝔽 {v} = P :=
          Submodule.eq_of_le_of_finrank_le hle (by simpa [hfin] using hP)
        simpa [heq]
      · exact Submodule.span_le.mpr (by simpa using hvP)
    by_cases hx : v.1 = 0
    · have hz : v.2 ≠ 0 := by
        intro hz
        apply hv
        exact Prod.ext hx hz
      let E : (𝔽 × 𝔽) ≃ₗ[𝔽] (𝔽 × 𝔽) :=
        { toFun := fun x => (v.2 * x.1, v.2⁻¹ * x.2)
          invFun := fun x => (v.2⁻¹ * x.1, v.2 * x.2)
          left_inv := by intro x; ext <;> simp [hz]
          right_inv := by intro x; ext <;> simp [hz]
          map_add' := by intro x y; ext <;> simp [mul_add]
          map_smul' := by intro a x; ext <;> simp [mul_assoc, mul_left_comm] }
      refine ⟨{ toLinearEquiv := E, preserves := ?_ }, ?_⟩
      · intro x y
        change (v.2 * x.1) * (v.2⁻¹ * y.2) -
          (v.2⁻¹ * x.2) * (v.2 * y.1) = x.1 * y.2 - x.2 * y.1
        field_simp [hz]
      · intro p
        have hp : p.1 ∈ Submodule.span 𝔽 {v} := by simpa [← hspan] using p.2
        rcases Submodule.mem_span_singleton.mp hp with ⟨a, ha⟩
        change v.2 * p.1.1 = 0
        rw [← ha]
        simp [hx]
    · let E : (𝔽 × 𝔽) ≃ₗ[𝔽] (𝔽 × 𝔽) :=
        { toFun := fun x => (v.2 * x.1 - v.1 * x.2, v.1⁻¹ * x.1)
          invFun := fun y => (v.1 * y.2, v.1⁻¹ * (v.2 * v.1 * y.2 - y.1))
          left_inv := by intro x; ext <;> field_simp <;> ring
          right_inv := by intro y; ext <;> field_simp <;> ring
          map_add' := by intro x y; ext <;> simp <;> ring
          map_smul' := by intro a x; ext <;> simp <;> ring }
      refine ⟨{ toLinearEquiv := E, preserves := ?_ }, ?_⟩
      · intro x y
        change (v.2 * x.1 - v.1 * x.2) * (v.1⁻¹ * y.1) -
          (v.1⁻¹ * x.1) * (v.2 * y.1 - v.1 * y.2) =
            x.1 * y.2 - x.2 * y.1
        field_simp [hx]
        ring
      · intro p
        have hp : p.1 ∈ Submodule.span 𝔽 {v} := by simpa [← hspan] using p.2
        rcases Submodule.mem_span_singleton.mp hp with ⟨a, ha⟩
        change v.2 * p.1.1 - v.1 * p.1.2 = 0
        rw [← ha]
        simp
        ring

/--
Linear-algebraic heart of Lemma 2.  The pair-kernel hypothesis is exactly what the
`n-1` distance assumption says: no vector outside `R` can vanish at two coordinates.
-/
theorem coordinate_images_have_rank_at_most_one
    {𝔽 : Type u} [Field 𝔽] {ι : Type*} [Fintype ι] [DecidableEq ι]
    (L R : Submodule 𝔽 (PauliVector 𝔽 ι)) (hRL : R ≤ L)
    (hdim : Module.finrank 𝔽 L = Module.finrank 𝔽 R + 2)
    (hRdim : 2 < Module.finrank 𝔽 R)
    (hpair : ∀ (v : L) (i h : ι), i ≠ h → v.1 i = 0 → v.1 h = 0 → v.1 ∈ R) :
    ∀ i, Module.finrank 𝔽 (R.map (coordinateMap i)) ≤ 1 := by
  classical
  -- The proof is the paper's rank-nullity argument, packaged as a finite-dimensional lemma.
  intro i
  by_contra hi
  have hi2 : Module.finrank 𝔽 (R.map (coordinateMap i)) = 2 := by
    have hle : Module.finrank 𝔽 (R.map (coordinateMap i)) ≤ 2 := by
      calc
        _ ≤ Module.finrank 𝔽 (𝔽 × 𝔽) := Submodule.finrank_le _
        _ = 2 := by simp [Module.finrank_prod]
    omega
  have hinj : Function.Injective ((coordinateMap i).domRestrict R) := by
    rw [← LinearMap.ker_eq_bot]
    apply (Submodule.eq_bot_iff _).mpr
    intro r hr
    have hri : r.1 i = 0 := hr
    apply Subtype.ext
    funext h
    by_cases hhi : h = i
    · simpa [hhi]
    · have hih : i ≠ h := Ne.symm hhi
      let fL := (coordinatePairMap i h).domRestrict L
      let fR := (coordinatePairMap i h).domRestrict R
      let inc : fR.ker →ₗ[𝔽] fL.ker :=
        { toFun := fun x =>
            ⟨⟨x.1.1, hRL x.1.2⟩, by
              change coordinatePairMap i h x.1.1 = 0
              exact x.2⟩
          map_add' := by intro x y; rfl
          map_smul' := by intro a x; rfl }
      have hinc : Function.Bijective inc := by
        constructor
        · intro x y hxy
          apply Subtype.ext
          apply Subtype.ext
          exact congrArg (fun z => z.1.1) hxy
        · intro x
          have hxi : x.1.1 i = 0 := by
            have hx := x.2
            change (x.1.1 i, x.1.1 h) = 0 at hx
            exact congrArg Prod.fst hx
          have hxh : x.1.1 h = 0 := by
            have hx := x.2
            change (x.1.1 i, x.1.1 h) = 0 at hx
            exact congrArg Prod.snd hx
          have hxR : x.1.1 ∈ R := hpair x.1 i h hih hxi hxh
          let y : fR.ker :=
            ⟨⟨x.1.1, hxR⟩, by simpa [fR, coordinatePairMap, hxi, hxh]⟩
          refine ⟨y, ?_⟩
          apply Subtype.ext
          apply Subtype.ext
          rfl
      let kerEquiv : fR.ker ≃ₗ[𝔽] fL.ker := LinearEquiv.ofBijective inc hinc
      have hker : Module.finrank 𝔽 fR.ker = Module.finrank 𝔽 fL.ker :=
        kerEquiv.finrank_eq
      have hRLrank := fL.finrank_range_add_finrank_ker
      have hRRrank := fR.finrank_range_add_finrank_ker
      have hrange : Module.finrank 𝔽 fL.range = Module.finrank 𝔽 fR.range + 2 := by
        rw [hker] at hRRrank
        omega
      have hLrange_le : Module.finrank 𝔽 fL.range ≤ 4 := by
        calc
          _ ≤ Module.finrank 𝔽 ((𝔽 × 𝔽) × (𝔽 × 𝔽)) := Submodule.finrank_le _
          _ = 4 := by simp [Module.finrank_prod]
      have hRrange_le : Module.finrank 𝔽 fR.range ≤ 2 := by omega
      have hRrange_ge : 2 ≤ Module.finrank 𝔽 fR.range := by
        have hmap := Submodule.finrank_map_le
          (LinearMap.fst 𝔽 (𝔽 × 𝔽) (𝔽 × 𝔽)) fR.range
        have heq : fR.range.map (LinearMap.fst 𝔽 (𝔽 × 𝔽) (𝔽 × 𝔽)) =
            R.map (coordinateMap i) := by
          ext z
          constructor
          · rintro ⟨y, ⟨r, hr⟩, rfl⟩
            refine ⟨r.1, r.2, ?_⟩
            simpa [fR, coordinatePairMap, coordinateMap] using congrArg Prod.fst hr
          · rintro ⟨v, hvR, rfl⟩
            refine ⟨(v i, v h), ?_, rfl⟩
            exact ⟨⟨v, hvR⟩, rfl⟩
        rw [heq, hi2] at hmap
        exact hmap
      have hRrange : Module.finrank 𝔽 fR.range = 2 := by omega
      let g : fR.range →ₗ[𝔽] (R.map (coordinateMap i)) :=
        { toFun := fun y =>
            ⟨y.1.1, by
              rcases y.2 with ⟨r, hr⟩
              refine ⟨r.1, r.2, ?_⟩
              simpa [fR, coordinatePairMap, coordinateMap] using congrArg Prod.fst hr⟩
          map_add' := by intro x y; rfl
          map_smul' := by intro a x; rfl }
      have hgsurj : Function.Surjective g := by
        intro x
        rcases x.2 with ⟨v, hvR, hv⟩
        let y : fR.range := ⟨(v i, v h), ⟨⟨v, hvR⟩, rfl⟩⟩
        refine ⟨y, ?_⟩
        apply Subtype.ext
        change v i = x.1
        exact hv
      have hgfin : Module.finrank 𝔽 fR.range =
          Module.finrank 𝔽 (R.map (coordinateMap i)) := by omega
      have hginj : Function.Injective g :=
        (LinearMap.injective_iff_surjective_of_finrank_eq_finrank hgfin).2 hgsurj
      let y : fR.range := ⟨fR ⟨r.1, r.2⟩, ⟨⟨r.1, r.2⟩, rfl⟩⟩
      have hgy : g y = 0 := by
        apply Subtype.ext
        exact hri
      have hy : y = 0 := hginj hgy
      have hy' := congrArg (fun z => z.1.2) hy
      exact hy'
  have hfin := LinearMap.finrank_le_finrank_of_injective hinj
  have : Module.finrank 𝔽 R ≤ 2 := by
    simpa [Module.finrank_prod] using hfin
  omega

/-- **Lemma 2 (Coordinate normalization).** -/
theorem lemma2_coordinate_normalization
    {𝔽 : Type u} [Field 𝔽] [DecidableEq 𝔽] {ι : Type*} [Fintype ι] [DecidableEq ι]
    (L R : Submodule 𝔽 (PauliVector 𝔽 ι)) (hRL : R ≤ L)
    (hdim : Module.finrank 𝔽 L = Module.finrank 𝔽 R + 2)
    (hRdim : 2 < Module.finrank 𝔽 R)
    (hdistance : ∀ v : L, v.1 ∉ R →
      Fintype.card ι - 1 ≤ symplecticWeight v.1) :
    IsLocallyZNormalizable R := by
  classical
  have hpair : ∀ (v : L) (i h : ι), i ≠ h → v.1 i = 0 → v.1 h = 0 → v.1 ∈ R := by
    intro v i h hih hvi hvh
    by_contra hvR
    have hd := hdistance v hvR
    -- Two distinct zero coordinates force weight at most `n-2`, contradicting `d ≥ n-1`.
    let S : Finset ι := Finset.univ.filter fun j => v.1 j ≠ 0
    have hsub : S ⊆ (Finset.univ.erase i).erase h := by
      intro j hj
      have hjne : v.1 j ≠ 0 := (Finset.mem_filter.mp hj).2
      have hji : j ≠ i := by
        intro hji
        exact hjne (by simpa [hji] using hvi)
      have hjh : j ≠ h := by
        intro hjh
        exact hjne (by simpa [hjh] using hvh)
      simp [hji, hjh]
    have hcard : S.card ≤ Fintype.card ι - 2 := by
      have := Finset.card_le_card hsub
      have hi_mem : i ∈ (Finset.univ : Finset ι) := Finset.mem_univ i
      have hhi : h ≠ i := Ne.symm hih
      have hh_mem : h ∈ (Finset.univ.erase i : Finset ι) := by simp [hhi]
      rw [Finset.card_erase_of_mem hh_mem, Finset.card_erase_of_mem hi_mem] at this
      rw [Finset.card_univ] at this
      omega
    have hcard2 : 2 ≤ Fintype.card ι := by
      by_contra hsmall
      have hle1 : Fintype.card ι ≤ 1 := by omega
      letI : Subsingleton ι := Fintype.card_le_one_iff_subsingleton.mp hle1
      exact hih (Subsingleton.elim i h)
    change Fintype.card ι - 1 ≤ S.card at hd
    omega
  have hrank := coordinate_images_have_rank_at_most_one L R hRL hdim hRdim hpair
  choose T hT using fun i => local_normalize_line (R.map (coordinateMap i)) (hrank i)
  refine ⟨T, ?_⟩
  intro r i
  change ((T i).toLinearEquiv (r.1 i)).1 = 0
  simpa using hT i ⟨r.1 i, ⟨r.1, r.2, rfl⟩⟩

#print axioms lemma2_coordinate_normalization

end ICLR2027EAQECC

