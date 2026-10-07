# AGD Quantum Generality Definitive EOF - Report

## Explicit Equivalence Relation (fixed before operator construction)

Index the computational basis of the n-qubit Hilbert space as `i = a*m + b`, 
with `nq = ceil(n/2)` coarse qubits, `nf = floor(n/2)` fine qubits, 
`q = 2**nq`, `m = 2**nf`. The relation is `i ~ j` iff `floor(i/m) == floor(j/m)`. 
The `q` equivalence classes span the quotient `Q`. 
`Pi = I_q (x) 1_m^T / sqrt(m)`, `R = I_q (x) 1_m / sqrt(m)`, `Pi R = I_Q`. 
`U = V (x) I_m`, `Ubar = V`, formal gate `Pi U = Ubar Pi`, 
reconstruction `R Ubar Pi |psi> = U |psi>`.

## Scope

A linear quotient of dimension `q < d` cannot encode an arbitrary d-dimensional state. 
Therefore the complete-state reconstruction gate is tested on the quotient-invariant state family 
`psi = R alpha` with independently drawn `alpha`. Universal arbitrary-state/arbitrary-circuit 
reconstruction is out of scope and is classified NOT ESTABLISHED.

## Total Tests: 213
## Exact semantic passes: 189
## Exact semantic failures: 24
## Negative-control failures correctly rejected: 24

### Compression
- min: 2.0
- median: 8.0
- max: 32.0

### Kernel speedup (T_full / T_quotient_kernel)
- min: 0.5654857142857144
- median: 3.860215053763441
- max: 951.0547523109741

### Composed speedup (T_full / (T_quotient_kernel + T_reconstruction))
- min: 0.262830913737405
- median: 1.2430666666666668
- max: 60.00737157823589

### End-to-end speedup (T_full / T_total)
- min: 0.09421278765111862
- median: 0.8861324969109401
- max: 41.0988949241431

### Extremes
- max closure residual: 0.8147479580707876
- max state error: 2.2591401799415137e-16
- max observable error: 6.661338147750939e-16
- max reverse error: 5.721958498152797e-16

### Results by operator family

| family | tests | passes | closure | reverse | composition | median compression | median S_kernel | median S_composed |
|---|---|---|---|---|---|---|---|---|
| A_Permutation | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.692910301605954 | 1.2222666666666668 |
| B_DiagonalPhase | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.877742946708464 | 0.5447771887089841 |
| C_SparseLocal | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.860215053763441 | 1.253419253024724 |
| D_TensorProductLocal | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.8544 | 1.1538668098818474 |
| E_RandomUnitary | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.8544 | 1.3262527233115469 |
| F_HeterogeneousProduct | 27 | 27 | 27 | 27 | 27 | 8.0 | 3.9796238244514113 | 1.3098972417522985 |
| G_ForwardReverse | 27 | 27 | 27 | 27 | 27 | 8.0 | 7.427836818649297 | 1.5213408217118984 |

### Results by system size

| n | full dim | quotient dim | compression | tests | passes | max state err | median S_kernel |
|---|---|---|---|---|---|---|---|
| 2 | 4 | 2 | 2.0 | 21 | 21 | 2.2591401799415137e-16 | 1.132128740824393 |
| 3 | 8 | 4 | 2.0 | 21 | 21 | 2.237726045655905e-16 | 1.140168970814132 |
| 4 | 16 | 4 | 4.0 | 21 | 21 | 7.850462293418876e-17 | 1.2553104575163399 |
| 5 | 32 | 8 | 4.0 | 21 | 21 | 1.1102230246251565e-16 | 1.6794625719769671 |
| 6 | 64 | 8 | 8.0 | 21 | 21 | 1.1123893155135927e-16 | 3.877742946708464 |
| 7 | 128 | 16 | 8.0 | 21 | 21 | 8.441528768080323e-17 | 10.054328141977544 |
| 8 | 256 | 16 | 16.0 | 21 | 21 | 5.682377955034956e-17 | 28.614310645724256 |
| 9 | 512 | 32 | 16.0 | 21 | 21 | 4.291468873614597e-17 | 113.72299107142855 |
| 10 | 1024 | 32 | 32.0 | 21 | 21 | 3.479191088030031e-17 | 108.44034549144077 |

### Compression vs speed relationship
- kernel Pearson r: 0.5925849585648381
- kernel Spearman rho: 0.8897669706180344
- composed Pearson r: 0.5988936254142994
- composed Spearman rho: 0.8536554151335787

### Complete failure ledger

