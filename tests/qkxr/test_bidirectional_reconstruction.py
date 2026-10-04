import unittest

from qkxr.execution_quotient import (
    MarketState,
    coarse_quotient,
    execution_quotient,
    execution_signature,
    representative_reconstruct,
)


class BidirectionalReconstructionTest(unittest.TestCase):
    def test_representative_round_trip_preserves_execution(self):
        states = [
            MarketState(84797.19, 84797.20, -0.43653),
            MarketState(84797.19, 84797.20, -0.43773),
        ]
        for state in states:
            q = execution_quotient(state)
            reconstructed = representative_reconstruct(states, q)
            self.assertIsNotNone(reconstructed)
            self.assertEqual(execution_signature(state), execution_signature(reconstructed))
            self.assertEqual(execution_quotient(reconstructed), q)

    def test_rejected_coarse_class_is_not_used_for_execution_reconstruction(self):
        states = [
            MarketState(84797.19, 84797.20, -0.43653),
            MarketState(84797.19, 84797.20, -0.49741),
        ]
        self.assertEqual(coarse_quotient(states[0]), coarse_quotient(states[1]))
        self.assertNotEqual(execution_quotient(states[0]), execution_quotient(states[1]))
        for state in states:
            reconstructed = representative_reconstruct(states, execution_quotient(state))
            self.assertEqual(execution_signature(state), execution_signature(reconstructed))


if __name__ == "__main__":
    unittest.main()
