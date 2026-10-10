import unittest

from qkxr.execution_quotient import (
    MarketState,
    coarse_quotient,
    execution_quotient,
    execution_signature,
    execution_preserving,
)


class ExecutionPreservingQuotientTest(unittest.TestCase):
    def test_known_market_collision_is_rejected(self):
        states = [
            MarketState(84797.19, 84797.20, -0.43653),
            MarketState(84797.19, 84797.20, -0.43773),
            MarketState(84797.19, 84797.20, -0.49741),
        ]
        self.assertEqual(coarse_quotient(states[0]), coarse_quotient(states[1]))
        self.assertEqual(coarse_quotient(states[1]), coarse_quotient(states[2]))
        self.assertEqual(execution_signature(states[0]), "HOLD")
        self.assertEqual(execution_signature(states[1]), "HOLD")
        self.assertEqual(execution_signature(states[2]), "SELL")
        self.assertFalse(execution_preserving(states))

    def test_uniform_class_is_accepted(self):
        states = [
            MarketState(84797.19, 84797.20, -0.43653),
            MarketState(84797.19, 84797.20, -0.43773),
        ]
        self.assertTrue(execution_preserving(states))

    def test_semantic_refinement_separates_collision(self):
        states = [
            MarketState(84797.19, 84797.20, -0.43653),
            MarketState(84797.19, 84797.20, -0.49741),
        ]
        self.assertNotEqual(execution_quotient(states[0]), execution_quotient(states[1]))


if __name__ == "__main__":
    unittest.main()