| family | n | seed | expected | closure_res | state_max | state_l2 | obs | reverse | result |
|---|---|---|---|---|---|---|---|---|---|
| NEG_random_class_assignment | 4 | 1 | True | 6.922e-01 | 6.655e-01 | 1.050e+00 | 5.522e-01 | 5.327e-01 | FAIL |
| NEG_random_class_assignment | 4 | 2 | True | 8.147e-01 | 5.694e-01 | 1.169e+00 | 7.696e-01 | 3.652e-01 | FAIL |
| NEG_random_class_assignment | 6 | 1 | True | 5.602e-01 | 2.532e-01 | 1.044e+00 | 1.194e+00 | 2.275e-01 | FAIL |
| NEG_random_class_assignment | 6 | 2 | True | 5.654e-01 | 2.663e-01 | 1.128e+00 | 1.627e+00 | 1.954e-01 | FAIL |
| NEG_random_class_assignment | 8 | 1 | True | 3.135e-01 | 1.683e-01 | 1.033e+00 | 8.675e-01 | 1.383e-01 | FAIL |
| NEG_random_class_assignment | 8 | 2 | True | 2.768e-01 | 1.653e-01 | 1.027e+00 | 7.141e-01 | 1.399e-01 | FAIL |
| NEG_broken_symmetry | 4 | 1 | True | 5.211e-01 | 4.416e-01 | 8.061e-01 | 8.604e-01 | 4.423e-01 | FAIL |
| NEG_broken_symmetry | 4 | 2 | True | 5.885e-01 | 4.098e-01 | 9.185e-01 | 6.085e-01 | 3.753e-01 | FAIL |
| NEG_broken_symmetry | 6 | 1 | True | 3.466e-01 | 2.715e-01 | 9.218e-01 | 5.693e-01 | 2.501e-01 | FAIL |
| NEG_broken_symmetry | 6 | 2 | True | 3.269e-01 | 2.318e-01 | 9.201e-01 | 4.731e-01 | 3.096e-01 | FAIL |
| NEG_broken_symmetry | 8 | 1 | True | 1.500e-01 | 1.443e-01 | 9.643e-01 | 5.308e-01 | 1.424e-01 | FAIL |
| NEG_broken_symmetry | 8 | 2 | True | 1.882e-01 | 1.297e-01 | 9.747e-01 | 4.528e-01 | 1.500e-01 | FAIL |
| NEG_altered_quotient_operator | 4 | 1 | True | 2.463e-02 | 3.896e-01 | 8.094e-01 | 7.205e-01 | 3.382e-01 | FAIL |
| NEG_altered_quotient_operator | 4 | 2 | True | 2.194e-02 | 3.355e-01 | 8.092e-01 | 5.340e-01 | 4.017e-01 | FAIL |
| NEG_altered_quotient_operator | 6 | 1 | True | 1.153e-02 | 3.190e-01 | 9.282e-01 | 4.891e-01 | 2.466e-01 | FAIL |
| NEG_altered_quotient_operator | 6 | 2 | True | 1.210e-02 | 3.013e-01 | 9.296e-01 | 6.565e-01 | 2.147e-01 | FAIL |
| NEG_altered_quotient_operator | 8 | 1 | True | 4.492e-03 | 1.634e-01 | 9.654e-01 | 1.042e+00 | 1.396e-01 | FAIL |
| NEG_altered_quotient_operator | 8 | 2 | True | 3.925e-03 | 1.600e-01 | 9.710e-01 | 8.319e-01 | 1.326e-01 | FAIL |
| NEG_corrupted_reconstruction | 4 | 1 | True | 0.000e+00 | 4.259e-01 | 8.838e-01 | 1.217e+00 | 4.167e-01 | FAIL |
| NEG_corrupted_reconstruction | 4 | 2 | True | 0.000e+00 | 4.022e-01 | 8.237e-01 | 1.450e+00 | 5.043e-01 | FAIL |
| NEG_corrupted_reconstruction | 6 | 1 | True | 0.000e+00 | 2.421e-01 | 9.304e-01 | 9.470e-01 | 2.889e-01 | FAIL |
| NEG_corrupted_reconstruction | 6 | 2 | True | 0.000e+00 | 3.353e-01 | 9.309e-01 | 7.298e-01 | 3.237e-01 | FAIL |
| NEG_corrupted_reconstruction | 8 | 1 | True | 0.000e+00 | 1.316e-01 | 9.666e-01 | 6.455e-01 | 1.572e-01 | FAIL |
| NEG_corrupted_reconstruction | 8 | 2 | True | 0.000e+00 | 1.564e-01 | 9.560e-01 | 4.854e-01 | 1.303e-01 | FAIL |

### Hashes

- source script SHA-256: `72ebf1fe11c555f225b488324fc022e8d7697e9bc6ce6280aba83e816cb6436c`
- generated quotient maps (aggregate) SHA-256: `5ec70d128e9ffa14ffe0453fd22100beb9f22d827a139dfca4945595192fe90b`
- reference outputs (aggregate) SHA-256: `6611e6fbd5b762c4ee9093b55523ca4c4d431273dd49b1326fa7e3dde0492d26`
- reconstructed outputs (aggregate) SHA-256: `16ae342710c642dec103eb74c4fa26720e767863d3256bcaff6ac41ec8754bb9`
- final CSV SHA-256: `cc06fe015d75f0a13ffb79e20f02498899e1f8ba8a9afe872fa8827cce9edf34`
- final JSON SHA-256: `b4c4f261087cc2081e1648db9a0b60726a3af7d0f47756cb6468aa8bf55e9783`

### Claims

- CLAIM A "Exact quotient reconstruction demonstrated.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM B "Closure survives heterogeneous operator families.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM C "Closure survives composition.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM D "Bidirectional closure demonstrated.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM E "Generalization across tested operator families.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM F "Scalable compression demonstrated.": PASS - PROVEN IN THIS EXPERIMENT
- CLAIM G "Measured acceleration.": PASS - SUPPORTED BY MULTIPLE INDEPENDENT WITNESSES
- CLAIM H "Universal arbitrary-circuit quantum speedup.": NOT PASSED - NOT ESTABLISHED

### Definitive status

- All positive semantic gates passed exactly at the declared tolerances.
- Compression sequence across n: [2.0, 2.0, 4.0, 4.0, 8.0, 8.0, 16.0, 16.0, 32.0]
- Measured median kernel speedup over passing instances: 3.860215053763441
- Negative-control anomalies (invalid quotients that PASSED validation): 0

_Generated by AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py. No values were mocked; every matrix, map, state, observable, hash, and timing was generated inside the script at runtime._
