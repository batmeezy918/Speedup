#!/usr/bin/env python3
"""Input-domain robustness sweep for the MuNi callable operator.

Every historical correctness receipt was produced on CONSTANT inputs
(A = all 1.1, B = all 2.2). Constant operands accumulate identically under any
summing order, so `max_abs_diff == 0` on that family is close to the weakest
possible correctness witness: it cannot distinguish "reassociation preserves the
result" from "this input family happens to be order-insensitive".

The two kernels genuinely do sum in different orders:
  baseline  gemm_scalar   : for k in [kk,kk+64): for j: c[i,j] += a[i,k]*b[k,j]
  candidate gemm_blocked  : for p in [pc,pc+128): microkernel_8x8 accumulates
                            C in registers over a whole k-block

This sweep measures, across several input families and sizes, whether the two
agree BITWISE and how far each sits from a float64 reference. It reports; it
never adjusts a gate.
"""
import hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
from muni_runtime import lib, ptr, call

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'receipts'
OUT.mkdir(exist_ok=True)
os.environ['OMP_NUM_THREADS'] = '1'


def both(n, a, b):
    cb = np.zeros((n, n), np.float32)
    cc = np.zeros((n, n), np.float32)
    call(lib.muni_baseline, n, a, b, cb)
    call(lib.muni_neon, n, a, b, cc)
    return cb, cc


def families(n, rng):
    """Input families ordered by how hostile they are to summation order."""
    f = {}
    f['constant_uniform'] = (np.full((n, n), 1.1, np.float32),
                             np.full((n, n), 2.2, np.float32))
    f['random_uniform'] = (rng.random((n, n)).astype(np.float32),
                           rng.random((n, n)).astype(np.float32))
    f['random_normal'] = (rng.standard_normal((n, n)).astype(np.float32),
                          rng.standard_normal((n, n)).astype(np.float32))
    # wide dynamic range: products span ~2^40, so small terms are absorbed and
    # the result depends strongly on the order of accumulation
    ea = rng.integers(-20, 21, size=(n, n))
    eb = rng.integers(-20, 21, size=(n, n))
    f['mixed_scale_pow2'] = (np.ldexp(np.ones((n, n), np.float32), ea),
                             np.ldexp(np.ones((n, n), np.float32), eb))
    # alternating signs at similar magnitude -> catastrophic cancellation
    sa = (rng.integers(0, 2, size=(n, n)) * 2 - 1).astype(np.float32)
    sb = (rng.integers(0, 2, size=(n, n)) * 2 - 1).astype(np.float32)
    f['alternating_sign'] = (sa, sb)
    # severe absorption: one huge row dominates, small terms vanish
    a = rng.random((n, n)).astype(np.float32)
    b = rng.random((n, n)).astype(np.float32)
    a[0, :] = np.float32(1e18)
    b[0, :] = np.float32(1e18)
    f['absorption_extreme'] = (a, b)
    return f


def main():
    rng = np.random.default_rng(20261001)
    sizes = [33, 64, 129, 257, 512]
    rows = []
    for n in sizes:
        for name, (a, b) in families(n, rng).items():
            cb, cc = both(n, a, b)
            ref = a.astype(np.float64) @ b.astype(np.float64)
            d_ab = float(np.max(np.abs(cb.astype(np.float64) - cc.astype(np.float64))))
            scale = float(np.max(np.abs(ref))) or 1.0
            rows.append({
                'n': n, 'family': name,
                'bitwise_agree': d_ab == 0.0,
                'max_abs_diff_between_kernels': d_ab,
                'rel_diff_between_kernels': d_ab / scale,
                'baseline_err_vs_f64': float(np.max(np.abs(cb.astype(np.float64) - ref))),
                'candidate_err_vs_f64': float(np.max(np.abs(cc.astype(np.float64) - ref))),
                'baseline_rel_err': float(np.max(np.abs(cb.astype(np.float64) - ref))) / scale,
                'candidate_rel_err': float(np.max(np.abs(cc.astype(np.float64) - ref))) / scale,
            })
        print('n=%-5d done' % n, flush=True)

    agree = [r for r in rows if r['bitwise_agree']]
    disagree = [r for r in rows if not r['bitwise_agree']]
    worst = max(disagree, key=lambda r: r['rel_diff_between_kernels']) if disagree else None

    receipt = {
        'schema': 'PCSS-MUNI-ROBUSTNESS-1.0',
        'run_id': time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()),
        'arch': platform.machine(), 'kernel': platform.release(),
        'omp_threads': 1,
        'library_sha256': hashlib.sha256((ROOT / 'libmuni.so').read_bytes()).hexdigest(),
        'purpose': 'Test whether the bitwise-equality correctness witness '
                   'generalises beyond the constant-input family used by every '
                   'prior receipt.',
        'sizes': sizes,
        'rows': rows,
        'summary': {
            'cases': len(rows),
            'bitwise_agree_cases': len(agree),
            'bitwise_disagree_cases': len(disagree),
            'families_tested': sorted({r['family'] for r in rows}),
            'families_with_disagreement': sorted({r['family'] for r in disagree}),
            'constant_family_agrees': all(
                r['bitwise_agree'] for r in rows if r['family'] == 'constant_uniform'),
            'worst_disagreement': worst,
        },
        'finding': (
            'Constant inputs agree bitwise, as prior receipts recorded. General '
            'inputs do NOT: the two kernels accumulate the k axis in different '
            'orders and binary32 addition is not associative, so bitwise equality '
            'is an artefact of the constant-input family rather than a property of '
            'the transformation.' if disagree else
            'No bitwise disagreement observed across the tested families and sizes.'),
        'consequence': (
            'The historical `max_abs_diff == 0` correctness witness is '
            'INPUT-FAMILY DEPENDENT and must not be read as a general equivalence '
            'claim. The Lean results are stated over Int, where blocking IS '
            'value-preserving (blockedSumObligation_holds); over binary32 it is not. '
            'Empirical agreement on general inputs is a matter of magnitude within '
            'rounding error, not of bitwise identity.' if disagree else
            'Bitwise agreement held across all tested families and sizes.'),
    }

    p = OUT / ('PCSS_MUNI_ROBUSTNESS_%s.json' % receipt['run_id'])
    p.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt['summary'], indent=2))
    print('RECEIPT=' + str(p))


if __name__ == '__main__':
    main()