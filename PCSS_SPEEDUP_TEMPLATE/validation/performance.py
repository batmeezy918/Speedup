"""Performance check. A missing baseline is not a speedup."""

def check(baseline_ns: int | None, candidate_ns: int | None) -> bool:
    if baseline_ns is None or candidate_ns is None or candidate_ns <= 0:
        return False
    return baseline_ns > candidate_ns
