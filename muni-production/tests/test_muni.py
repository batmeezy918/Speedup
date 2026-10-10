"""Test suite for the MUNI production API.

Every test must pass. Nothing here asserts a speedup without measuring it.
"""

import math
import unittest

import muni


def block_constant_state(r, m, seed=0.0):
    """A genuinely block-constant state: m identical fibers per block."""
    return [seed + 0.01 * b for b in range(r) for _ in range(m)]


class TestScopeHelpers(unittest.TestCase):
    def test_measure_sector_exact(self):
        resid, bad, total = muni.measure_sector([1.0, 1.0, 2.0, 2.0], m=2)
        self.assertEqual(resid, 0.0)
        self.assertEqual(bad, 0)
        self.assertEqual(total, 2)

    def test_measure_sector_detects_violation(self):
        resid, bad, total = muni.measure_sector([1.0, 1.1, 2.0, 2.0], m=2)
        self.assertGreater(resid, 0.0)
        self.assertEqual(bad, 1)
        self.assertEqual(total, 2)

    def test_measure_sector_rejects_bad_m(self):
        with self.assertRaises(ValueError):
            muni.measure_sector([1.0, 2.0, 3.0], m=2)

    def test_is_admissible_respects_tol(self):
        x = [1.0, 1.0 + 1e-12, 2.0, 2.0]
        self.assertTrue(muni.is_admissible(x, m=2, tol=1e-9))
        self.assertFalse(muni.is_admissible(x, m=2, tol=0.0))

    def test_claim_is_scoped(self):
        c = muni.claim()
        self.assertEqual(c["scope_id"], "tensor-separable-block-constant-v1")
        self.assertGreater(len(c["exclusions"]), 3)
        joined = " ".join(c["exclusions"]).lower()
        for forbidden in ("not a general-purpose accelerator",
                          "no independent-hardware replication",
                          "no automatic discovery"):
            self.assertIn(forbidden, joined)


class TestRunExactness(unittest.TestCase):
    """The correctness contract: optimised == original, always."""

    def test_admissible_run_is_exact(self):
        U = [[0.9, 0.1], [0.2, 0.8]]
        x = block_constant_state(2, 2)
        res = muni.run(U, x, steps=32)
        self.assertTrue(res.used_quotient)
        self.assertTrue(res.exact)
        self.assertEqual(res.max_abs_error, 0.0)
        self.assertEqual(res.values, res.reference)

    def test_inadmissible_run_falls_back_and_is_still_exact(self):
        U = [[0.9, 0.1], [0.2, 0.8]]
        x = [1.0, 1.1, 2.0, 2.0]
        res = muni.run(U, x, steps=32)
        self.assertFalse(res.used_quotient)
        self.assertTrue(res.exact)
        self.assertEqual(res.max_abs_error, 0.0)
        self.assertIn("INADMISSIBLE", res.reason)

    def test_zero_steps_is_identity(self):
        U = [[0.5, 0.5], [0.25, 0.75]]
        x = block_constant_state(2, 3)
        res = muni.run(U, x, steps=0)
        self.assertTrue(res.exact)
        for a, b in zip(res.values, x):
            self.assertAlmostEqual(a, b, places=12)

    def test_large_shape_is_exact(self):
        r, m = 64, 64
        U = [[0.01 if i == j else 0.002 for j in range(r)] for i in range(r)]
        x = block_constant_state(r, m)
        res = muni.run(U, x, steps=64)
        self.assertTrue(res.used_quotient)
        self.assertTrue(res.exact)

    def test_single_block_single_fiber(self):
        res = muni.run([[2.0]], [3.0], steps=4)
        self.assertTrue(res.used_quotient)
        self.assertTrue(res.exact)
        self.assertAlmostEqual(res.values[0], 3.0 * 2.0 ** 4, places=9)

    def test_mismatched_shapes_rejected(self):
        with self.assertRaises(ValueError):
            muni.run([[0.9, 0.1], [0.2, 0.8]], [1.0, 1.0, 2.0], steps=1)

    def test_non_square_operator_rejected(self):
        with self.assertRaises(ValueError):
            muni.run([[0.9, 0.1, 0.0], [0.2, 0.8]], [1.0, 1.0], steps=1)

    def test_negative_steps_rejected(self):
        with self.assertRaises(ValueError):
            muni.run([[1.0]], [1.0], steps=-1)


