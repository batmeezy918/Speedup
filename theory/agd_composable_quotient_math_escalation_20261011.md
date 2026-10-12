# AGD / MuNi Mathematical Escalation: Composable Quotient Execution

**Date:** 2026-10-11  
**Status:** Proposed formalization with conditional proofs; not yet Lean-checked in this branch and not a claim of priority-verified novelty.  
**Evidence anchor:** [normalized recent evidence](../evidence/normalized/normalized_recent_evidence_20261011.md)

## Executive claim

The strongest mathematical next step is not a larger speedup slogan. It is a *composable admissible-quotient contract*: an optimization may run only when its state abstraction preserves the required transition semantics and observables; quantitative approximation is allowed only when a proven accumulated error bound fits the declared tolerance; and the performance claim is accepted only from comparable end-to-end measurements. If any proof gate fails, execution uses the unoptimized path.

The basic ingredients—quotients, abstraction, structured linear algebra, numerical error bounds, and compiler semantic preservation—have substantial prior art. The candidate contribution is their particular synthesis into one machine-checkable, fail-closed optimization certificate. Novelty/priority requires a separate, systematic literature review.

## 1. Mathematical setting

Let:
- \(X_i\) be the concrete state space at pipeline stage \(i\);
- \(Q_i\) be its quotient/abstract state space;
- \(A_i(x)\) be the admissibility predicate;
- \(F_i:X_i\to X_{i+1}\) be the concrete transition;
- \(\widehat F_i:Q_i\to Q_{i+1}\) be the optimized transition;
- \(\pi_i:X_i\to Q_i\) be the abstraction map;
- \(H:X_k\to Y\) and \(\widehat H:Q_k\to Y\) be the concrete and abstract observations.

An abstraction is not automatically valid just because the code is smaller or a tensor looks separable. It must preserve the semantics that the application actually requires.

### Admissible Quotient Simulation (AQS) obligations

For each stage, prove:

**A1 — admissibility preservation**
\[
A_i(x)\implies A_{i+1}(F_i(x)).
\]

**A2 — transition commutation on admissible states**
\[
A_i(x)\implies
\pi_{i+1}(F_i(x))=\widehat F_i(\pi_i(x)).
\]

**A3 — observation preservation**
\[
A_k(x)\implies H(x)=\widehat H(\pi_k(x)).
\]

The diagram in A2 must commute for every state covered by the theorem, not merely for sampled test cases. If a required full-state output distinguishes states collapsed by \(\pi\), A3 fails: either retain the missing information in the quotient or narrow the claim to an invariant observable.

## 2. Theorem: compositional exactness

**Theorem (AQS composition, conditional).** Suppose A1 and A2 hold for every stage \(i=0,\ldots,k-1\), the initial concrete state is admissible, and A3 holds for the final observation. Then the abstract pipeline produces the same declared observation as the concrete pipeline:
\[
H(F_{k-1}\circ\cdots\circ F_0(x_0))
=
\widehat H(\widehat F_{k-1}\circ\cdots\circ\widehat F_0(\pi_0(x_0))).
\]

**Proof sketch.** Induct on the stage index. At stage zero the abstract state is \(\pi_0(x_0)\). Assume the abstract state after stage \(i\) equals \(\pi_i(x_i)\). By A1, the next concrete state remains admissible. By A2, its abstraction equals \(\widehat F_i(\pi_i(x_i))\), which is precisely the next abstract state. Thus the equality holds after each stage. At the final stage apply A3. QED.

**Interpretation.** Several individually justified transformations can be composed without losing the stated guarantee, provided each stage's admissibility and abstraction contracts match at their interfaces. A certificate for an isolated kernel does not alone certify a whole application pipeline.

This theorem is an elementary consequence of commuting-diagram/forward-simulation reasoning; its statement is provided as a clean target for the AGD contract, not as a priority claim.

## 3. Theorem: quantitative approximation budget

Exact commutation may be unavailable for floating-point execution. Let the abstract state metric be \(d\); assume the abstract transition is Lipschitz with constant \(L\), and the one-step abstraction defect is bounded:
\[
d(\pi(F(x)),\widehat F(\pi(x)))\leq\delta.
\]
Let \(e_t=d(\pi(x_t),\widehat x_t)\), with \(e_0=0\). Then:
\[
e_{t+1}\leq L e_t+\delta,
\]
and, for \(L\ne1\),
\[
e_t\leq\delta\sum_{j=0}^{t-1}L^j
=\delta\frac{L^t-1}{L-1}.
\]
For \(L=1\), \(e_t\leq t\delta\). For \(0\leq L<1\), the bound is \(e_t\leq\delta(1-L^t)/(1-L)\).

