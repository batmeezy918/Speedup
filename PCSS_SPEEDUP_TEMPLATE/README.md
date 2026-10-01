# PCSS speedup template

Reusable experimental formalization skeleton. Do not bake a numeric speedup into this tree.

Each specimen gets its own RUN_ID, hashes, environment, gates, and Lean obligations.

Flow:

INPUT -> ADMISSIBILITY -> FORWARD Q -> REDUCED STATE -> CANDIDATE
-> REVERSE Qinv -> RECONSTRUCTION -> INVARIANT -> CORRECTNESS
-> REPRODUCIBILITY -> PERFORMANCE -> CERTIFICATE -> LEAN

Acceptance:

A = I and R and Q and Qinv and Omega and X and L

Unknown or false => QUARANTINE.

Lean formalizes the supplied certificate. Lean does not measure the device.

First specimen: evidence/certificates/PCSS_NEON_GEMM_N512_20261001T052954Z
Next intended specimen: SIM2XR, still blocked on L until a bound certificate exists.
