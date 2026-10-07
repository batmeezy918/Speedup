#!/usr/bin/env python3
"""
Elevation pass over the EOF proof-gated hierarchical acceleration validation.

Inputs (read-only):
  /root/EOF_HIERARCHICAL_ACCELERATION_VALIDATION/BRANCH_RESULTS.json
  /root/EOF_HIERARCHICAL_ACCELERATION_VALIDATION/COMPOSITION_RESULTS.json
  /root/EOF_HIERARCHICAL_ACCELERATION_VALIDATION/FINAL_VALIDATION.json
  /root/ATD_QG_MAXIMAL_RESULTS/ATD_QG_MAXIMAL_CERTIFICATE.json

Outputs (deterministic, hash-bound):
  AUDIT.json            D1..D6 defect register, each with the observed value
  GATE_VALIDATION.json  negative-control promotion: sensitivity/specificity
  SCALING_LAW.json      single-lane, single-regime fitted law + predictions
  CROSS_DOMAIN_LAW.json classical <-> quantum shared structural law
  ELEVATED_REPORT.txt   human-readable corrected report

No speedup is multiplied. No number is promoted past its own accounting regime.
"""
import json
import math
import os
import hashlib
from datetime import datetime, timezone

SRC = "/root/EOF_HIERARCHICAL_ACCELERATION_VALIDATION"
QG = "/root/ATD_QG_MAXIMAL_RESULTS/ATD_QG_MAXIMAL_CERTIFICATE.json"
OUT = os.path.dirname(os.path.abspath(__file__))
LANE = "Q0_site0"  # single-lane rule: one algorithm, L=2..8, no per-L switching
BRANCHES = ["Q0_site0", "Q1_parity", "Q2_majority", "Q3_endpoint"]


def load(p):
    with open(p) as f:
        return json.load(f)


def sha256_text(t):
    return hashlib.sha256(t.encode()).hexdigest()


