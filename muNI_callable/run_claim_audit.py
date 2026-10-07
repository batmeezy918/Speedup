#!/usr/bin/env python3
"""End-to-end speedup claim audit: callable receipts vs quarantine vs proofs.

Purpose
-------
Every other harness in this lane produces a speedup. None of them ask whether
the number means what a reader will assume it means. This harness does, and it
is deliberately an auditor rather than a benchmark: it re-reads existing
receipts and re-derives what each claim actually supports.

The central question it answers is ATTRIBUTION. A composite speedup factor
`S_total` can be produced by very different mechanisms:

  * a genuine reduction in executed work (the only kind that generalises),
  * a reduction in the SIZE of the state that must be computed, which is a
    memory/algorithmic win and is real but is NOT a faster kernel,
  * incidental cache or locality effects at one particular size.

Quoting `S_total` without saying which of these produced it invites the reader
to attribute the whole factor to kernel optimisation. The audit forces the split.

Governing law
-------------
`CLAIM_POLICY.md` (origin/main):

  * the evidence lattice is monotone: `CLAIM_STRENGTH <= EVIDENCE_STRENGTH`;
  * a speedup is scoped to the exact workload, environment, protocol and
    statistical treatment in its certificate;
  * **"A Lean theorem proves the proposition encoded by the theorem. It does not
    validate facts that were never encoded or supplied as assumptions."**
  * on disagreement, the strongest supported status is reduced or the artifact is
    quarantined.

Composition diagnostic
----------------------
`candidate/theorems/CT-002-Composition-Interaction-Bound.md` defines

    K12 = S12 / (S1 * S2)

and states that multiplicative composition is exact iff `K12 = 1`, while warning
that `K12` "is a descriptive statistic of the realized composition; it is not a
predictive law". This harness recomputes `K12` from the raw per-stage timings in
each receipt rather than trusting the receipt's own precomputed `K`, so a
miscomputed interaction factor is caught rather than copied.

Evidence classes
----------------
Every claim is assigned exactly one class:

  PROVEN        a machine-checked theorem establishes precisely this claim
  EMPIRICAL     directly measured on this device under a pinned protocol
  REFUTED       a machine-checked counterexample or measurement contradicts it
  UNSUPPORTED   asserted without evidence sufficient for the stated status
  ILL_SCOPED    true but narrower than the phrasing implies

No claim is upgraded. The audit can only downgrade or annotate, so it cannot
launder a weak claim into a strong one.
"""

from __future__ import annotations

import json
import hashlib
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

from muni_seeds import SEED_MANIFEST, seed_for, DEFAULT_SEED

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'receipts'
OUT.mkdir(exist_ok=True)
# Superseded runs are retained but must not be re-audited: they record the
# state of the auditor at a moment when it was still wrong (e.g. before the
# S1 basis fix, before structural receipt discovery). Auditing them again would
# reproduce the same defects under new timestamps and look like new evidence.
SUPERSEDED = OUT / '_superseded'
LIB = ROOT / 'libmuni.so'
LEAN = ROOT.parent / 'lean4'

# The highest label this audit is willing to emit for a speedup that is only
# measured. Mirrors CLAIM_POLICY.md.
MEASURED_CAP = 'EMPIRICAL'