If the final observable is \(K\)-Lipschitz and its own implementation adds at most \(\epsilon_{out}\), then the end-to-end error bound is
\[
\epsilon_{E2E}(t)\leq K e_t+\epsilon_{out}.
\]
A positive-tolerance claim is admissible only if this derived bound is at most the declared tolerance for every state and horizon covered by the claim. Measured max error on finite inputs is not a substitute for the bound.

**Immediate consequence for the existing ledger.** The normalized report records O2b with \(\max\_err=3.15199\times10^{-7}\) and \(\max\_tol=9.99\times10^{-10}\), i.e. about **315.514 times the tolerance**. That witness fails this tolerance gate. It cannot be called tolerance-certified, much less bit-exact, until the claim is corrected or a valid new proof/receipt establishes a different error result.

The need to reason about floating-point error and stability is standard numerical analysis; see Higham's *Accuracy and Stability of Numerical Algorithms* (https://epubs.siam.org/doi/10.1137/1.9780898718027.ch1).

## 4. Cost theorem: when a quotient is actually faster

Let \(C_b(W)\) be reference end-to-end cost for workload \(W\), \(C_q(W)\) optimized computation cost, and \(G(W)\) the combined admission-check, validation, reconstruction, and dispatch overhead. A valid speedup is:
\[
S(W)=\frac{C_b(W)}{C_q(W)+G(W)},
\]
provided both runs implement the same declared observable and include the same boundary of work. This is a cost identity, not a proof that \(S>1\); that inequality must be measured.

For a conventional Amdahl decomposition where fraction \(p\) of baseline runtime is accelerated by factor \(r\),
\[
S=\frac{1}{(1-p)+p/r}.
\]
Thus \(p\geq1-1/S\). For the recorded end-to-end ratio 67.387039x, the Amdahl decomposition implies at least approximately **98.516%** of baseline runtime must belong to work that is accelerated or eliminated, assuming the decomposition and timing boundary apply. The optimized run is about **1.484%** of baseline elapsed time. This is a calibration, not a universal complexity theorem.

An optimization that must reconstruct the full concrete state at every stage may erase the gain. Keep a compressed representation across stages only when the next operation and the final required observable support it. If reconstruction is needed only at the end, charge it once; if it is needed every step, charge it every step.

### Important guard on the current structured-operator claim

Kronecker/separable structure can reduce work, but structure alone does not justify discarding independent state components. For example,
\[
(A\otimes B)\operatorname{vec}(X)=\operatorname{vec}(BXA^T)
\]
is a standard identity. It permits an implementation that avoids materializing the full Kronecker matrix; it does **not**, by itself, prove that arbitrary columns of \(X\) are identical or can be removed. The quotient needs an invariant/subspace proof plus output sufficiency.

