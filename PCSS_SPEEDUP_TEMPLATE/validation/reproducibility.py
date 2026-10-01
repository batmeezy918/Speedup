"""Reproducibility check. One run is not a pass."""

def check(run_count: int, semantic_match: bool) -> bool:
    return run_count >= 3 and semantic_match