def sha256(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load_receipts(pattern='*.json'):
    """Load receipts matching pattern from OUT only, skipping unparseable.

    Deliberately does NOT glob recursively: superseded runs live under
    receipts/_superseded/ and must be excluded from discovery.
    """
    out = []
    for p in sorted(OUT.glob(pattern)):
        try:
            out.append((p, json.loads(p.read_text())))
        except Exception as exc:  # a malformed receipt must not abort the audit
            out.append((p, {'__error__': str(exc)}))
    return out


# Timing keys that identify a receipt as carrying a composed-speedup claim.
# Detection is structural rather than by filename or schema string on purpose:
# a name-based glob silently ignores any receipt written by a differently named
# harness, which is exactly the coverage hole this audit exists to close.
COMPOSITION_TIMING_KEYS = ('full_baseline', 'quotient_baseline',
                           'quotient_neon', 'composed_e2e')

SELF_PREFIX = 'PCSS_MUNI_CLAIM_AUDIT_'


def is_composition_receipt(d):
    """True if any case carries the full composition timing set."""
    cases = d.get('cases')
    if not isinstance(cases, list):
        return False
    for c in cases:
        if not isinstance(c, dict):
            continue
        t = c.get('timing')
        if isinstance(t, dict) and all(k in t for k in COMPOSITION_TIMING_KEYS):
            return True
    return False


def has_speedup_claim(d):
    """True if the receipt asserts a numeric speedup factor above 1.

    A substring search over the serialized JSON was tried first and rejected:
    it flags receipts that merely mention the word "speedup" in prose. The
    formal-binding receipts do exactly that in their claim boundaries while
    asserting no measured factor at all, so a substring gap list was ~9 entries
    of pure noise. A coverage report that cries wolf is not a coverage report.

    Instead: walk the structure and accept only keys naming a speedup whose
    value is a number strictly greater than 1.0. A factor of exactly 1.0, a
    ratio below 1, a boolean or a string verdict do not count as a claim.
    """
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if 'speedup' in k.lower() and isinstance(v, (int, float)) \
                        and not isinstance(v, bool) and v > 1.0:
                    found.append('%s.%s=%s' % (path, k, v))
                walk(v, '%s.%s' % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, '%s[%d]' % (path, i))

    walk(d, '')
    return bool(found)


# --------------------------------------------------------------------------
# Theorem inventory: what is actually machine-checked in this checkout.
# --------------------------------------------------------------------------

def theorem_inventory():
    """Ask Lean for the axiom footprint of the theorems the speedup claims lean
    on. This is read from the build artifacts, not hardcoded, so the audit
    cannot drift from the proofs.

    A theorem that depends on `sorryAx` or a `native_decide` oracle axiom is an
    unsound oracle regardless of how it reads on paper.
    """
    probe = LEAN / '_audit_axiom_probe.lean'
    targets = [
        ('PCSSCallableBinding', 'callable_kernel_respects_blocked_sum'),
        ('PCSSCallableBinding', 'callable_microkernel_identity'),
        ('PCSSCallableBinding', 'callable_work_ratio_is_one'),
        ('PCSSCompositionCriterion', 'compositionTheoremObligation_refuted'),
        ('PCSSCompositionCriterion', 'composedGain_le_product'),
        ('PCSSCompositionCriterion', 'composedGain_lt_of_overlap'),
        ('PCSSCompositionCriterion',
         'multiplicative_composition_iff_zero_overlap'),
        ('PCSSGemmRegisterBlock', 'blockedSumObligation_holds'),
        ('PCSSGemmRegisterBlock', 'FloatModel.float_blocked_differs_from_flat'),
        ('PCSSGemmRegisterBlock', 'FloatModel.float_add_not_associative'),
    ]
    body = 'import PCSSCallableBinding\nimport PCSSCompositionCriterion\n'
    body += 'import PCSSGemmRegisterBlock\n'
    for mod, thm in targets:
        body += '#print axioms %s.%s\n' % (mod, thm)
    probe.write_text(body)

    env = dict(__import__('os').environ)
    env['PATH'] = '/root/.elan/bin' + __import__('os').pathsep + env.get('PATH', '')
    env['LEAN_PATH'] = str(LEAN / '.lake' / 'build' / 'lib' / 'lean')
    try:
        r = subprocess.run(['lean', str(probe)], cwd=LEAN, env=env,
                           capture_output=True, text=True, timeout=1800)
        found = {}
        # Lean wraps long axiom lists across lines, so match multiline.
        for m in re.finditer(
                r"'([\w.]+)' depends on axioms: \[([^\]]*)\]", r.stdout, re.S):
            found[m.group(1)] = [d.strip() for d in
                                 m.group(2).replace('\n', ' ').split(',')
                                 if d.strip()]
        for m in re.finditer(
                r"'([\w.]+)' does not depend on any axioms", r.stdout):
            found[m.group(1)] = []
        return found, r.returncode
    finally:
        if probe.exists():
            probe.unlink()


ORACLE_AXIOMS = ('sorryAx',)
ORACLE_SUBSTR = ('native_decide', 'Lean.ofReduceBool')


def classify_theorem(deps):
    """PROVEN only if machine-checked and free of unsound oracles."""
    if deps is None:
        return 'UNSUPPORTED', 'no axiom footprint recorded (proof not checked)'
    if any(d in ORACLE_AXIOMS for d in deps):
        return 'REFUTED', 'depends on %s' % ', '.join(
            d for d in deps if d in ORACLE_AXIOMS)
    if any(any(s in d for s in ORACLE_SUBSTR) for d in deps):
        return 'REFUTED', 'depends on an unsound oracle (%s)' % ', '.join(
            d for d in deps if any(s in d for s in ORACLE_SUBSTR))
    if not deps:
        return 'PROVEN', 'kernel-checked, no axioms'
    return 'PROVEN', 'kernel-checked via %s' % ', '.join(deps)


# --------------------------------------------------------------------------
# Composition attribution (CT-002).
# --------------------------------------------------------------------------

def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def recompute_composition(case):
    """Recompute S1, S2, S12 and K12 from RAW timings, not from the receipt's
    own precomputed values. Returns None when the case lacks raw timings.

    `CT-002` requires isolating the primitives against the same canonical
    baseline T0 and comparing the composed result against their product.
    """
    t = case.get('timing') or {}

    def med_of(key):
        d = t.get(key)
        if not d:
            return None
        if d.get('median_ns') is not None:
            return float(d['median_ns'])
        raw = d.get('timings_ns')
        return float(median(raw)) if raw else None

    T0 = med_of('full_baseline')
    T1 = med_of('quotient_baseline')
    T2 = med_of('quotient_neon')
    TR = med_of('reconstruction')
    T12 = med_of('composed_e2e')
    if None in (T0, T1, T2, T12) or min(T0, T1, T2, T12) <= 0:
        return None
    TR = TR or 0.0

    # Two different notions of S1, and the difference is the whole story.
    #
    # CT-002 literally defines S1 = T0/T1, i.e. the quotient compute measured
    # ALONE against the full baseline. That ignores that producing the full
    # result from the quotient result costs reconstruction, which this lane
    # actually pays.
    #
    # The end-to-end consistent figure is S1 = T0/(T1+TR): the full baseline
    # against the FULL cost of the quotient path, reconstruction included.
    #
    # Both are reported. The literal CT-002 form is retained because it is the
    # published definition; the e2e form is used for the interaction diagnostic
    # because mixing a reconstruction-free numerator with a reconstruction-bearing
    # product would make K12 meaningless.
    S1_literal = T0 / T1
    S1_e2e = T0 / (T1 + TR) if (T1 + TR) > 0 else None
    S2_raw = T1 / T2                      # kernel on quotient, raw
    S2_cond = (T1 + TR) / (T2 + TR)      # reconstruction held fixed
    S12 = T0 / T12
    product = (S1_e2e * S2_cond) if S1_e2e else None
    K = (S12 / product) if product else None
    return {
        'T0_full_baseline_ns': T0, 'T1_quotient_baseline_ns': T1,
        'T2_quotient_neon_ns': T2, 'T_reconstruction_ns': TR,
        'T12_composed_e2e_ns': T12,
        'S1_literal_CT002_T0_over_T1': S1_literal,
        'S1_e2e_T0_over_T1_plus_reconstruction': S1_e2e,
        'S2_kernel_raw': S2_raw,
        'S2_kernel_conditional_reconstruction_fixed': S2_cond,
        'S12_composed_e2e': S12,
        'product_S1_x_S2': product,
        'K12_recomputed': K,
        'K12_receipt_value': (case.get('speedups') or {}).get('composition_K'),
        'K12_basis': 'S1_e2e = T0/(T1+TR); using the reconstruction-free CT-002 '
                     'literal S1 = T0/T1 here would compare a bare quotient '
                     'against a reconstruction-bearing product and make K12 '
                     'meaningless',
        'reconstruction_overhead_fraction_of_T1': (TR / T1 if T1 else None),
        'reconstruction_dominates_quotient': (TR > T1),
    }


def audit_composition_case(case):
    """Attribute a composed speedup: how much is state reduction vs kernel."""
    rec = recompute_composition(case)
    if rec is None:
        return {'verdict': 'UNSUPPORTED',
                'reason': 'no raw per-stage timings to recompute from'}
    findings, labels = [], []

    K = rec['K12_recomputed']
    if K is not None:
        # CT-002: exact multiplication iff K == 1.
        dev = abs(K - 1.0)
        rec['K12_abs_deviation_from_one'] = dev
        if dev < 0.02:
            labels.append('K12_NEAR_ONE')
        else:
            labels.append('K12_DEVIATES_FROM_ONE')
            findings.append(
                'K12 = %.4f, so the composed factor is NOT the product of the '
                'isolated factors (CT-002 exactness requires K12 = 1). '
                'CT-002 also states K12 is descriptive, not predictive, so this '
                'is not by itself a defect; it does mean the product must not be '
                'quoted as the achieved speedup.' % K)
        rk = rec['K12_receipt_value']
        if rk is not None and abs(rk - K) > 1e-9:
            findings.append(
                'receipt K (%.12g) disagrees with recomputed K (%.12g); the '
                'receipt value is not reproduced from its own raw timings'
                % (rk, K))
            labels.append('RECEIPT_K_NOT_REPRODUCED')

    # The decisive attribution question.
    s2 = rec['S2_kernel_conditional_reconstruction_fixed']
    s2_raw = rec['S2_kernel_raw']
    s1 = rec['S1_e2e_T0_over_T1_plus_reconstruction']
    s1_literal = rec['S1_literal_CT002_T0_over_T1']
    total = rec['S12_composed_e2e']

    if rec['reconstruction_dominates_quotient']:
        ratio = rec['reconstruction_overhead_fraction_of_T1']
        labels.append('RECONSTRUCTION_DOMINATES')
        findings.append(
            'reconstruction costs %.2fx the quotient compute it expands '
            '(TR/T1 = %.1f). The state-reduction win is therefore largely '
            'consumed paying for the expansion back to full size, which is why '
            'S1_e2e = %.2f while the reconstruction-free CT-002 literal '
            'S1 = T0/T1 = %.2f overstates it by %.1fx.' %
            (ratio, ratio, s1, s1_literal,
             (s1_literal / s1) if s1 else float('nan')))

    if s2 < 1.0:
        labels.append('KERNEL_SLOWER_THAN_BASELINE')
        findings.append(
            'the NEON kernel is SLOWER than the scalar baseline it replaces: '
            'S2_raw = %.4f (raw), S2_conditional = %.4f. The composed speedup of '
            '%.2fx therefore does NOT come from faster arithmetic; it comes from '
            'computing a %.0fx smaller state (S1_e2e = %.2f).' %
            (s2_raw, s2, total, s1, s1))
    elif s2 < 1.05:
        labels.append('KERNEL_SPEEDUP_NEGLIGIBLE')
        findings.append(
            'S2_conditional = %.4f: with reconstruction held fixed the kernel is '
            'within 5%% of the baseline, i.e. no measurable kernel speedup.' % s2)
    else:
        labels.append('KERNEL_SPEEDUP_MATERIAL')

    rec['verdict'] = 'EMPIRICAL'
    rec['evidence_class'] = MEASURED_CAP
    rec['attribution'] = {
        'total_composed_e2e': total,
        'state_reduction_S1_e2e_incl_reconstruction': s1,
        'state_reduction_S1_literal_excl_reconstruction': s1_literal,
        'kernel_factor_conditional_S2': s2,
        'kernel_factor_raw_S2': s2_raw,
        'dominant_contribution': (
            'state/memory-traffic reduction' if s2 < 1.05 else 'kernel arithmetic'),
        'bottleneck': ('reconstruction (TR), not the quotient kernel'
                       if rec['reconstruction_dominates_quotient']
                       else 'quotient kernel'),
    }
    rec['findings'] = findings
    rec['labels'] = labels
    return rec


# --------------------------------------------------------------------------
# Remote / formal cross-check: can any theorem license these speedups?
# --------------------------------------------------------------------------

def remote_claim_check():
    """Inspect origin/main for theorem documents and their declared status.

    Run offline-safe: if git or the remote is unavailable, report that the check
    did not run rather than silently treating it as a pass.
    """
    out = {'remote': 'https://github.com/batmeezy918/Speedup.git', 'available': False}
    try:
        r = subprocess.run(['git', '-C', str(ROOT.parent), 'remote', '-v'],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            out['error'] = 'git remote unavailable'
            return out
        out['available'] = True
    except Exception as exc:
        out['error'] = str(exc)
        return out

    theorems = []
    try:
        ls = subprocess.run(
            ['git', '-C', str(ROOT.parent), 'ls-tree', '-r', '--name-only',
             'origin/main'], capture_output=True, text=True, timeout=120)
        paths = [p for p in ls.stdout.splitlines()
                 if p.startswith('candidate/theorems/') and p.endswith('.md')]
        for p in paths:
            show = subprocess.run(
                ['git', '-C', str(ROOT.parent), 'show', 'origin/main:' + p],
                capture_output=True, text=True, timeout=120)
            head = show.stdout[:1200]
            m = re.search(r'\*\*Status:\*\*\s*(.+)', head)
            theorems.append({
                'path': p,
                'declared_status': (m.group(1).strip() if m else 'UNDECLARED'),
                'proves_a_wall_clock_speedup': False,
            })
    except Exception as exc:
        out['error'] = str(exc)
        return out

    non_verified = [t for t in theorems
                    if 'VERIFIED' not in t['declared_status'].upper()
                    or 'NOT' in t['declared_status'].upper()]
    out['candidate_theorems'] = theorems
    out['all_candidate_not_verified'] = len(non_verified) == len(theorems)
    out['conclusion'] = (
        'No theorem on origin/main proves a wall-clock speedup. CLAIM_POLICY.md: '
        '"A Lean theorem proves the proposition encoded by the theorem. It does '
        'not validate facts that were never encoded or supplied as '
        'assumptions." Therefore no measured speedup in this lane may be '
        'described as proven.')
    return out


# --------------------------------------------------------------------------
# Main audit.
# --------------------------------------------------------------------------

def audit_legacy_callable(d):
    """Audit MUNI-CALLABLE-RUNTIME-0.1 receipts.

    These predate the current harnesses and are easy to overlook because their
    filename does not match any PCSS_* pattern. They are recomputed from raw
    per-repetition timings rather than trusting the declared speedup, and the
    FLOP-reduction claim is checked against work_ratio.
    """
    findings = []
    rows = []
    for r in d.get('results', []):
        b, c = r.get('baseline') or {}, r.get('candidate') or {}
        bt, ct = b.get('timings_ns'), c.get('timings_ns')
        if not (bt and ct):
            continue
        # Recompute the median from the raw samples, not from the stored
        # median, so a mis-stored median cannot pass unnoticed.
        mb = float(median(bt))
        mc = float(median(ct))
        recomputed = mb / mc if mc else None
        declared = r.get('speedup')
        agree = (recomputed is not None and declared is not None
                 and abs(recomputed - declared) <= 1e-6 * max(abs(declared), 1.0))
        wr = r.get('work_ratio')
        bitwise = (r.get('max_abs_diff') == 0.0)
        rows.append({
            'n': r.get('n'), 'declared_speedup': declared,
            'recomputed_speedup_from_raw_timings': recomputed,
            'agrees_within_1e-6_relative': agree,
            'work_ratio': wr,
            'flop_reduction_claimed': bool(
                wr is not None and abs(wr - 1.0) > 1e-12),
            'max_abs_diff': r.get('max_abs_diff'),
            'bitwise_equal': bitwise,
            'checksums_agree': (r.get('checksum_baseline')
                                == r.get('checksum_candidate')),
        })
        if not agree:
            findings.append(
                'n=%s declared speedup %s disagrees with %s recomputed from raw '
                'timings' % (r.get('n'), declared, recomputed))
        if r.get('max_abs_diff') == 0.0:
            findings.append('n=%s: bitwise identical (max_abs_diff = 0)' % r.get('n'))

    labels = set()
    if any(not x['agrees_within_1e-6_relative'] for x in rows):
        labels.add('DECLARED_SPEEDUP_UNREPRODUCIBLE')
    if any(x['flop_reduction_claimed'] for x in rows):
        labels.add('FLOP_REDUCTION_CLAIMED')
    if rows and all(x['bitwise_equal'] for x in rows):
        labels.add('BITWISE_EQUAL_ALL_SIZES')

    if 'DECLARED_SPEEDUP_UNREPRODUCIBLE' in labels:
        verdict = 'REFUTED'
    elif 'FLOP_REDUCTION_CLAIMED' in labels:
        verdict = 'ILL_SCOPED'
    else:
        verdict = 'EMPIRICAL'
    return {
        'schema': d.get('schema'), 'verdict': verdict, 'rows': rows,
        'labels': sorted(labels), 'findings': findings,
        'has_claim_boundary': bool(d.get('claim_boundary')),
        'seed_status_present': 'seed_status' in d,
    }


def audit_qg_callable(d):
    """Audit the ad-hoc QG callable receipt.

    Flagged here because it asserts a large speedup while failing several
    policy checks. Each finding is a specific, checkable defect rather than a
    general suspicion.
    """
    findings = []
    labels = []
    speedup = d.get('e2e_speedup')
    status = d.get('status')
    bitwise = d.get('bitwise_equal')

    if status == 'PASS' and bitwise is False:
        labels.append('PASS_WITHOUT_BITWISE_EQUALITY')
        findings.append(
            'status is PASS but bitwise_equal is False; "PASS" must be defined '
            'against an explicit tolerance (exact_error=%r), otherwise it reads '
            'as an unqualified correctness claim' % d.get('exact_error'))
    if not d.get('claim_boundary'):
        labels.append('NO_CLAIM_BOUNDARY')
        findings.append(
            'no claim_boundary: scope, correctness basis and FLOP work ratio are '
            'unstated, so the %r speedup is ungoverned by CLAIM_POLICY' % speedup)
    if not d.get('claim_strength'):
        labels.append('NO_CLAIM_STRENGTH')
        findings.append('no claim_strength field; status cannot be placed on the '
                        'evidence lattice')
    seed = d.get('seed')
    allowed = set(SEED_MANIFEST.get('seeds', {}).values()) | {DEFAULT_SEED}
    if seed is not None and seed not in allowed:
        labels.append('SEED_OUTSIDE_POLICY')
        findings.append(
            'seed %r is not produced by muni_seeds (default %r), so this run is '
            'not reproducible under the pinned-seed policy'
            % (seed, DEFAULT_SEED))
    if not isinstance(d.get('schema'), str):
        labels.append('UNDECLARED_SCHEMA')
        findings.append('no schema field; the receipt cannot be routed by type')

    verdict = 'UNSUPPORTED'
    return {
        'schema': d.get('schema'), 'verdict': verdict,
        'e2e_speedup': speedup, 'declared_status': status,
        'labels': labels, 'findings': findings,
        'recommendation': (
            'either regenerate under a current PCSS harness with an explicit '
            'claim_boundary and a muni_seeds seed, or move to quarantine; do not '
            'cite the %r speedup meanwhile' % speedup),
    }


def main():
    t0 = time.time()
    thm, ax_exit = theorem_inventory()
    theorems = {}
    for key, deps in sorted(thm.items()):
        cls, why = classify_theorem(deps)
        theorems[key] = {'axioms': deps, 'class': cls, 'basis': why}

    tracked = ['PCSSCallableBinding.callable_kernel_respects_blocked_sum',
               'PCSSCallableBinding.callable_microkernel_identity',
               'PCSSCallableBinding.callable_work_ratio_is_one',
               'PCSSCompositionCriterion.compositionTheoremObligation_refuted',
               'PCSSCompositionCriterion.composedGain_le_product',
               'PCSSCompositionCriterion.composedGain_lt_of_overlap',
               'PCSSCompositionCriterion.multiplicative_composition_iff_zero_overlap',
               'PCSSGemmRegisterBlock.blockedSumObligation_holds',
               'PCSSGemmRegisterBlock.FloatModel.float_blocked_differs_from_flat',
               'PCSSGemmRegisterBlock.FloatModel.float_add_not_associative']
    unverified = [t for t in tracked if t not in thm]

    # --- audit the composed-speedup receipts ---
    # Routed structurally, not by glob, so no composition receipt escapes.
    comp_audits = []
    for p, d in load_receipts('*.json'):
        if p.name.startswith(SELF_PREFIX):
            continue
        if not is_composition_receipt(d):
            continue
        if '__error__' in d:
            comp_audits.append({'receipt': p.name, 'verdict': 'UNSUPPORTED',
                                'reason': 'unparseable receipt'})
            continue
        entry = {'receipt': p.name,
                 'schema': d.get('schema'),
                 'claimed_strength': d.get('claim_strength'),
                 'library_sha256': d.get('library_sha256'),
                 'seed_status': d.get('seed_status'),
                 'cases': []}
        excluded = []
        for case in d.get('cases', []):
            # A harness may mark a case inadmissible (e.g. the reference
            # overflowed). Such a case must not contribute to a verdict.
            if case.get('speedup_admissible') is False:
                excluded.append({'case': case.get('case'),
                                 'correctness': case.get('correctness')})
                continue
            entry['cases'].append(audit_composition_case(case))
        entry['cases_excluded_inadmissible'] = excluded
        # A claim is only as strong as its weakest case.
        labels = set()
        for c in entry['cases']:
            labels.update(c.get('labels', []))
        entry['aggregated_labels'] = sorted(labels)
        if 'KERNEL_SLOWER_THAN_BASELINE' in labels:
            entry['verdict'] = 'ILL_SCOPED'
            entry['verdict_reason'] = (
                'claimed composed speedup is attributable to state reduction, '
                'not to a faster kernel; phrasing it as a kernel speedup would '
                'exceed the evidence (CLAIM_POLICY conflict rule)')
        elif not entry['cases']:
            entry['verdict'] = 'UNSUPPORTED'
            entry['verdict_reason'] = (
                'no admissible case: every case was excluded by the producing '
                'harness, so no speedup claim in this receipt is supported')
        elif 'K12_DEVIATES_FROM_ONE' in labels:
            entry['verdict'] = 'ILL_SCOPED'
            entry['verdict_reason'] = (
                'composed factor is not the product of isolated factors (K12 != 1)')
        else:
            entry['verdict'] = MEASURED_CAP
            entry['verdict_reason'] = 'directly measured, scope as declared'
        comp_audits.append(entry)

    # --- audit the callable receipts ---
    callable_audits = []
    for p, d in load_receipts('PCSS_MUNI_CALLABLE_*.json'):
        if '__error__' in d:
            callable_audits.append({'receipt': p.name, 'verdict': 'UNSUPPORTED',
                                    'reason': 'unparseable receipt'})
            continue
        gates = d.get('gates') or {}
        rep = d.get('semantic_reproducibility') or {}
        entry = {
            'receipt': p.name, 'schema': d.get('schema'),
            'claimed_strength': d.get('claim_strength'),
            'all_gates_pass': all(gates.values()) if gates else None,
            'failed_gates': [k for k, v in gates.items() if not v],
            'speedup_min': rep.get('speedup_min'),
            'speedup_median': rep.get('speedup_median'),
            'speedup_max': rep.get('speedup_max'),
            'has_seed_record': ('seed' in d) or ('seed_status' in d),
        }
        # Historical receipts with failing gates must never be presented as
        # passing evidence; flag them so a reader cannot pick them up by mistake.
        if entry['failed_gates']:
            entry['verdict'] = 'REFUTED'
            entry['verdict_reason'] = 'own gates failed: %s' % ', '.join(
                entry['failed_gates'])
        else:
            entry['verdict'] = MEASURED_CAP
            entry['verdict_reason'] = (
                'directly measured at one size on one device; speedup is '
                'work_ratio == 1 plus memory-traffic reduction, not fewer FLOPs')
        if not entry['has_seed_record']:
            entry['advisory'] = (
                'no seed recorded (pre-dates seed pinning); inputs were '
                'deterministic constants, so this is a provenance gap rather '
                'than a reproducibility defect')
        callable_audits.append(entry)

    # --- audit legacy/unrouted receipts that still assert speedups ---
    # Discovered by scanning for an asserted speedup and then routed by shape,
    # so a receipt from an old harness cannot quietly escape review.
    legacy_audits = []
    for p, d in load_receipts('*.json'):
        if p.name.startswith(SELF_PREFIX) or '__error__' in d:
            continue
        if not has_speedup_claim(d):
            continue
        if is_composition_receipt(d):
            continue
        # Already covered by the dedicated callable auditor. Without this
        # exclusion the fallback below double-captures them and mislabels nine
        # properly-audited receipts UNSUPPORTED, which would be a false alarm
        # against the strongest evidence in the set.
        if p.name.startswith('PCSS_MUNI_CALLABLE_'):
            continue
        if (d.get('schema') == 'MUNI-CALLABLE-RUNTIME-0.1'
                or (isinstance(d.get('results'), list) and d.get('results'))):
            legacy_audits.append(dict(audit_legacy_callable(d),
                                      receipt=p.name))
        elif 'e2e_speedup' in d:
            legacy_audits.append(dict(audit_qg_callable(d), receipt=p.name))
        else:
            legacy_audits.append({
                'receipt': p.name, 'schema': d.get('schema'),
                'verdict': 'UNSUPPORTED',
                'reason': 'asserts a speedup but matches no known auditor shape',
            })

    # --- coverage: which receipts carry a speedup claim, and were they audited? ---
    # Computed AFTER every audit loop so all routed receipts are accounted for.
    # Anything asserted but not routed is reported as a gap: an unaudited claim
    # must be visible, never quietly absent.
    audited_names = ({e['receipt'] for e in comp_audits} |
                     {e['receipt'] for e in callable_audits} |
                     {e['receipt'] for e in legacy_audits})
    coverage = []
    for p, d in load_receipts('*.json'):
        if p.name.startswith(SELF_PREFIX):
            continue
        if '__error__' in d:
            coverage.append({'receipt': p.name, 'schema': None,
                             'parsed': False, 'audited': False,
                             'note': 'unparseable; cannot confirm claim content'})
            continue
        coverage.append({
            'receipt': p.name, 'schema': d.get('schema'),
            'parsed': True,
            'claims_speedup': has_speedup_claim(d),
            'is_composition': is_composition_receipt(d),
            'audited': p.name in audited_names,
            'claim_strength': d.get('claim_strength'),
            'seed_status_present': 'seed_status' in d,
        })
    gaps = [{'receipt': g['receipt'], 'schema': g['schema'],
             'claim_strength': g['claim_strength']}
            for g in coverage
            if g.get('claims_speedup') and not g.get('audited')]

    remote = remote_claim_check()

    quarantine = {
        'path': 'evidence/quarantine/',
        'role': 'retained candidates excluded from claims per CLAIM_POLICY.md '
                '(status QUARANTINED)',
        'speedup_claims_admitted': 0,
        'rationale': 'quarantined material is excluded from claims by definition; '
                     'it cannot raise any measured or formal status',
    }

    verdicts = {}
    for e in comp_audits + callable_audits + legacy_audits:
        verdicts[e['verdict']] = verdicts.get(e['verdict'], 0) + 1

    receipt = {
        'schema': 'PCSS-MUNI-CLAIM-AUDIT-1.0',
        'run_id': time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()),
        'seed': seed_for('claim_audit'),
        'seed_policy': SEED_MANIFEST,
        'purpose': 're-read every speedup receipt and re-derive what each claim '
                   'supports, attributing composite factors to their true source '
                   'and downgrading any claim that exceeds its evidence',
        'auditor_capability': 'can only downgrade or annotate; never upgrades a '
                              'claim, so it cannot launder weak evidence',
        'device': {'arch': platform.machine(), 'kernel': platform.release()},
        'library_sha256': sha256(LIB),
        'governing_law': {
            'claim_policy': 'CLAIM_POLICY.md (origin/main)',
            'monotonicity': 'CLAIM_STRENGTH <= EVIDENCE_STRENGTH',
            'theorem_scope': 'a Lean theorem validates only what it encodes',
            'conflict_rule': 'disagreement reduces the strongest supported '
                             'status, or quarantines the artifact',
            'composition_diagnostic': 'CT-002: K12 = S12/(S1*S2); exact '
                                      'multiplication iff K12 = 1; K12 is '
                                      'descriptive, not predictive',
        },
        'theorem_inventory': {
            'lean_probe_exit_code': ax_exit,
            'theorems': theorems,
            'tracked_but_not_found': unverified,
            'oracle_free': all(t['class'] == 'PROVEN' for t in theorems.values()),
        },
        'formal_to_speedup_mapping': [
            {'speedup_claim': 'the two kernels compute the same result',
             'theorem': 'PCSSCallableBinding.callable_kernel_respects_blocked_sum',
             'class': theorems.get(
                 'PCSSCallableBinding.callable_kernel_respects_blocked_sum',
                 {}).get('class'),
             'verdict': 'ILL_SCOPED',
             'why': 'proved over Int; the shipped kernels accumulate in binary32, '
                    'which is not associative (machine-checked). Bitwise equality '
                    'is therefore empirical, not proven, and fails at ragged '
                    'sizes by ~1 ULP.'},
            {'speedup_claim': 'the microkernel evaluates the block identity',
             'theorem': 'PCSSCallableBinding.callable_microkernel_identity',
             'class': theorems.get(
                 'PCSSCallableBinding.callable_microkernel_identity',
                 {}).get('class'),
             'verdict': 'PROVEN',
             'scope': 'the algebraic 2x2 regrouping only; says nothing about time'},
            {'speedup_claim': 'fewer FLOPs are performed',
             'theorem': 'PCSSCallableBinding.callable_work_ratio_is_one',
             'class': theorems.get(
                 'PCSSCallableBinding.callable_work_ratio_is_one',
                 {}).get('class'),
             'verdict': 'REFUTED',
             'why': 'work_ratio = 1 exactly. NO flop reduction is available; any '
                    'speedup is memory/state traffic, not arithmetic.'},
            {'speedup_claim': 'composed speedups multiply',
             'theorem': 'PCSSCompositionCriterion.'
                        'multiplicative_composition_iff_zero_overlap',
             'class': theorems.get(
                 'PCSSCompositionCriterion.'
                 'multiplicative_composition_iff_zero_overlap',
                 {}).get('class'),
             'verdict': 'REFUTED',
             'why': 'machine-checked that the original composition obligation was '
                    'FALSE, and proved that multiplicative composition holds iff '
                    'subspace overlap is zero. CT-002 is CANDIDATE, not VERIFIED. '
                    'No corpus artifact records a work_ratio, so no measured '
                    'factor is licensed to compose multiplicatively.'},
            {'speedup_claim': 'reassociation preserves the value',
             'theorem': 'PCSSGemmRegisterBlock.'
                        'FloatModel.float_blocked_differs_from_flat',
             'class': theorems.get(
                 'PCSSGemmRegisterBlock.FloatModel.float_blocked_differs_from_flat',
                 {}).get('class'),
             'verdict': 'REFUTED',
             'why': 'machine-checked counterexample; this is a formal refutation '
                    'of value-preserving reassociation in floating point'},
        ],
        'composed_speedup_audit': comp_audits,
        'legacy_routed_audit': legacy_audits,
        'coverage': {
            'receipts_seen': len(coverage),
            'receipts_audited': len(audited_names),
            'speedup_claims_not_audited': gaps,
            'detection': 'structural (timing keys present), not glob-based, so '
                         'a receipt from a newly named harness is still audited',
            'note': 'a gap listed here means the receipt asserts a speedup but '
                    'no auditor in this file routed it; it is reported rather '
                    'than ignored',
            'per_receipt': coverage,
        },
        'callable_speedup_audit': callable_audits,
        'remote_cross_check': remote,
        'quarantine': quarantine,
        'verdict_counts': verdicts,
        'findings': sorted({
            f for e in comp_audits for c in e.get('cases', [])
            for f in c.get('findings', [])
        }),
        'elapsed_seconds': round(time.time() - t0, 3),
        'claim_boundary': [
            'This audit performs NO timing of its own; it re-derives conclusions '
            'from receipts already on disk plus a live Lean axiom probe.',
            'It cannot upgrade any claim. Its only power is to downgrade.',
            'A speedup quoted from this lane must state whether it is a '
            'state/memory-traffic reduction or a kernel arithmetic speedup. '
            'work_ratio = 1, so no arithmetic reduction exists.',
            'All measured factors remain scoped to this device, binary, '
            'compiler, thread count and input distribution.',
            'No claim here is VERIFIED. Formal status remains FORMAL_PARTIAL and '
            'measured status is capped at EMPIRICAL.',
        ],
    }

    p = OUT / ('PCSS_MUNI_CLAIM_AUDIT_%s.json' % receipt['run_id'])
    p.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    print('RECEIPT=' + str(p))


if __name__ == '__main__':
    main()