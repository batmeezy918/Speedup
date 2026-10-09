"""MUNI - production API for certified exact quotient reduction.

The one thing this library does: it runs your real data through the kernel that
Lean has proved exact on a specific algebraic class, and it tells you honestly
whether your data was in that class.

    >>> import muni
    >>> Ubar = [[0.9, 0.1], [0.2, 0.8]]      # r x r quotient operator
    >>> x0 = [1.0, 1.0, 2.0, 2.0]            # m=2 fibers, r=2 blocks
    >>> res = muni.run(Ubar, x0, steps=10)
    >>> res.exact                             # verified against the original
    True
    >>> res.used_quotient                     # admissible -> certified path
    True
    >>> res.speedup                           # measured on YOUR data
    27.4

If your data is not block-constant the kernel refuses and falls back:

    >>> res = muni.run(Ubar, [1.0, 1.1, 2.0, 2.0], steps=10)
    >>> res.used_quotient
    False
    >>> res.exact
    True
    >>> res.reason
    'INADMISSIBLE: state leaves the block-constant sector; ran original path'

Scope, stated once and enforced everywhere
------------------------------------------
The speedup is exact for operators of the form U = Ubar (x) I_m applied to
states that are constant across each identity fiber. That is the entire claim.
No claim is made for arbitrary operators, arbitrary neural networks, arbitrary
hardware, or inputs outside that sector. `muni.claim()` returns this text and
the current evidence hashes.
"""

from .core import (
    run,
    benchmark,
    Result,
    status_name,
    is_admissible,
    measure_sector,
    claim,
    verify_evidence,
    version,
    SCOPE_TEXT,
    SCOPE_EXCLUSIONS,
    LICENSE,
)

__all__ = [
    "run",
    "benchmark",
    "Result",
    "status_name",
    "is_admissible",
    "measure_sector",
    "claim",
    "verify_evidence",
    "version",
    "SCOPE_TEXT",
    "SCOPE_EXCLUSIONS",
    "LICENSE",
]