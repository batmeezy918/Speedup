# GS254 E_EQ Block Closure — 2026-09-08

## Result
The E_EQ block was re-derived from first principles after the target gate returned `INSTRUMENTATION_MISSING`.

The baseline executable performs a 20,000,000-iteration loop using `exp(-0.005*(i mod 2048))` and a `torsion < 1e-12` threshold. It does not use the RSA-260 modulus in the computation.

The candidate executable performs a 10,000,000-iteration loop using `exp(-0.02*(i mod 1024))` and a `flow < 0.000001` threshold. It also does not use the RSA-260 modulus in the computation.

Therefore the two executables are not implementations of the same semantic function. Their elapsed-time ratio cannot establish bidirectional semantic equivalence for a factorization task.

## Gate consequence
The historical `18.533401810344827x` GS254 effective-time claim is **not elevated**.

This block is now closed as a **proven negative gate**: the obstruction is semantic-function mismatch, not merely missing timing instrumentation.

## Required next operator
A genuine E_EQ run must bind both sides to the same input and machine-checkable semantic result contract, establish result equality/reconstruction, and only then admit timing into the speedup certificate.

## Boundary
No throughput-dominance, factorization, cryptographic-break, or universal-speedup claim is supported by this artifact.
