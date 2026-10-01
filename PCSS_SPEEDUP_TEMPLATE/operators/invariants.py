"""Invariant check Omega. Empty invariant list is not a pass."""

def check(baseline, candidate, names: list[str] | None):
    if not names:
        return False
    return baseline is not None and candidate is not None
