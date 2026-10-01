"""Measurement hook. This template does not emit a speedup number."""

def run_pair(baseline_runner: str, candidate_runner: str, repeats: int):
    if repeats < 1 or not baseline_runner or not candidate_runner:
        raise ValueError("admissible measurement requires both runners and repeats >= 1")
    return {"status": "NOT_RUN", "repeats": repeats}