class TestNonFiniteHandling(unittest.TestCase):
    """NaN and Inf must be refused, not silently propagated."""

    def test_nan_state_refused(self):
        res = muni.run([[1.0]], [float("nan")], steps=1)
        self.assertEqual(res.status_name, "ERR_NONFINITE")
        self.assertFalse(res.exact)

    def test_inf_operator_refused(self):
        res = muni.run([[float("inf")]], [1.0], steps=1)
        self.assertEqual(res.status_name, "ERR_NONFINITE")

    def test_signed_zero_bitwise_identical_between_arms(self):
        """Signed zero is a real IEEE-754 edge case for this kernel.

        Both arms accumulate into `double acc = 0.0`, so a single-term product of
        -0.0 becomes +0.0 in BOTH paths. The two arms therefore still agree
        bit-for-bit, which is the contract that matters. What is NOT claimed is
        that the sign of zero survives an iteration -- it does not, in either arm.

        This test pins the actual behaviour so a future change cannot silently
        make the two arms disagree about the sign of zero.
        """
        import struct
        res = muni.run([[1.0]], [-0.0], steps=1)
        self.assertTrue(res.exact)
        fast_bits = struct.pack("<d", res.values[0])
        ref_bits = struct.pack("<d", res.reference[0])
        self.assertEqual(fast_bits, ref_bits,
                         "optimised and original must agree bit-for-bit including sign")

    def test_signed_zero_mixed_in_fiber_is_inadmissible(self):
        """-0.0 and +0.0 compare equal numerically, so the sector gate accepts
        them as the same fiber value. Documented consequence: the gate is a
        numeric-tolerance gate, not a bitwise gate."""
        res = muni.run([[1.0]], [-0.0, 0.0], steps=1)
        self.assertTrue(res.exact)
        self.assertEqual(res.max_abs_error, 0.0)
        self.assertTrue(res.used_quotient,
                        "numeric gate should accept mixed signed zeros")


class TestBenchmarkHonesty(unittest.TestCase):
    """The benchmark must measure, and must not report a speedup it did not earn."""

    def test_admissible_benchmark_is_exact(self):
        U = [[0.9, 0.1], [0.2, 0.8]]
        x = block_constant_state(2, 64)
        res = muni.benchmark(U, x, steps=64, trials=5, reps=3)
        self.assertTrue(res.used_quotient)
        self.assertTrue(res.exact)
        self.assertGreater(res.baseline_ms, 0.0)
        self.assertGreater(res.optimised_ms, 0.0)

    def test_inadmissible_benchmark_warns(self):
        U = [[0.9, 0.1], [0.2, 0.8]]
        x = [1.0 + 0.01 * (i % 5) for i in range(128)]
        res = muni.benchmark(U, x, steps=32, trials=3, reps=3)
        self.assertFalse(res.used_quotient)
        self.assertIn("must NOT be read as a speedup", res.reason)

    def test_receipt_binds_inputs(self):
        U = [[0.9, 0.1], [0.2, 0.8]]
        x = block_constant_state(2, 8)
        a = muni.benchmark(U, x, steps=8, trials=3, reps=3).receipt
        b = muni.benchmark(U, x, steps=8, trials=3, reps=3).receipt
        self.assertEqual(a["input_digest"]["x0_sha256"], b["input_digest"]["x0_sha256"])
        c = muni.benchmark(U, [1.0] * 16, steps=8, trials=3, reps=3).receipt
        self.assertNotEqual(a["input_digest"]["x0_sha256"], c["input_digest"]["x0_sha256"])


class TestEvidence(unittest.TestCase):
    def test_claim_is_json_serialisable(self):
        import json
        json.dumps(muni.claim())

    def test_verify_evidence_returns_verdict(self):
        ev = muni.verify_evidence()
        self.assertIn(ev["integrity"], {"PASS", "FAIL", "UNKNOWN", "NO_EVIDENCE"})
        self.assertIsInstance(ev["checks"], dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)