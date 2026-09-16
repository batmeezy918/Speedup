"""Canonical PCSS engine package.

Engines produce EVIDENCE. Only publisher/strict_gate.py promotes.

Responsibilities:
    engines/quotient.py         Q : forward quotient preservation
    engines/reconstruction.py   Q^-1 : reverse reconstruction
    engines/invariant.py        Omega : invariant preservation
    engines/performance.py      X : timing statistics / direct speedup
    engines/attribution.py      attribution / work-vs-wallclock separation
    engines/linear_exact.py     exact invariant-sector reference workload
    engines/discovery.py        admissible quotient discovery (Phase 17)
    engines/refinement.py       quotient refinement loop (Phase 18)
"""