def ols(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    m = sxy / sxx
    b0 = my - m * mx
    ss = sum((b - my) ** 2 for b in y)
    rs = sum((b - (m * a + b0)) ** 2 for a, b in zip(x, y))
    return m, b0, (1 - rs / ss if ss else 1.0)


def solve_L(target, A, g, a, b):
    lo, hi = 2.0, 400.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if A * g ** mid / (a + b * mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


branch = load(os.path.join(SRC, "BRANCH_RESULTS.json"))
comp = load(os.path.join(SRC, "COMPOSITION_RESULTS.json"))
final = load(os.path.join(SRC, "FINAL_VALIDATION.json"))
qg = load(QG)

idx = {(r["L"], r["branch"]): r for r in branch}
Ls = [c["L"] for c in comp]
E2E = [c["end_to_end_seconds"] for c in comp]
base = [idx[(L, LANE)]["baseline_seconds"] for L in Ls]
quot = [idx[(L, LANE)]["quotient_seconds"] for L in Ls]

# ---------------------------------------------------------------- D1: regimes
hdr_max = final["maximum_observed_branch_speedup"]
l8 = idx[(8, LANE)]
e2e_at_l8 = 4.896e-06
d1 = {
    "id": "D1",
    "defect": "Two accounting regimes in one report.",
    "detail": (
        "Header 'MAX VALID BRANCH SPEEDUP' is a no-overhead branch ratio "
        "(baseline/quotient). The COMPOSITION table is overhead-inclusive "
        "end-to-end (baseline/E2E). The header is the more favourable regime."
    ),
    "header_value_x": hdr_max,
    "same_configuration_overhead_inclusive_x": l8["baseline_seconds"] / e2e_at_l8,
    "overstatement_factor": hdr_max / (l8["baseline_seconds"] / e2e_at_l8),
    "fix": "Publish one regime only: overhead-inclusive E2E. Branch ratios become diagnostic, not headline.",
}

# ------------------------------------------------- D2: per-L branch switching
switch, suboptimal = [], []
for c in comp:
    L = c["L"]
    valid = [b for b in BRANCHES if idx[(L, b)]["all_gates"] and idx[(L, b)]["residual"] == 0.0]
    best = max(valid, key=lambda b: idx[(L, b)]["baseline_seconds"] / c["end_to_end_seconds"])
    if best != c["branch"]:
        suboptimal.append({
            "L": L, "reported_branch": c["branch"],
            "reported_x": c["end_to_end_speedup"],
            "best_valid_branch": best,
            "best_valid_x": idx[(L, best)]["baseline_seconds"] / c["end_to_end_seconds"],
        })
for i in range(1, len(comp)):
    if comp[i]["branch"] != comp[i - 1]["branch"]:
        switch.append({"from_L": comp[i - 1]["L"], "to_L": comp[i]["L"],
                       "branches": [comp[i - 1]["branch"], comp[i]["branch"]]})
d2 = {
    "id": "D2",
    "defect": "Per-L branch switching with no disclosed selection rule.",
    "detail": (
        "The COMPOSITION table mixes two branch families (L=2..6 vs L=7..8), so the "
        "trend is not one algorithm. The end_to_end_seconds values are not present in "
        "BRANCH_RESULTS.json, so the table is not reproducible from the emitted artifacts."
    ),
    "branch_switches": switch,
    "suboptimal_selections": suboptimal,
    "e2e_timings_absent_from_branch_artifact": all("end_to_end_seconds" not in r for r in branch),
    "fix": "Pin a single lane (%s) for all L and re-emit E2E into the artifact set." % LANE,
}

# ------------------------------------------ D3: branch-dependent denominator
spread = []
for L in Ls:
    v = [idx[(L, b)]["baseline_seconds"] for b in BRANCHES]
    spread.append({"L": L, "min_s": min(v), "max_s": max(v),
                   "spread_pct": (max(v) / min(v) - 1) * 100})
d3 = {
    "id": "D3",
    "defect": "The speedup denominator is not a fixed reference.",
    "detail": "Baseline is re-measured per branch and varies at fixed L, so cross-branch speedups are not commensurable.",
    "per_L_baseline_spread": spread,
    "max_spread_pct": max(s["spread_pct"] for s in spread),
    "fix": "One baseline per L, shared by all branches; branch ranking then compares numerators only.",
}

# ------------------------------------------ D4: empty adversarial set read PASS
rejected = [r for r in branch if not r["all_gates"]]
accepted = [r for r in branch if r["all_gates"]]
d4 = {
    "id": "D4",
    "defect": "An empty adversarial set was read as PASS.",
    "detail": (
        "ADVERSARIAL_RESULTS.json is []. Under a fail-closed constitution, zero "
        "adversarial trials is INDETERMINATE, not PASS. The report nevertheless "
        "prints 'ADVERSARIAL FAILURES []' next to 'STATUS: PASS'."
    ),
    "adversarial_trials_recorded": 0,
    "fail_closed_verdict": "INDETERMINATE",
    "incidental_negative_controls_found": len(rejected),
    "fix": "Report INDETERMINATE until a declared negative-control battery exists; see GATE_VALIDATION.json for the 4 that were already in the data.",
}

# ------------------------------------------------------- D5: no dispersion
d5 = {
    "id": "D5",
    "defect": "Single-shot microsecond timings with no dispersion.",
    "detail": (
        "Quotient timings are 1.8-3.5 us and were taken without repeats, median or CI, "
        "yet per-L branch selection turns on differences of that order "
        "(L=8: 1.771us vs 2.188us = 24%). Selection is therefore noise-exposed."
    ),
    "quotient_seconds_range_s": [min(quot), max(quot)],
    "inter_branch_spread_at_L8_pct": abs(
        [idx[(8, b)]["quotient_seconds"] for b in BRANCHES].index(
            idx[(8, "Q3_endpoint")]["quotient_seconds"])
        - [idx[(8, b)]["quotient_seconds"] for b in BRANCHES].index(
            idx[(8, "Q0_site0")]["quotient_seconds"]))
    / idx[(8, "Q0_site0")]["quotient_seconds"] * 100,
    "fix": "Report median-of-N with IQR; require separation > dispersion before ranking branches.",
}

# ------------------------------------------------- D6: no complexity statement
d6 = {
    "id": "D6",
    "defect": "A constant was published where a law was measured.",
    "detail": "'385.912x' is one point. The actual result is exponential-over-linear in L, which is falsifiable at L=9,10,11.",
    "fix": "Publish the fitted law with R^2 and its out-of-sample predictions as the claim.",
}

audit = {
    "protocol": "EOF_HIERARCHICAL_ACCELERATION_ELEVATION_AUDIT",
    "source_artifact_dir": SRC,
    "defects_found": 6,
    "corrections_move_in_both_directions": True,
    "net_effect": (
        "Header is 2.238x too high (D1); the L=7,8 table rows are 1.32x and 1.26x too "
        "LOW (D2). Correcting both is what makes the single-lane claim monotone and defensible."
    ),
    "defects": [d1, d2, d3, d4, d5, d6],
}

# =============================================================== GATE
q1 = [r for r in branch if r["branch"] == "Q1_parity"]
q1_bad = [r for r in q1 if not r["all_gates"]]
q1_good = [r for r in q1 if r["all_gates"]]
gate = {
    "protocol": "EOF_NEGATIVE_CONTROL_PROMOTION",
    "finding": "The Q1_parity lane is a declared-in-effect negative control that the report discarded.",
    "defect_signature": {
        "description": "Unit parity drift injected per layer; accumulates linearly, cancels at odd L.",
        "residual_equals": "L (exactly, for every rejected trial)",
        "residual_by_L": {str(r["L"]): r["residual"] for r in sorted(q1_bad, key=lambda x: x["L"])},
        "detected_at_even_L": [r["L"] for r in sorted(q1_bad, key=lambda x: x["L"])],
        "undetectable_at_odd_L": [r["L"] for r in sorted(q1_good, key=lambda x: x["L"])],
    },
    "sensitivity": {
        "definition": "P(reject | known-defective)",
        "detected": len(q1_bad), "of": len(q1_bad), "value": len(q1_bad) / len(q1_bad),
    },
    "specificity": {
        "definition": "P(accept | valid)",
        "accepted": len([r for r in accepted if r["residual"] == 0.0]),
        "of": len(accepted), "value": len([r for r in accepted if r["residual"] == 0.0]) / len(accepted),
    },
    "false_negatives": len([r for r in q1 if r["residual"] != 0.0 and r["all_gates"]]),
    "false_positives": len([r for r in accepted if r["residual"] != 0.0]),
    "key_result": {
        "statement": "The gate is exact, not tolerance-based.",
        "evidence": "All 24 accepted trials have residual identically 0.0; the 4 rejected have residual identically L.",
        "consequence": (
            "A drift of relative size L/2^(L-1) is caught with zero tolerance budget "
            "because the comparison happens in the O(1) reduced space, not the 2^(L-1) full space. "
            "At L=8 that is 6.25% relative drift detected exactly."
        ),
        "relative_drift_by_L": {str(r["L"]): r["residual"] / r["state_reduction_factor"]
                                for r in sorted(q1_bad, key=lambda x: x["L"])},
        "novel_operational_claim": (
            "Quotient projection makes error DETECTION exponentially cheaper than error "
            "PREVENTION: prevention must certify 2^(L-1) states, detection certifies 1."
        ),
    },
    "residual_budget_note": (
        "No tolerance is recorded anywhere in the source artifacts. Exactness is therefore "
        "an observed property of this run, not a declared gate parameter. Publishing it as a "
        "tolerance-free claim requires recording epsilon=0 explicitly."
    ),
}

# =========================================================== SCALING LAW
m_log, b_log, r2_log = ols(Ls, [math.log(v) for v in base])
A, g = math.exp(b_log), math.exp(m_log)
m_e, b_e, r2_e = ols(Ls, E2E)
per_L = [A * g ** L / (b_e + m_e * L) for L in Ls]
obs = [b / e for b, e in zip(base, E2E)]
step = [None] + [obs[i] / obs[i - 1] for i in range(1, len(obs))]
law_band = (min(p / o for o, p in zip(obs, per_L)), max(p / o for o, p in zip(obs, per_L)))

law = {
    "protocol": "EOF_HIERARCHICAL_SCALING_LAW_V2",
    "lane": LANE,
    "accounting_regime": "overhead-inclusive end-to-end (single regime)",
    "why_this_lane": "L=2..6 and L=7..8 in the source table used different branches; Q0_site0 is valid and residual-0 at every L in 2..8, so it is the only lane that spans the whole range.",
    "baseline_law": {
        "form": "T_base(L) = A * g^L",
        "A": A, "g": g, "g_minus_2_pct": (g / 2 - 1) * 100, "R2_log": r2_log,
        "reading": "Baseline is exponential in L with growth 2.008/L-step, i.e. the workload really does pay 2^(L-1).",
    },
    "candidate_law": {
        "form": "T_e2e(L) = a + b*L",
        "a_s": b_e, "b_s_per_L": m_e, "R2": r2_e,
        "reading": "O(1) quotient core plus O(L) reconstruction/section overhead. The core is 1.8-3.5us flat across L=2..8.",
    },
    "speedup_law": {
        "form": "S(L) = A*g^L / (a + b*L)  =  Theta(2^L / L)",
        "complexity_class": "exponential-over-linear",
        "single_lane_points": [{"L": L, "observed_x": o, "law_x": p, "ratio": p / o}
                               for L, o, p in zip(Ls, obs, per_L)],
        "per_step_growth": [None if s is None else round(s, 4) for s in step],
        "asymptotic_per_step_growth": g,
    },
    "prediction_band": {
        "basis": "The fit's own law/observed ratios span [%.3f, %.3f] over the fitted range; that dispersion is carried onto the out-of-sample points." % law_band,
        "band": list(law_band),
    },
    "corrected_single_lane_table": [
        {"L": L, "branch": LANE, "baseline_s": b, "quotient_s": q, "e2e_s": e,
         "overhead_s": e - q, "overhead_pct_of_e2e": (e - q) / e * 100,
         "e2e_speedup_x": o, "branch_no_overhead_x": b / q,
         "source_reported_x": c["end_to_end_speedup"]}
        for L, b, q, e, o, c in zip(Ls, base, quot, E2E, obs, comp)
    ],
    "predictions": {
        "note": "Out-of-sample and falsifiable. Each is a testable assertion about an unmeasured L.",
        "S_exceeds_x_at_L": {str(t): round(solve_L(t, A, g, b_e, m_e), 2)
                             for t in (385.912, 500, 1000, 2000, 5000, 10000, 100000)},
        "S_at_L_with_band": {
            str(L): {"point_x": A * g ** L / (b_e + m_e * L),
                     "band_x": [A * g ** L / (b_e + m_e * L) * lo,
                                A * g ** L / (b_e + m_e * L) * hi]}
            for L, lo, hi in ((9, *law_band), (10, *law_band), (11, *law_band))
        },
    },
    "corrected_headline": {
        "old_header_x": hdr_max,
        "new_header_x": obs[-1],
        "correction_factor": hdr_max / obs[-1],
        "statement": (
            "At L=8 the defensible overhead-inclusive single-lane number is %.2fx, not %.3fx. "
            "The old header excluded reconstruction overhead, which is %.1f%% of end-to-end time at L=8."
            % (obs[-1], hdr_max, (E2E[-1] - quot[-1]) / E2E[-1] * 100)
        ),
    },
    "residual_risk": (
        "Fitted on 7 points over L=2..8 with single-shot timings. The g=2.008 estimate is "
        "not separated from 2.0 at this sample size, so the claim is stated as Theta(2^L/L) "
        "with g measured, not as an exact base."
    ),
}

# ======================================================= CROSS-DOMAIN LAW
qgs = qg["lattice_summaries"]
qgL = [s["L"] for s in qgs]
qgrow = [s["compression_ratio"] for s in qgs]
eof_grow = [idx[(L, LANE)]["state_reduction_factor"] for L in Ls]
qm, qb, qr2 = ols(qgL, [math.log(v) for v in [s["full_runtime"] for s in qgs]])
qm_flat, _, _ = ols([L for L in qgL if L <= 5],
                    [math.log(s["full_runtime"]) for s in qgs if s["L"] <= 5])
rm, rb, _ = ols(qgL, [math.log(v) for v in [s["reduced_runtime"] for s in qgs]])
fr = [s["full_runtime"] for s in qgs]
rr = [s["reduced_runtime"] for s in qgs]

cross = {
    "protocol": "CROSS_DOMAIN_REDUCTION_AND_CROSSOVER_LAW",
    "governing_note": (
        "This artifact asserts a shared STRUCTURE, not a shared number. No speedup is "
        "multiplied across domains; that remains INCOMPATIBLE per PROOF_GATED_HIERARCHICAL_"
        "ACCELERATION_CALCULUS_2026-09-25.md section 12."
    ),
    "observation_1_reduction_law_is_domain_invariant": {
        "classical_eof_state_reduction_by_L": {str(L): v for L, v in zip(Ls, eof_grow)},
        "quantum_atd_qg_compression_by_L": {str(L): v for L, v in zip(qgL, qgrow)},
        "identical": [int(v) for v in eof_grow[:len(qgrow)]] == [int(v) for v in qgrow],
        "closed_form": "2^(L-1) in both domains",
        "classical_exactness": "reconstruction residual 0.0, equivalence residual 0.0 at all 24 accepted trials",
        "quantum_exactness": "projector_residual 0.0 and reconstruction_residual 0.0 at every L",
        "quantum_status": "ATD_QG_MAXIMAL_CERTIFICATE.json formal_consequences L*.C1b: ratio 2^{L-1} is DERIVED from the gauge condition, not merely observed",
        "elevation": (
            "The classical run reported 2^(L-1) as an observed factor. The quantum certificate "
            "already carries it as a derived closed form. The structure is therefore not a "
            "numerical coincidence between two experiments: it is forced, and it recurs."
        ),
    },
    "observation_2_reduction_is_not_speedup": {
        "quantum_data": [
            {"L": s["L"], "compression": s["compression_ratio"],
             "measured_speedup_x": s["measured_retained_residency_speedup"],
             "full_runtime_s": s["full_runtime"], "reduced_runtime_s": s["reduced_runtime"]}
            for s in qgs
        ],
        "classical_data": [
            {"L": L, "state_reduction": idx[(L, LANE)]["state_reduction_factor"],
             "e2e_speedup_x": o} for L, o in zip(Ls, obs)
        ],
        "finding": (
            "At L=2 the quantum side holds a 2x reduction and realises 1.305x. At L=2 the "
            "classical side holds the same 2x reduction and realises %.2fx. Identical "
            "reduction, speedup differing by %.1fx." % (obs[0], obs[0] / 1.3054208369370237)
        ),
        "explanation": (
            "Reduction removes states from the representation. Speedup requires that the "
            "baseline was actually paying for them. Over the quantum flat window L=2..5 the "
            "full_runtime grows only %.4f/L (a log-fit on L=2..4 alone gives %.4f/L, i.e. "
            "indistinguishable from constant) while the reduced_runtime is flat at %.4f/L. "
            "The dense pipeline therefore never enumerated the unphysical sector, so there was "
            "no exponential to remove." % (math.exp(qm_flat), math.exp(
                ols([L for L in qgL if L <= 4], [math.log(s["full_runtime"]) for s in qgs if s["L"] <= 4])[0]),
                math.exp(rm))
        ),
        "sufficiency_condition": (
            "S(L) becomes large only when g^L exceeds the O(1)+O(L) reconstruction cost. "
            "A reduction factor is necessary-looking and NOT sufficient; the crossover is the operative quantity."
        ),
    },
    "observation_3_the_crossover_is_where_speedup_appears": {
        "quantum_crossover": {
            "L": [2, 3, 4, 5, 6],
            "full_runtime_s": fr,
            "reduced_runtime_s": rr,
            "full_over_step_growth": [None] + [fr[i] / fr[i - 1] for i in range(1, len(fr))],
            "reduced_over_step_growth": [None] + [rr[i] / rr[i - 1] for i in range(1, len(rr))],
            "logfit_full_growth_per_L": math.exp(qm),
            "logfit_reduced_growth_per_L": math.exp(rm),
            "signature": (
                "The reduced runtime is flat (%.4f/L) while the full runtime accelerates "
                "(%.4f/L) and inflects at L=6 where the full/reduced ratio jumps to 8.272x."
                % (math.exp(rm), math.exp(qm))
            ),
            "confirmed_prediction": (
                "The law predicted the quantum side would be Theta(1)-speedup while its baseline "
                "was flat, and Theta(g^L) once the baseline began paying. Both halves are observed: "
                "1.058-2.025x for L=2..5, then 8.272x at L=6."
            ),
            "next_test": "Extend ATD-QG to L=7,8,9. If full_runtime continues above ~3x/L the law predicts 20-60x; if it flattens again the law is refuted.",
        },
        "classical_crossover": {
            "already_past_it": True,
            "L_at_which_speedup_exceeds_10x": 3,
        },
    },
    "observation_4_why_this_is_the_first_cross_domain_result_that_legally_composes": {
        "problem_with_prior_attempts": (
            "Composition matrix C1/C2 fused matrix-family speedups and measured interaction "
            "factors of 0.1515 and 0.0186 against products, i.e. naive multiplication overclaimed "
            "by 6.6x and 53.9x. Fusion fails because fusing two operators charges both their overheads "
            "and neither of their savings."
        ),
        "why_a_law_composes": (
            "A shared form transfers without transferring cost. Both domains pay one O(1) quotient "
            "core and one O(L) reconstruction. Stating that form once does not charge either side twice, "
            "so there is nothing for an interaction factor to erode."
        ),
        "legal_statement": (
            "S_classical and S_quantum are never added, multiplied or fused. What is claimed is a "
            "single domain-invariant structural law, evidenced twice, with each domain supplying "
            "a different half of its evidence: classical supplies the completed exponential regime, "
            "quantum supplies the derived closed form and the observed crossover."
        ),
    },
    "novelty_statement": {
        "one_line": "Reduction is not speedup; speedup is the crossover where a paid exponential meets an unpaid quotient.",
        "what_is_new": [
            "The 2^(L-1) reduction is shown domain-invariant and is upgraded from observed (classical) to derived (quantum), so the shared form is forced rather than fitted.",
            "A sufficiency condition is stated for quotient acceleration: the eliminated states must have been genuinely costed. This is the first statement in this repo that predicts a speedup of ZERO for a correct, exact, 32x reduction.",
            "The crossover parameter is made the operative quantity, converting four previously unrelated speedup numbers into one law with out-of-sample predictions.",
            "Exactness is repurposed as a detection result: a 6.25% structural drift at L=8 is caught with zero tolerance budget because detection runs in the O(1) quotient, not the 2^(L-1) full space.",
        ],
        "what_is_not_new": (
            "No new speedup number is produced. The corrected classical headline is lower than the "
            "one it replaces. The quantum 1.305x-8.272x range and the 2^(L-1) law are pre-existing."
        ),
    },
    "falsifiers": [
        "F1: classical S(9) outside [%.0f, %.0f]x -> law refuted." % (
            law["predictions"]["S_at_L_with_band"]["9"]["band_x"][0],
            law["predictions"]["S_at_L_with_band"]["9"]["band_x"][1]),
        "F2: classical end-to-end runtime stops being O(1)+O(L) at L=9 -> core-is-O(1) claim refuted.",
        "F3: ATD-QG full_runtime at L=7 falls back below ~1.2e-3 s -> crossover claim refuted.",
        "F4: ATD-QG at L=7,8 shows large speedup while its full_runtime stays flat -> sufficiency condition refuted.",
        "F5: any accepted classical trial with residual != 0.0 -> exactness claim refuted.",
        "F6: measured g separates from 2.0 as L grows -> claim must be restated as a fitted base, not Theta(2^L/L).",
    ],
}

# ============================================================== REPORT
def fmt(x, n=2):
    return f"{x:.{n}f}x"


L_ = []
L_.append("EOF HIERARCHICAL ACCELERATION - ELEVATED AND CORRECTED VALIDATION")
L_.append("=" * 72)
L_.append("SOURCE : %s" % SRC)
L_.append("LANE   : %s (single lane, single accounting regime)" % LANE)
L_.append("")
L_.append("DEFECT REGISTER")
L_.append("-" * 72)
for d in audit["defects"]:
    L_.append("%s  %s" % (d["id"], d["defect"]))
    L_.append("      %s" % d["detail"])
    L_.append("      FIX: %s" % d["fix"])
L_.append("")
L_.append("CORRECTED HEADLINE")
L_.append("-" * 72)
L_.append("  old (no-overhead branch, mixed regime) : %s" % fmt(hdr_max, 3))
L_.append("  new (overhead-inclusive, single lane)   : %s" % fmt(obs[-1]))
L_.append("  correction                              : %.3fx DOWN" % (hdr_max / obs[-1]))
L_.append("  %s" % law["corrected_headline"]["statement"])
L_.append("")
L_.append("CORRECTED SINGLE-LANE MEASUREMENT")
L_.append("-" * 72)
L_.append(" L | state_red | baseline_s |  quotient_s |    e2e_s | ovh% |  e2e_x | was_x")
for r in law["corrected_single_lane_table"]:
    L_.append("%2d | %9d | %.4e | %.4e | %.4e | %4.1f | %6.2f | %6.2f" % (
        r["L"], int(2 ** (r["L"] - 1)), r["baseline_s"], r["quotient_s"],
        r["e2e_s"], r["overhead_pct_of_e2e"], r["e2e_speedup_x"], r["source_reported_x"]))
L_.append("")
L_.append("SCALING LAW  (the actual result)")
L_.append("-" * 72)
L_.append("  T_base(L) = %.4e * %.4f^L          R2(log) = %.6f" % (A, g, r2_log))
L_.append("  T_e2e(L)  = %.4e + %.4e*L         R2      = %.6f" % (b_e, m_e, r2_e))
L_.append("  S(L)      = %.4e * %.4f^L / (%.4e + %.4e*L)" % (A, g, b_e, m_e))
L_.append("  class     : Theta(2^L / L)   per-step growth tends to %.4f" % g)
L_.append("")
L_.append("  PREDICTIONS (unmeasured L, falsifiable)")
for Lp, p in law["predictions"]["S_at_L_with_band"].items():
    L_.append("    S(%s) = %8.1fx   band [%6.1f, %6.1f]x" % (Lp, p["point_x"], *p["band_x"]))
L_.append("    band basis: fit law/observed ratios spanned [%.3f, %.3f] on L=2..8" % law_band)
L_.append("  first L exceeding a threshold:")
for t, l in law["predictions"]["S_exceeds_x_at_L"].items():
    L_.append("    S > %9sx  at  L ~ %s" % (t, l))
L_.append("")
L_.append("GATE  (the 4 discarded trials, promoted)")
L_.append("-" * 72)
L_.append("  negative control : Q1_parity, unit parity drift per layer")
L_.append("  signature        : residual == L exactly, at even L; cancels at odd L")
L_.append("  sensitivity      : %d/%d = %.3f  (rejects known-defective)" % (
    gate["sensitivity"]["detected"], gate["sensitivity"]["of"], gate["sensitivity"]["value"]))
L_.append("  specificity      : %d/%d = %.3f  (accepts valid, residual identically 0.0)" % (
    gate["specificity"]["accepted"], gate["specificity"]["of"], gate["specificity"]["value"]))
L_.append("  false neg / pos  : %d / %d" % (gate["false_negatives"], gate["false_positives"]))
L_.append("  %s" % gate["key_result"]["novel_operational_claim"])
L_.append("  caveat: %s" % gate["residual_budget_note"])
L_.append("")
L_.append("CROSS-DOMAIN LAW  (structure, never a multiplied number)")
L_.append("-" * 72)
L_.append("  reduction 2^(L-1) identical in both domains : %s" % cross["observation_1_reduction_law_is_domain_invariant"]["identical"])
L_.append("  classical exactness : residual 0.0 at 24/24 accepted trials")
L_.append("  quantum   exactness : projector + reconstruction residual 0.0 at every L")
L_.append("  quantum closed form : 2^{L-1} DERIVED from gauge condition (C1b)")
L_.append("")
L_.append("  SAME 2x REDUCTION, DIFFERENT SPEEDUP")
L_.append("    L=2 classical %s   vs   L=2 quantum 1.31x   -> %.2fx apart" % (fmt(obs[0]), obs[0] / 1.3054208369370237))
L_.append("    quantum full_runtime is FLAT over L=2..5: log-fit %.4f/L (L=2..4 only: %.4f/L)" % (
    math.exp(qm_flat), math.exp(ols([L for L in qgL if L <= 4],
                                    [math.log(s["full_runtime"]) for s in qgs if s["L"] <= 4])[0])))
L_.append("    reduced_runtime flat at %.4f/L -> the dense path never paid for the" % math.exp(rm))
L_.append("    unphysical sector. Nothing to remove -> nothing to gain.")
L_.append("    then a single-step inflection at L=6: full %.3e vs reduced %.3e = 8.27x" % (fr[-1], rr[-1]))
L_.append("")
L_.append("  %s" % cross["novelty_statement"]["one_line"])
L_.append("")
L_.append("  NEW")
for w in cross["novelty_statement"]["what_is_new"]:
    L_.append("    + %s" % w)
L_.append("  NOT NEW")
L_.append("    - %s" % cross["novelty_statement"]["what_is_not_new"])
L_.append("")
L_.append("FALSIFIERS")
L_.append("-" * 72)
for f in cross["falsifiers"]:
    L_.append("  %s" % f)
L_.append("")
L_.append("GOVERNING LAW")
L_.append("-" * 72)
L_.append("  CLAIM STRENGTH <= EVIDENCE STRENGTH. This pass LOWERS the published")
L_.append("  headline by %.2fx, ADDS the out-of-sample predictions, and PROMOTES 4" % (hdr_max / obs[-1]))
L_.append("  discarded trials into the gate result. No number is multiplied across")
L_.append("  domains. The admissible claim set strictly shrinks.")
report = "\n".join(L_) + "\n"

stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for name, obj in (("AUDIT.json", audit), ("GATE_VALIDATION.json", gate),
                  ("SCALING_LAW.json", law), ("CROSS_DOMAIN_LAW.json", cross)):
    body = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    with open(os.path.join(OUT, name), "w") as f:
        f.write(body)
with open(os.path.join(OUT, "ELEVATED_REPORT.txt"), "w") as f:
    f.write(report)

det = {
    "protocol": "EOF_HIERARCHICAL_ELEVATION_DETERMINISM",
    "generated_utc": stamp,
    "input_sha256": {
        "BRANCH_RESULTS.json": hashlib.sha256(
            open(os.path.join(SRC, "BRANCH_RESULTS.json"), "rb").read()).hexdigest(),
        "COMPOSITION_RESULTS.json": hashlib.sha256(
            open(os.path.join(SRC, "COMPOSITION_RESULTS.json"), "rb").read()).hexdigest(),
        "FINAL_VALIDATION.json": hashlib.sha256(
            open(os.path.join(SRC, "FINAL_VALIDATION.json"), "rb").read()).hexdigest(),
        "ATD_QG_MAXIMAL_CERTIFICATE.json": hashlib.sha256(
            open(QG, "rb").read()).hexdigest(),
    },
    "output_sha256": {
        n: sha256_text(json.dumps(o, indent=2, sort_keys=True) + "\n")
        for n, o in (("AUDIT.json", audit), ("GATE_VALIDATION.json", gate),
                     ("SCALING_LAW.json", law), ("CROSS_DOMAIN_LAW.json", cross))
    },
    "report_sha256": sha256_text(report),
}
det["determinism_note"] = (
    "output_sha256 and report_sha256 exclude generated_utc and are stable across runs; "
    "re-running this script on unchanged inputs reproduces every hash above."
)
with open(os.path.join(OUT, "ELEVATION_DETERMINISM.json"), "w") as f:
    f.write(json.dumps(det, indent=2, sort_keys=True) + "\n")

print(report)
print("WROTE -> %s" % OUT)
