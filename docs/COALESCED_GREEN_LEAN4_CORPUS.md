# COALESCED GREEN LEAN4 CORPUS

## Scope and evidence rule

This dossier records the currently audited **user-authored** GREEN Lean4 theorem surfaces relevant to the Speedup/ChronoFold/OIC formal stack. GREEN means the source declares a completed proof with no `sorry` in the cited module and the repository's theorem inventories/build records classify it as verified. It does not mean every concrete implementation depending on a theorem is automatically verified.

The upstream `batmeezy918/mathlib4` repository is treated as an inherited dependency corpus rather than copied theorem-by-theorem; including all upstream Mathlib theorems would not be an accurate representation of the user's authored theorem corpus.

`chronoflow-proof` is retained as a distinct Mathlib-backed kernel. Hypothesized, narrative-only, disabled, rejected, and EMV-0001 materials are excluded from GREEN.

## 1. ChronoFold AGD core

GREEN theorem set from `docs/PROVEN_THEOREMS.md`:

- `AGDEquiv.refl`, `AGDEquiv.symm`, `AGDEquiv.trans`
- `TBar_sound`
- `interchangeable_iff`
- `admission_iff_TBar`
- `admissible_implies_descends`
- `admissible_compose`
- `admissible_id`
- `opIterate_zero`, `opIterate_succ`
- `admissible_iterate`
- `TBar_iterate_sound`

Kernel proof pattern: direct equality (`rfl`) for definitional identities; `Quotient.sound`/`Quotient.exact`; induction over `Nat`; chained equalities for compositional preservation.

Operational effect: admissible operators preserve the retained constitutional observations and remain admissible under finite composition/iteration; their quotient dynamics is defined by a sound lift.

## 2. ChronoFold universal quotient

- `respects_of_interchangeable`
- `lift_pi`
- `lift_unique`
- `qstar_universal_exists`
- `qstar_universal_unique`
- `qstar_universal`
- `morphTo_commutes`
- `morphTo_unique`
- `qstar_initial`
- `TBar_is_lift`

Kernel proof pattern: `Quotient.lift`, `Quotient.inductionOn`, function extensionality, and uniqueness by pointwise equality.

Operational effect: every AGD-respecting map factors through the canonical quotient, and the factor is unique. The quotient therefore represents the declared observable structure rather than an arbitrary compression.

## 3. Rank / multi-invariant layers

- `projective_collapse`
- `apply_is_fixed`
- `RankedSpan.rank_eq_length`
- `RankedSpan.rank_le_length`
- `projective_idempotent_comp`
- `MultiEquiv.refl`, `MultiEquiv.symm`, `MultiEquiv.trans`
- `multiEquiv_of_finer`
- `multiAdmissible_compose`
- `finer_implies_coarser`

Operational effect: idempotent projections stabilize after one application; finer multi-invariant equality implies coarser equality; multi-invariant admissibility composes.

## 4. Certified class graph

- `certifiedEdge_class_step`
- `classAdjacent_of_mem`
- `classPath_zero`
- `classPath_one_of_adjacent`
- `outDegreeBound_eq`

Operational effect: concrete certified transitions can be represented as quotient-class edges and finite class paths.

## 5. Bidirectional / fibre / finite reduction

- `exists_reconstruct`
- `residual_zero_observables`
- `reconstruct_residual_zero`
- `pi_surjective`
- `zero_node_admissible`
- `admissible_preserves_class`
- `bidirectional_intertwine`
- `operator_algebra_closed`
- `admissible_powers`
- `TBar_powers_sound`
- `fibre_witness_collapses`
- `nontrivial_fibre_pi_not_injective`
- `strict_card_of_surjective_not_injective`
- `nontrivial_fibre_strict_reduction`

Kernel proof pattern: quotient representative existence; `Quotient.sound`/`Quotient.exact`; injectivity contradiction; finite cardinality arguments; operator composition/iteration induction.

Operational effect: nontrivial observational fibres are formally detectable. On finite covered domains, a nontrivial fibre plus surjective coverage forces strict reduction of quotient cardinality.

## 6. Invariant safety

- `invariantSafe'_of_safe`
- `invariantSafe_of_safe'`
- `invariantSafe_iff`
- `invariantSafe_nil`
- `invariantSafe_of_criticals_in_constitution`
- `invariantSafe_omega`
- `invariantSafe_C`
- `invariantSafe_omega_and_C`
- `drop_critical_makes_unsafe`
- `multiInvariantSafe_of_components`
- `coarser_may_be_unsafe`
- `checkSafeSample_implies_pairwise`

Operational effect: quotient/refinement choices can be checked against explicitly declared critical observables. A witness proving a critical distinction is collapsed gives a formal unsafety result for that quotient.

## 7. SIC constitutional layer

