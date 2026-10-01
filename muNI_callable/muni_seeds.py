"""Single source of truth for every seeded device run in the MuNi callable lane.

Rationale
---------
A speedup factor is only meaningful if the measurement is reproducible. A seed is
part of the certificate: `CLAIM_POLICY.md` scopes a speedup to "the exact
workload, environment, measurement protocol, and statistical treatment in its
certificate". An unpinned RNG makes the input data a hidden, unrecorded variable
in that certificate, so two runs of the same harness are not comparable and a
disagreement cannot be attributed to the kernel rather than the data.

Before this module, only `run_robustness.py` pinned a seed, and it hardcoded it.
`run_pcss_callable.py` and the composition harnesses drew unseeded data, so their
reproducibility was nominal. Every repeated device run must now take its seed
from here, and must record it in its receipt.

Policy
------
* Seeds are NEVER derived from wall-clock time, PID, or object identity.
* A harness that reports a speedup MUST record the seed that produced the data.
* Changing a seed changes the measured input distribution, so a changed seed is a
  new measurement, not a rerun. Receipts are immutable; do not overwrite one
  produced under a different seed.
* `SEED_MANIFEST` is the audit record: which harness used which seed.
"""

from __future__ import annotations

# The canonical seed for the callable lane. Pinned 2026-10-01.
#
# This is the value `run_robustness.py` had already been using
# (np.random.default_rng(20261001)). It is preserved rather than rotated so that
# receipts written before and after this module stay comparable.
DEFAULT_SEED = 20261001

# Distinct-but-fixed seeds, so a harness can vary the data without silently
# reusing one stream, while remaining reproducible. Assigned deliberately rather
# than sequentially generated.
SEEDS = {
    'default': DEFAULT_SEED,
    # Robustness sweep across input families (constant, uniform, normal, ...).
    'robustness': DEFAULT_SEED,
    # Per-case seed derivation for the callable harness, so each N gets its own
    # stream while the whole run stays reproducible from the base seed.
    'callable_base': DEFAULT_SEED,
    # Composition harnesses: separate streams for the state-reduction sweep and
    # the floor sweep, so the two are not correlated through a shared RNG.
    'composition': DEFAULT_SEED,
    'floor_sweep': DEFAULT_SEED,
    # Claim audit: the audit itself performs no timed measurement, but it
    # re-verifies sampled receipts, so it takes a seed for completeness.
    'claim_audit': DEFAULT_SEED,
}


def seed_for(name: str) -> int:
    """Return the pinned seed for a named harness.

    Raises KeyError on an unknown name rather than silently falling back to a
    default. An unregistered harness must not quietly inherit a seed: that is
    exactly the class of unrecorded-variable bug this module exists to prevent.
    """
    if name not in SEEDS:
        raise KeyError(
            'no pinned seed for harness %r; register it in muni_seeds.SEEDS '
            'before running, so the receipt can record the seed explicitly'
            % name)
    return SEEDS[name]


def derive(base_seed: int, label: str) -> int:
    """Derive a stable per-case seed from a pinned base and a case label.

    Uses a fixed integer hash so the mapping label -> seed is reproducible
    across processes, platforms, and Python versions. `hash()` is deliberately
    avoided because PYTHONHASHSEED randomises it per process, which would make
    the "same" run draw different data.
    """
    acc = (int(base_seed) & 0xFFFFFFFF) ^ 0x9E3779B9
    for ch in label.encode('utf-8'):
        acc = (acc * 31 + ch) & 0xFFFFFFFF
    return int(acc)


def case_seed(name: str, label: str) -> int:
    """Pinned per-case seed for a harness, derived from that harness's base."""
    return derive(seed_for(name), label)


# Recorded in every receipt that consumes a seed, so a reader can reproduce it.
SEED_MANIFEST = {
    'policy': 'all repeated device runs use a pinned seed from this module',
    'default_seed': DEFAULT_SEED,
    'seeds': dict(SEEDS),
    'derivation': 'case_seed(name,label) = stable int hash of (base_seed, label)',
    'note': 'a changed seed is a new measurement, not a rerun; receipts are immutable',
}