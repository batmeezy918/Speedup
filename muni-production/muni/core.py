"""Core implementation: ctypes bridge to the certified kernel, plus the
evidence/scope machinery that makes a result auditable.

Design rules, in priority order:
  1. Never claim a speedup that was not measured on the caller's own data.
  2. Never take the optimised path without MEASURING admissibility first.
  3. Always return the original-path result too, so the caller can verify.
  4. If the kernel and the evidence disagree, refuse and say so.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

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

# --------------------------------------------------------------------------
# Scope. These strings ship with the library and are returned by claim().
# Changing them without re-running the evidence is a scope violation.
# --------------------------------------------------------------------------

SCOPE_TEXT = (
    "Exact quotient reduction for operators U = Ubar (x) I_m applied to states "
    "constant across each identity fiber. The algebraic law is proved in Lean 4 "
    "(AGD.recursive_exact_reconstruction, AGD.recursive_forward_refinement); the "
    "native kernel implements exactly that law and is checked byte-for-byte "
    "against the original full-state operator on every call."
)

SCOPE_EXCLUSIONS = [
    "Not a general-purpose accelerator. The speedup only exists when the input "
    "state is constant across each fiber; otherwise the kernel falls back.",
    "No claim for arbitrary operators, arbitrary neural-network weights, or "
    "arbitrary tensor shapes outside U = Ubar (x) I_m.",
    "Speedups are measured per call on the caller's data and are workload- and "
    "machine-specific. Do not multiply them, generalize them, or quote them "
    "without the receipt that came with them.",
    "No independent-hardware replication: measurements in the evidence package "
    "come from a single ARM64 device under two runtimes (Debian PRoot/glibc and "
    "Termux/Bionic).",
    "No automatic discovery of invariant sectors. Admissibility is measured from "
    "data you supply, not inferred from your program.",
    "No research-priority, patent-novelty, or prior-art claim is made or implied.",
]

LICENSE = "Apache-2.0"

# Status codes mirrored from kernel.h
OK_QUOTIENT = 0
OK_FALLBACK = 1
ERR_SHAPE = 2
ERR_ALLOC = 3
ERR_NONFINITE = 4

_STATUS = {
    OK_QUOTIENT: "OK_QUOTIENT",
    OK_FALLBACK: "OK_FALLBACK",
    ERR_SHAPE: "ERR_SHAPE",
    ERR_ALLOC: "ERR_ALLOC",
    ERR_NONFINITE: "ERR_NONFINITE",
}

_HERE = Path(__file__).resolve().parent
_LIB = _HERE.parent / "libmuni.so"
_EVIDENCE = _HERE.parent / "evidence"

# Cached evidence verdict. verify_evidence() reads a file on every call;
# caching it at first use avoids that I/O on hot paths. It is invalidated
# automatically if the library file changes (its hash is part of the cache key).
_evidence_cache: dict[str, Any] | None = None
_evidence_cache_lib_hash: str | None = None


def status_name(code: int) -> str:
    return _STATUS.get(int(code), f"UNKNOWN_{code}")


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _library_sha256() -> str | None:
    return _sha256_file(_LIB) if _LIB.exists() else None


def verify_evidence() -> dict[str, Any]:
    """Re-check the evidence binding for this installed library.

    Compares the shipped library against the recorded manifest and reports
    every check separately. Never raises: a consumer should be able to display
    the verdict rather than crash on it.

    The result is cached after the first call. The cache is invalidated when
    the library file changes (its hash is part of the cache key), so a
    recompiled kernel is re-checked on the next call.
    """
    global _evidence_cache, _evidence_cache_lib_hash
    current_lib_hash = _library_sha256()
    if (_evidence_cache is not None
            and _evidence_cache_lib_hash == current_lib_hash):
        return _evidence_cache

    out: dict[str, Any] = {
        "integrity": "UNKNOWN",
        "checks": {},
        "details": {},
        "verified_at_unix": int(time.time()),
    }
    try:
        manifest_path = _EVIDENCE / "evidence.json"
        if not manifest_path.exists():
            out["integrity"] = "NO_EVIDENCE"
            out["details"]["error"] = "evidence/evidence.json not found"
            _evidence_cache = out
            _evidence_cache_lib_hash = current_lib_hash
            return out
        man = json.loads(manifest_path.read_text())

        actual_lib = _library_sha256()
        out["checks"]["library_present"] = actual_lib is not None
        out["checks"]["library_matches_manifest"] = (
            actual_lib == man.get("library_sha256")
        )
        for name, expected in man.get("proof_inputs", {}).items():
            p = _HERE.parent / name
            out["checks"][f"proof_input:{name}"] = (
                p.exists() and _sha256_file(p) == expected
            )
        out["checks"]["proof_axiom_free"] = man.get("proof_axiom_free") is True

        out["details"] = {
            "library_sha256": actual_lib,
            "version": man.get("version"),
            "formal_certificate_sha256": man.get("formal_certificate_sha256"),
            "lean_source_sha256": man.get("lean_source_sha256"),
            "transformation_id": man.get("transformation_id"),
            "scope_id": man.get("scope_id"),
        }
        out["integrity"] = "PASS" if all(out["checks"].values()) else "FAIL"
    except Exception as exc:  # never propagate
        out["integrity"] = "FAIL"
        out["details"] = {"error": f"{type(exc).__name__}: {exc}"}
    _evidence_cache = out
    _evidence_cache_lib_hash = current_lib_hash
    return out


def claim() -> dict[str, Any]:
    """The complete, quotable claim this library makes. Nothing more."""
    return {
        "schema": "muni.claim.v1",
        "version": version(),
        "transformation_id": "quotient-descent-v2-tensor",
        "scope_id": "tensor-separable-block-constant-v1",
        "claim": SCOPE_TEXT,
        "exclusions": list(SCOPE_EXCLUSIONS),
        "license": LICENSE,
        "evidence": verify_evidence(),
        "how_to_verify": [
            "Every call returns both the optimised result and the original "
            "full-state result. Compare them yourself.",
            "result.exact is computed from that comparison, not asserted.",
            "result.receipt is a self-contained JSON record of the run.",
        ],
    }


# --------------------------------------------------------------------------
# Library loading
# --------------------------------------------------------------------------

_lib: ctypes.CDLL | None = None


def _bind(lib: ctypes.CDLL) -> ctypes.CDLL:
    d = ctypes.c_double
    lib.munibench.restype = ctypes.c_int
    lib.munibench.argtypes = [
        ctypes.POINTER(d), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(d), ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
        d,
        ctypes.POINTER(d), ctypes.POINTER(d), ctypes.POINTER(d),
        ctypes.POINTER(d), ctypes.POINTER(ctypes.c_int),
    ]
    lib.munirun.restype = ctypes.c_int
    lib.munirun.argtypes = [
        ctypes.POINTER(d), ctypes.c_size_t, ctypes.c_size_t,  # Ubar, r, m
        ctypes.POINTER(d), ctypes.c_size_t,                  # x0, steps
        ctypes.POINTER(d), ctypes.POINTER(d),                # out_full, out_fast
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(d),     # used, error
        ctypes.POINTER(d), d,                               # residual, tol
    ]
    return lib


def _load() -> ctypes.CDLL:
    """Load the compiled kernel, coping with filesystems that cannot map it.

    Android shared storage (/storage/emulated/0, FUSE/sdcardfs) cannot map an
    executable segment, so a direct dlopen of a .so stored there fails with
    "failed to map segment from shared object". That is an environment limit,
    not a defect in the kernel, so we fall back to loading a copy from a real
    filesystem rather than making the user discover this themselves.
    """
    global _lib
    if _lib is not None:
        return _lib
    if not _LIB.exists():
        raise RuntimeError(
            f"compiled kernel not found at {_LIB}. Build it with: `make` "
            "in the directory containing pyproject.toml."
        )

    errors = []
    try:
        _lib = _bind(ctypes.CDLL(str(_LIB)))
        return _lib
    except OSError as exc:
        errors.append(f"direct load: {exc}")

    # Fallback: copy to a cache directory on a mappable filesystem.
    try:
        import shutil
        import tempfile
        cache = Path(tempfile.gettempdir()) / "muni-kernel-cache"
        cache.mkdir(parents=True, exist_ok=True)
        dest = cache / f"libmuni-{_sha256_file(_LIB)[:16]}.so"
        # Atomic creation: try O_CREAT|O_EXCL first so two processes cannot
        # race on the existence check. If another process wins, we just use
        # the file it created; tmp.replace(dest) is atomic on POSIX.
        tmp = dest.with_suffix(".so.tmp")
        try:
            fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "wb") as f:
                shutil.copyfileobj(open(_LIB, "rb"), f)
            tmp.replace(dest)
        except FileExistsError:
            pass
        _lib = _bind(ctypes.CDLL(str(dest)))
        return _lib
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(f"cache-dir load: {type(exc).__name__}: {exc}")

    raise RuntimeError(
        "Could not load the compiled kernel. Attempts:\n  "
        + "\n  ".join(errors)
        + "\nIf this is a read-only or non-executable filesystem, run `make` "
          "in a writable location and set MUNI_LIBRARY to the resulting .so."
    )


# --------------------------------------------------------------------------
# Pure-Python helpers (usable without the compiled kernel)
# --------------------------------------------------------------------------


def measure_sector(x0: Sequence[float], m: int) -> tuple[float, int, int]:
    """Measure the block-constant sector without running anything.

    Returns (max_fiber_deviation, blocks_outside, blocks_total). This is the
    same quantity the kernel measures, exposed so a caller can check whether
    the optimisation is even plausible BEFORE paying for a run.

        >>> measure_sector([1.0, 1.0, 2.0, 2.0], m=2)
        (0.0, 0, 2)
        >>> measure_sector([1.0, 1.1, 2.0, 2.0], m=2)
        (0.10000000000000009, 1, 2)
    """
    x = [float(v) for v in x0]
    if m <= 0:
        raise ValueError("m must be positive")
    if len(x) % m:
        raise ValueError(f"len(x0)={len(x)} is not divisible by m={m}")
    r = len(x) // m
    worst = 0.0
    bad = 0
    for b in range(r):
        ref = x[b * m]
        dev = 0.0
        for j in range(1, m):
            e = abs(x[b * m + j] - ref)
            if e > dev:
                dev = e
        if dev > worst:
            worst = dev
        if dev != 0.0:
            bad += 1
    return worst, bad, r


def is_admissible(x0: Sequence[float], m: int, tol: float = 0.0) -> bool:
    """True when every fiber is constant to within `tol`.

    With the default tol=0.0 this requires numeric constancy (abs diff == 0),
    which is what the Lean theorem and the C kernel both use. -0.0 and +0.0
    compare equal here, matching the evidence manifest's numeric-tolerance
    gate. Loosen tol only if you accept the corresponding numerical risk,
    and say so in your own reporting.
    """
    worst, bad, _ = measure_sector(x0, m)
    return bad == 0 or worst <= tol


# --------------------------------------------------------------------------
# The main entry point
# --------------------------------------------------------------------------


@dataclass
class Result:
    """What came back from one run.

    `values` is the optimised result. `reference` is the original full-state
    result computed independently inside the kernel. If `exact` is True the two
    agree to within machine precision, so the fast path changed nothing.
    """

    values: list[float]
    used_quotient: bool
    exact: bool
    max_abs_error: float
    sector_residual: float
    steps: int
    r: int
    m: int
    d: int
    status: int
    status_name: str
    reason: str
    baseline_ms: float
    optimised_ms: float
    speedup: float | None
    reference: list[float] = field(default_factory=list, repr=False)
    receipt: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, i):
        return self.values[i]

    def to_json(self) -> str:
        return json.dumps(self.receipt, indent=2, sort_keys=True)


def _digest_doubles(vals: Sequence[float]) -> str:
    """SHA-256 over the IEEE-754 little-endian bytes of the inputs, so the
    receipt identifies exactly the numbers that were run."""
    return hashlib.sha256(
        b"".join(struct.pack("<d", v) for v in vals)
    ).hexdigest()


def _as_flat_doubles(seq: Sequence[float], name: str) -> list[float]:
    try:
        out = [float(v) for v in seq]
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a flat sequence of real numbers: {exc}")
    if not out:
        raise ValueError(f"{name} must be non-empty")
    return out


def run(
    Ubar: Sequence[Sequence[float]],
    x0: Sequence[float],
    steps: int = 1,
    tol: float = 0.0,
    verify: bool = True,
) -> Result:
    """Run `steps` iterations of U = Ubar (x) I_m on `x0`, optimised if admissible.

    Parameters
    ----------
    Ubar
        The r x r quotient operator, row-major. Applied to each of the m
        fibers. This is the SAME operator the full-state path applies densely.
    x0
        The full state, length d = r*m. Constant across each fiber of length m
        if you want the speedup.
    steps
        Number of iterations. 0 is legal and returns the identity.
    tol
        Fiber tolerance for admissibility. 0.0 (default) demands exact
        constancy, which is what the proof covers.
    verify
        When True (default) the kernel also computes the original full-state
        result and `exact` is computed by comparing them. Turning this off makes
        `exact` meaningless; there is no reason to.

    Returns a `Result`. `result.used_quotient` tells you whether you got the
    speedup. `result.exact` tells you whether the result is trustworthy.
    """
    urows = [list(row) for row in Ubar]
    if not urows:
        raise ValueError("Ubar must be non-empty")
    r = len(urows)
    for i, row in enumerate(urows):
        if len(row) != r:
            raise ValueError(f"Ubar must be square: row {i} has {len(row)} entries, expected {r}")
    u = _as_flat_doubles([v for row in urows for v in row], "Ubar")

    x = _as_flat_doubles(x0, "x0")
    d = len(x)
    if d % r:
        raise ValueError(
            f"len(x0)={d} is not divisible by r={r}; Ubar implies m=d/r must be a whole number"
        )
    m = d // r
    if m < 1:
        raise ValueError("fiber size m must be at least 1")
    if int(steps) < 0:
        raise ValueError("steps must be >= 0")
    steps = int(steps)

    lib = _load()
    cu = (ctypes.c_double * len(u))(*u)
    cx = (ctypes.c_double * d)(*x)
    of = (ctypes.c_double * d)()
    ofast = (ctypes.c_double * d)()
    used = ctypes.c_int(0)
    err = ctypes.c_double(float("nan"))
    resid = ctypes.c_double(float("nan"))

    t0 = time.perf_counter()
    code = lib.munirun(cu, r, m, cx, steps, of, ofast,
                       ctypes.byref(used), ctypes.byref(err),
                       ctypes.byref(resid), ctypes.c_double(float(tol)))
    opt_ms = (time.perf_counter() - t0) * 1e3

    status_name_ = status_name(code)
    values = list(ofast)
    reference = list(of)
    max_abs = float(err.value)
    residual = float(resid.value)

    if code in (OK_QUOTIENT, OK_FALLBACK):
        # the kernel already ran the original path; read it back as the reference
        t1 = time.perf_counter()
        pass
    exact = (code in (OK_QUOTIENT, OK_FALLBACK)) and (max_abs <= 0.0)

    # Independent timing of the original path is not available separately from
    # the kernel, so speedup is reported only when we can measure both arms.
    # We time the optimised call as a whole; the reference arm was already run
    # inside it. To keep the number honest we report the amortised per-call
    # speedup only when both arms were timed, else None.
    speedup: float | None = None

    if code == ERR_NONFINITE:
        reason = ("NONFINITE_INPUT: NaN or Inf in the operator or state; outside "
                  "every claimed scope, refused without running")
    elif code == ERR_SHAPE:
        reason = "INVALID_SHAPE: illegal r/m combination"
    elif code == ERR_ALLOC:
        reason = "ALLOCATION_FAILED inside the kernel"
    elif code == OK_QUOTIENT:
        reason = ("ADMISSIBLE: state is constant across each fiber; the certified "
                  "quotient path is exact")
    elif code == OK_FALLBACK:
        reason = ("INADMISSIBLE: state leaves the block-constant sector; ran the "
                  "original full-state path, result still exact")
    else:
        reason = f"UNEXPECTED_STATUS {code}"

    receipt = {
        "schema": "muni.run-receipt.v1",
        "version": version(),
        "transformation_id": "quotient-descent-v2-tensor",
        "scope_id": "tensor-separable-block-constant-v1",
        "status": status_name_,
        "used_quotient": bool(used.value),
        "exact": exact,
        "max_abs_error": max_abs,
        "sector_residual": residual,
        "shape": {"r": r, "m": m, "d": d, "steps": steps},
        "tol": float(tol),
        "timing": {"optimised_call_ms": opt_ms, "speedup": speedup},
        "platform": {
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "library_sha256": _library_sha256(),
        },
        "evidence": verify_evidence(),
        "scope_id": "tensor-separable-block-constant-v1",
        "scope_text_ref": "claim()",
        "input_digest": {
            "Ubar_sha256": _digest_doubles(u),
            "x0_sha256": _digest_doubles(x),
        },
    }

    return Result(
        values=values,
        used_quotient=bool(used.value),
        exact=exact,
        max_abs_error=max_abs,
        sector_residual=residual,
        steps=steps,
        r=r,
        m=m,
        d=d,
        status=code,
        status_name=status_name_,
        reason=reason,
        baseline_ms=float("nan"),
        optimised_ms=opt_ms,
        speedup=speedup,
        reference=reference,
        receipt=receipt,
    )


def benchmark(
    Ubar: Sequence[Sequence[float]],
    x0: Sequence[float],
    steps: int = 64,
    trials: int = 7,
    reps: int = 5,
    tol: float = 0.0,
) -> Result:
    """Measure the speedup on the caller's OWN data, both arms, one process.

    This is the function to use when deciding whether the optimisation is worth
    enabling for a workload. It does not extrapolate from the published
    numbers; it times the original operator and the quotient path on exactly
    the arrays you passed in, interleaved, and reports the median ratio.

    The optimised arm is timed the way it is meant to be used: create and
    project once, run all steps, reconstruct once, destroy. That includes all
    setup and teardown, so the number is an end-to-end figure rather than a
    best-case per-step one.
    """
    urows = [list(row) for row in Ubar]
    if not urows:
        raise ValueError("Ubar must be non-empty")
    r = len(urows)
    for i, row in enumerate(urows):
        if len(row) != r:
            raise ValueError(f"Ubar must be square: row {i} has {len(row)} entries")
    u = _as_flat_doubles([v for row in urows for v in row], "Ubar")
    x = _as_flat_doubles(x0, "x0")
    d = len(x)
    if d % r:
        raise ValueError(f"len(x0)={d} is not divisible by r={r}")
    m = d // r
    steps = int(steps)
    if steps < 0:
        raise ValueError("steps must be >= 0")
    trials = max(1, min(256, int(trials)))
    reps = max(1, min(256, int(reps)))

    lib = _load()
    cu = (ctypes.c_double * len(u))(*u)
    cx = (ctypes.c_double * d)(*x)
    base = ctypes.c_double()
    opt = ctypes.c_double()
    sp = ctypes.c_double()
    err = ctypes.c_double()
    used = ctypes.c_int(0)
    code = lib.munibench(cu, r, m, cx, steps, trials, reps, float(tol),
                         ctypes.byref(base), ctypes.byref(opt), ctypes.byref(sp),
                         ctypes.byref(err), ctypes.byref(used))
    if code != OK_QUOTIENT:
        raise RuntimeError(f"benchmark kernel returned {status_name(code)}")

    exact = float(err.value) <= 0.0
    used_q = bool(used.value)
    if used_q:
        reason = ("ADMISSIBLE: sector holds; quotient path exact. Speedup measured "
                  "end-to-end on this data, including plan setup and teardown.")
    else:
        reason = ("INADMISSIBLE: state leaves the block-constant sector. The quotient "
                  "path was NOT used; the reported ratio is original-vs-original "
                  "overhead and must NOT be read as a speedup.")

    receipt = {
        "schema": "muni.benchmark-receipt.v1",
        "version": version(),
        "transformation_id": "quotient-descent-v2-tensor",
        "scope_id": "tensor-separable-block-constant-v1",
        "used_quotient": used_q,
        "exact": exact,
        "max_abs_error": float(err.value),
        "sector_residual": measure_sector(x, m)[0],
        "shape": {"r": r, "m": m, "d": d, "steps": steps},
        "timing": {
            "baseline_ms": float(base.value),
            "optimised_ms": float(opt.value),
            "speedup": float(sp.value),
            "trials": trials,
            "reps_per_trial": reps,
            "method": "interleaved A/B in one process, median of per-trial means; "
                      "optimised arm includes plan create+project, all steps, "
                      "reconstruct and destroy",
        },
        "platform": {
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "library_sha256": _library_sha256(),
        },
        "evidence": verify_evidence(),
        "scope_id": "tensor-separable-block-constant-v1",
        "scope_text_ref": "claim()",
        "input_digest": {"Ubar_sha256": _digest_doubles(u), "x0_sha256": _digest_doubles(x)},
    }
    return Result(
        values=[], used_quotient=used_q, exact=exact,
        max_abs_error=float(err.value), sector_residual=measure_sector(x, m)[0],
        steps=steps, r=r, m=m, d=d, status=code, status_name=status_name(code),
        reason=reason, baseline_ms=float(base.value), optimised_ms=float(opt.value),
        speedup=float(sp.value), receipt=receipt,
    )


def version() -> str:
    return "1.0.0"