- `operationalEq_refl`
- `operationalEq_symm`
- `operationalEq_trans`
- `operationalEq_equivalence`
- `invariant_identity`
- `invariant_comp`
- `SICOperatorAlgebra_id`
- `SICOperatorAlgebra_comp`
- `invariant_preservation_implies_operational_equivalence`
- `governor_iff_invariant`
- `governor_sound`
- `governor_identity`
- `governor_composition_closed`
- `governor_generates_closed_operator_system`
- `governor_preserves_declared_information`
- `quotient_descent`
- `reconstruction_modulo_observables`
- `reconstruction_preserves_declared_information`
- `replay_preserves_declared_information`
- `constitutional_roundtrip`
- `lawfulTrajectory_preserves_invariant`
- `lawfulTrajectory_preserves_declared_information`
- `sic_agd_constitutional_closure`
- `reconstruction_is_operational_not_microscopic`
- `completeness_implies_operational_equivalence`

Operational effect: if declared observables factor through an invariant, invariant preservation gives operational equivalence on those observables, including lawful finite trajectories, replay, and reconstruction modulo the declared observable relation.

## 8. Measurement / dynamic closure

- `measurement_equiv_refl`, `measurement_equiv_symm`, `measurement_equiv_trans`
- `dist_self`, `dist_comm`, `dist_triangle`
- `jitter_close_reflexive`, `jitter_close_symmetric`, `jitter_close_triangle`
- `agd_measurement_invariant`
- `speedup_positive`
- `benchmark_claim_valid`
- `agd_transport_closure`
- `agd_bisimulation`
- `agd_flow_semigroup`
- `agd_master_dynamic_closure`
- `agd_failure_recovery`
- `memory_lineage_reconstruction`

Operational effect: measured states have a formal equivalence relation over jitter/error; jitter closeness has reflexive/symmetric/triangle structure; invariant-preserving transport supports dynamic closure; failure recovery has a constructive rollback theorem under its stated stability assumptions.

## 9. Operational quotient chain

- `admissibility_sufficient`
- `operationalEq_refl`, `operationalEq_symm`, `operationalEq_trans`
- `operationalEq_preserved_by_operator`
- `control_preserved`
- `theta_projected_fixed`
- `quotient_of_full_chain`
- `quotient_iterate_operator`
- `speedup_implies_faster`

Operational effect: operator, Volterra, control, and Theta components can be chained through a quotient representation while preserving the formally declared quotient semantics.

## 10. CVR Phase 0 constitutional kernel

- `namespace_preservation`
- `version_preservation`
- `provenance_preservation`
- `relationship_resolution_preservation`
- `acyclicity_preservation`
- `omega_preservation`
- `admissibility_closure`
- `operator_composition_closed`
- `identity_operator_admissible`
- `operator_composition_associative`
- `inverse_is_admissible`
- `defect_monotonicity`
- `constitutional_closure`

Operational effect: any finite chain of operators satisfying the declared preservation contract retains the constitutional state. The defect measure is non-increasing under the theorem's hypotheses.

## 11. Concrete witnesses and intake kernels

- `w1_ne_w2`
- `w1_omega_eq_w2_omega`
- `w1_C_eq_w2_C`
- `w1_w2_same_class`
- `w1_w2_nontrivial_fibre`
- `pi_witness_not_injective`
- `witness_ne`
- `witness_omega`
- `witness_covariant`
- `witness_agd_equiv`
- `witness_fibre`
- `witness_noninjective`
- `witness_is_nontrivial_fibre`
- `agd_ci_marker`
- `t1`
- `nat_add_zero_right`
- `omega_divides_n` (including intake copy)
- `correct_by_construction_search`
- subclaims: `pivotal`, `identity_preservation`, `tilde_iff_stateEq`, `omega_sigma_id`, `step_implies_D_lt`, `execution_terminates`, `correct_reconstruction`

Operational effect: the fibre-collapse premise has explicit concrete witnesses, while the intake search theorem surface supplies closed correctness and termination/reconstruction consequences.

## 12. Nrebbi-El first-principles kernel

`NrebbiElTheorem.lean`:
- `iterate_zero`, `iterate_succ`
- `operationalEq_refl`, `operationalEq_symm`, `operationalEq_trans`
- `admissible_iff_class_preserved`
- `admissible_iff_operational_fixed`
- `admissible_iff_identity_descent`
- `descends_implies_wellDefined`
- `descent_implies_wellDefined_and_witness`
- `quotient_iterate`
- `recursive_implies_descent`
- `descent_iff_recursive`
- `admissible_iterate`
- `admissible_iff_recursive_identity`
- `descends_compose`
- `admissible_compose`
- `reconstruction_roundtrip`
- `reconstructed_state_operationalEq`
- `conjugacy_of_descent`
- `factorization_preserves_semantics`
- `nrebbi_el_theorem`

`NrebbiElSimulation.lean`:
- `iterate_zero`, `iterate_succ`
- `graph_rel_iff`, `graph_rel_refl`
- `descends_implies_simulates`
- `simulates_implies_descends`
- `simulation_iff_descent`
- `descends_implies_recursive_simulates`
- `recursively_simulates_implies_simulates`
- `simulation_iff_recursive_simulation`
- `descends_iff_exact_trajectory`
- `simulation_iff_exact_trajectory`
- `admissible_implies_identity_simulation`
- `admissible_implies_recursive_identity_simulation`
- `factor_witness_implies_respects`
- `nrebbi_el_simulation_theorem`

