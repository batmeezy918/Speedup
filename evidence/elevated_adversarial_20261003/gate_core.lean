def speedup_gate : Prop := 9601571 > 1000000 ∧ 19978818 > 1000000 ∧ 10001282 > 1000000 ∧ 9595680 > 1000000
def reconstruction_gate : Prop := 381469727 < 10000000000 ∧ 562667847 < 10000000000 ∧ 129699707 < 1000000000 ∧ 0 < 10000000000
def invariant_gate : Prop := 165281243 < 10000000000 ∧ 264223537 < 10000000000 ∧ 173214461 < 10000000000 ∧ 19635164 < 10000000000
theorem speedup_gate_proven : speedup_gate := by unfold speedup_gate; decide
theorem reconstruction_gate_proven : reconstruction_gate := by unfold reconstruction_gate; decide
theorem invariant_gate_proven : invariant_gate := by unfold invariant_gate; decide
theorem elevated_gate_proven : speedup_gate ∧ reconstruction_gate ∧ invariant_gate := by exact ⟨speedup_gate_proven, reconstruction_gate_proven, invariant_gate_proven⟩
