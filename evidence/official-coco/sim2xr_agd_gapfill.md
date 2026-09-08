# SIM2XR / AGD gap fill applied to the official optimizer

Formal facts used (chronofold Lean, not new axioms):

- AGD `Admissible(Ω,C,T)`: T preserves constitutional observables.
- SIM2XR: descent iff iterates intertwine the declared quotient.
- Fibre / Respects: an observable that respects the class is constant on R∞.

Operational translation on BBOB:

- Declared quotient Q = official `cocoex` evaluation + `final_target_hit`.
- Declared constitution Ω = coordinate slice `Omega = x[0]`, and `Xi = x[2]-2x[1]+x[0]` when dim>2.
- Admissible step = project candidate onto that slice ∩ box. Rejects spend no objective evaluation.

Gap closed relative to unconstrained SNAP/S6-equivalent scripts:
mutation is no longer free. Search is an AGD operator on the declared fibre.

What the theorems do **not** do:
they do not raise `final_target_hit` counts. Holding Ω on raw BBOB coordinates is a restriction. Official numbers below show the restriction is real.
