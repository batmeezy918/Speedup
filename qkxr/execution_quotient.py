"""Execution-preserving market quotient primitives.

A quotient class is admissible only when every declared execution
operator has the same observable signature across the class.

The current execution operator is explicit and deterministic:
SELL iff imbalance < -0.45, otherwise HOLD.

This is a validation primitive, not a claim about market dynamics
or economic profitability.
"""

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class MarketState:
    bid: float
    ask: float
    imbalance: float


def spread_ticks(state: MarketState, tick_size: float = 0.01) -> int:
    if tick_size <= 0:
        raise ValueError("tick_size must be positive")
    return round((state.ask - state.bid) / tick_size)


def imbalance_bucket(state: MarketState, width: float = 0.1) -> int:
    if width <= 0:
        raise ValueError("width must be positive")
    bucket = int(state.imbalance // width)
    return max(-9, min(9, bucket))


def coarse_quotient(
    state: MarketState,
    tick_size: float = 0.01,
    imbalance_width: float = 0.1,
) -> Tuple[int, int]:
    return (
        spread_ticks(state, tick_size),
        imbalance_bucket(state, imbalance_width),
    )


def execution_signature(state: MarketState, sell_threshold: float = -0.45) -> str:
    return "SELL" if state.imbalance < sell_threshold else "HOLD"


def execution_preserving(
    states: Iterable[MarketState],
    tick_size: float = 0.01,
    imbalance_width: float = 0.1,
) -> bool:
    """Check whether the coarse quotient preserves execution semantics."""
    classes = {}
    for state in states:
        key = coarse_quotient(state, tick_size, imbalance_width)
        signature = execution_signature(state)
        previous = classes.setdefault(key, signature)
        if previous != signature:
            return False
    return True


def execution_quotient(state: MarketState) -> Tuple[int, int, str]:
    """Minimal semantic refinement of the coarse quotient."""
    coarse = coarse_quotient(state)
    return (*coarse, execution_signature(state))