Relevant background: Cornell's matrix-computations notes on separability and Kronecker products (https://www.cs.cornell.edu/courses/cs6210/2025fa/lec/2025-09-03.html), and Van Loan's survey chapter on tensor-structured matrix problems (https://doi.org/10.1007/978-3-319-49887-4_1).

The current receipt names parameters \(d,r,m\), but that notation alone does not establish which parameter counts redundant equivalent fibers. Do not infer a theoretical \(m\)-fold bound from the variable name. Confirm the exact operator and parameter semantics in the benchmark source before doing so.

## 5. Native implementation refinement is a separate theorem

To connect a Lean theorem about an algebraic model to a C binary, introduce a relation \(R(c,a)\) between concrete machine states \(c\) and abstract mathematical states \(a\). At minimum, establish:

1. **Initialization:** the encoded native initial state is related to the model's initial state.
2. **Step simulation:** each native transition maps to the corresponding model transition (or to a justified finite sequence of model transitions).
3. **Observation agreement:** native outputs satisfy the proved observation relation.
4. **Arithmetic contract:** rounding mode, contraction/FMA behavior, reassociation, overflow, NaN/Inf handling, signed zero, and any flush-to-zero behavior are either excluded by preconditions or modeled.
5. **Build provenance:** source hash, compiler/version/flags, target, linked-library versions, and binary hash match the tested receipt.

Without this bridge, the accurate status is *formal partial + locally measured*, not verified-native. Standard Lean axioms such as Quot.sound, propext, and sometimes Classical.choice are not by themselves defects; the actual theorem dependencies and absence of unproved project-specific axioms/sorryAx must be audited. See the Lean reference on axioms: https://lean-lang.org/doc/reference/latest/Axioms/.

## 6. Proposed proof-carrying optimization certificate

Each optimized run should emit a certificate with these fields:

- **Problem identity:** workload/input digest, operator definition, dimensions, precision, required observable.
- **Admissibility:** predicate, invariant witness, assumptions, and fallback decision.
- **Semantic proof:** AQS/commuting theorem identifier, native refinement theorem identifier, Lean version, dependency/axiom listing.
- **Numerical proof:** exact or tolerance mode; norm/metric; horizon; local defect; Lipschitz/stability constants; computed end-to-end bound.
- **Performance receipt:** raw repetitions, timing boundary, warmups, ordering/interleave policy, baseline implementation, machine/OS/governor/compiler, source and binary hashes, median plus range/dispersion, and A/A noise check.
- **Failure semantics:** failed admission or certificate means baseline execution, not silent acceptance of an unproved optimization.

Suggested verdict lattice:
- **EXACT_FORMAL_AND_NATIVE:** exact observation preservation plus native refinement proved.
- **TOLERANCE_FORMAL_AND_NATIVE:** proven global error bound within tolerance plus native refinement.
- **FORMAL_PARTIAL_MEASURED_LOCAL:** algebraic theorem and local timings, native refinement missing.
- **MEASURED_ONLY:** performance and finite correctness evidence only.
- **REJECTED_GATE:** invariant, semantics, tolerance, or provenance gate failed; optimized claim forbidden.

These labels are proposals and should be mapped to the repository's existing claim taxonomy rather than introduced as conflicting names without reconciliation.

## 7. Calibration against current evidence

The normalized 2026-10-11 report records:
- MUNI v4 end-to-end: **67.387039x** (68.325552 ms / 1.013927 ms), reported max absolute error zero in the sampled run.
- Run loop: **69.012892x** (68.475875 ms / 0.992219 ms).
- Formal-gap structured baseline: **68.329596x**; dense reference: **6703.995497x**.
- Nine-session structured ratio median: **78.348905x**, range **24.828234x–146.954659x**.
- Adversarial suite: **23/23**; property fuzz: **20,000 tests, zero observed violations**.

Interpretation:
- The first three support large local speedups in the named workload regime.
- The dense comparison is a structural reference, not a fair claim of superiority over generic optimized BLAS.
- The nine-session range shows material environmental/session variation; report median and range, and investigate timing drift.
- Finite fuzz/adversarial results are empirical evidence, not universal proofs.
- The open positive-tolerance witness, missing native-refinement artifact, assumed invariant, and stale checksum must remain visible.
- Do not multiply unrelated speedups together.

## 8. Prior-art / novelty discipline

Relevant existing work includes:
- Abstract-interpretation quotients (“The quotient of an abstract interpretation,” *Theoretical Computer Science*, 1998: https://doi.org/10.1016/S0304-3975(97)00137-0).
- Kronecker and low-rank structured computation (Van Loan, 2017: https://doi.org/10.1007/978-3-319-49887-4_1).
- Certified computation and proof-carrying results (“Deductive Runtime Certification,” 2005: https://doi.org/10.1016/j.entcs.2004.01.035).
- A recent preprint directly considers formal performance and compile-time guarantees for compiler optimization heuristics (August 2026: https://arxiv.org/abs/2608.20137).

Therefore, the basic ideas of quotient abstraction, semantic preservation, error bounds, and performance modeling are not novel in isolation. The hypothesis to investigate is whether AGD's **specific operational composition**—admissibility gate + state quotient + explicit tolerance budget + native-refinement obligation + fail-closed fallback + measurement receipt—adds a useful, formally integrated contract beyond these separate lines of work. A novelty claim requires a broader search and a precise comparison table.

## 9. Next proof and experiment gates

1. Write the AQS definitions and composition theorem in Lean with explicit assumptions and a reproducible axiom/sorry audit.
2. Add a counterexample test showing that a non-invariant or output-distinguishing state is rejected, not quotiented.
3. Resolve O2b: either repair the measured error/tolerance mismatch or downgrade/remove the tolerance claim.
4. Build the C-to-model relation and bind it to the exact source/binary/compiler receipt.
5. Regenerate the stale checksum only after the measured log is final.
6. Re-run the structured kernel with source-pinned reference implementations and matching end-to-end boundaries. Eigen's benchmark guide documents its CMake/Google Benchmark workflow: https://libeigen.gitlab.io/pages/how_to_run_the_benchmark_suite/.
7. Run MLPerf Inference only for a supported end-to-end model benchmark; follow its official dataset, accuracy, and timing rules: https://github.com/mlcommons/inference and https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc.

**Execution status:** this document is a mathematical escalation/verification target. It does not claim that the two public benchmark repositories were successfully cloned or that official public-suite runs have completed. The remote host was offline during that attempt.