Operational effect: one-step descent, graph simulation, recursive simulation, and exact finite trajectory correspondence are equivalent under the declared deterministic definitions. Admissibility is the identity-descent specialization.

## 13. Speedup Lean4 kernel

### Work / FLOP model
- `outer_factorization`
- `square_reduction`
- `quotientWork_ne_zero`
- `workRatio_outer`
- `workRatio_square`
- `fullWork_1024`
- `quotientWork_256`
- `canonical_ratio`
- `strict_work_reduction`
- `factor_four_gives_sixteen`
- `four_sq`
- `dim_factorization`
- `canonical_workRatio`
- `canonical_is_instance_of_q_square`
- `canonical_q_square_equals_sixteen`
- `work_model_closure`

Exact consequence: `W_full = 2,147,483,648`, `W_quotient = 134,217,728`, exact work ratio `16`, strict reduction, and 93.75% modeled arithmetic-work reduction.

### Projection
- `iterate_zero`, `iterate_succ`, `iterate_one`, `iterate_add`
- `projection_step`
- `intertwines_wellDefined`
- `observable_respects`
- `projection_iterate`
- `induced_operator_unique`
- `quotient_observable_correct`
- `projection_closure`

### Reconstruction
- `section_is_right_inverse`
- `section_injective`
- `section_implies_surjective`
- `reconstructed_operator`
- `reconstructed_iterate`
- `observe_via_section`
- `reconstructed_observable`
- `reconstruction_closure`

The concrete GEMM reconstruction section remains an explicit implementation obligation.

### Speedup boundary
- `modeled_speedup_valid`
- `semantic_and_work_closure`
- `measured_runtime_is_not_a_work_theorem`
- `measured_hundredths_neq_work_ratio_times_100`
- `speedup_stack_closure`

The encoded 15.96× runtime measurement is explicitly not identified with the 16× modeled work ratio.

### GODS quotient kernel
- `godsEquiv_refl`, `godsEquiv_symm`, `godsEquiv_trans`
- `mkG_sound`, `mkG_exact`, `mkG_eq_iff`, `mkG_surjective`
- `descendOp_mk`, `gods_one_step`, `gods_descend`, `gods_descend_unique`
- `iterate_zero`, `iterate_succ`, `respects_iterate`
- `gods_recursive_descent`
- `section_mk`, `gods_bidirectional_closure`
- `inducedObs_mk`, `inducedObs_recovers`, `observe_via_section`
- `invariant_descends`
- `reverse_one_step`, `reverse_respects`, `reverse_equiv_from_projection`, `reverse_recursive_from_bidirectional`, `reverse_fibre_iterate`
- `gods_len3_certified`
- `gods_maximal_operational_claim`

Operational effect: the quotient operator is uniquely induced by respect for the observational fibre; recursive descent and reverse section closure are available; reverse verification can recover the `Respects` premise.

### PCSS evidence kernel
- `publish_requires_all_gates`
- `lean_false_not_publishable`

Publication law: `PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`.

## 14. OIC-Core-Calculus kernel

- `Compose_assoc`
- `IdOp_left`
- `IdOp_right`
- `derive_sound`
- `residual_zero_is_decided`
- `bidirectional_closure`
- `empty_corpus_always_boundary`
- `phaseTransition_preserves_cert`
- `elevation_requires_provenance`
- `authorized_implies_provenance`
- `rcc_coherent_implies_realized`
- `residual_zero_sound`
- `instantiation_requires_AGD`
- `elevated_agd_scope`
- `authorized_extension_replay`
- `can_detect_boundary`

Operational effect: proof derivation and authorization can be represented as typed certificate transitions with explicit residual/boundary outcomes and replay preservation. OIC leaves concrete AGD corpus injection as an external boundary.

## 15. ChronoFlow auxiliary Mathlib-backed kernel

`chronoflow-proof/ChronoFlow/Basic.lean`:
- `normalize_norm_one`
- `flow_norm_invariant`
- `iterate_nonzero`
- `trajectory_bounded`

Operational effect: normalized states have unit norm; under the declared nonzero-preserving matrix condition, every iterate is nonzero and every positive-time trajectory is unit-norm.

## 16. Combined proof-governed operational law

`problem -> formal state -> constitution/invariants -> admissible operator -> quotient candidate -> descent/simulation -> exact finite correspondence -> observable preservation -> reconstruction section -> reverse closure -> work model -> external measurement -> evidence certificate -> PCSS gate -> claim class`

The bidirectional property is the key systems consequence: forward proof establishes what a proposed reduction preserves; reverse proof identifies what is necessary to justify that reduction. An LLM client can therefore be required to return either a proof-bearing closure object or an explicit boundary/reformulation rather than an unsupported conclusion.

## 17. Hard boundaries

- Arithmetic work ratio is not wall-clock runtime.
- Abstract reconstruction is not concrete GEMM reconstruction.
- A benchmark is not a theorem.
- A theorem is not an implementation-binding proof.
- An external client name is not evidence of live connectivity.
- The coarsest universally minimal admissible quotient construction remains a formal frontier.
- `mathlib4` upstream theorem volume is not counted as authored AGD theorem content.
