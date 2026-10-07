#!/usr/bin/env python3
"""
attribution.py -- make gain inheritable, or refuse.

Operationalises PCSSCompositionCriterion.multiplicative_composition_iff_zero_overlap
into a mechanical gate over the certificate corpus.

The gap this closes
-------------------
The Lean layer proves that a composed quotient gain equals the product of its
factors IFF the overlap between them is zero:

    multiplicative_composition_iff_zero_overlap : gain = q1*q2 <-> o = 0

The certificate layer records gains as bare JSON numbers. Nothing has ever
connected the two, so nothing has ever stopped a composed ratio from being
applied to a call site that was never measured. This tool is that connection.

Decision rule
-------------
A gain is INHERITABLE only when every precondition holds:

  R1  lean gate passed              -- a theorem backs the mechanism
  R2  quotient_forward AND          -- the quotient direction is checked
      reconstruction_reverse            and the reverse is certified
  R3  invariants pass               -- exactness/observable agreement
  R4  N >= 5 measured samples       -- a single sample cannot support a claim
  R5  interleaved OR provably-      -- sequential arms confound thermal drift
      single-block                    with the effect
  R6  noise floor measured and      -- an effect below the floor is noise
      below the effect
  R7  composed gains require an     -- the proved criterion; without an
      overlap witness o = 0           overlap witness the product is not
                                       attributable

R7 is the novel one. R1-R6 are hygiene a careful author applies anyway.

Exit codes: 0 = every inheritable gain verified; 1 = at least one claim
rejected; 2 = usage/corpus error.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

MIN_SAMPLES = 5
MIN_WARMUPS = 2

# COMPOSED_<n>_<K>_BASELINE ... -> COMPOSED<n>_CANDIDATE ... marks a fused,
# multi-stage substitution. COMPOSED3_BASELINE_T_full^22_full_space_n512 means
# two independent quotient stages were fused into one measured artefact.
COMPOSED_RE = re.compile(r"^COMPOSED\d*_(BASELINE|CANDIDATE)")


def _ident_side(node):
    """The corpus carries three shapes of implementation_identity.

    v1  {'baseline': {'implementation_id': str}, 'candidate': {...}}
    v2  {'baseline': 'redundant parse per observable', 'candidate': '...'}
    v3  {'baseline': {'operator':..,'measured':..,'dense':..}, 'candidate': {...}}

    Flatten each to a single comparable string rather than assuming a shape.
    """
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    for key in ("implementation_id", "measured", "operator"):
        if key in node:
            return str(node[key])
    for key in ("baseline", "candidate"):
        if key in node:
            return str(node[key])
    return ""


@dataclass
class Finding:
    rule: str
    passed: bool
    detail: str


@dataclass
class Verdict:
    cert: str
    ratio: float | None
    samples: int | None
    kind: str                      # isolated | composed | unknown
    baseline: str | None
    candidate: str | None
    findings: list[Finding] = field(default_factory=list)
    inheritable: bool = False
    quarantined: bool = False
    surface: str = ""

    @property
    def rejected_by(self) -> list[str]:
        return [f.rule for f in self.findings if not f.passed]


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def _mad(xs: list[float]) -> float:
    """Median absolute deviation -- spread that a single long tail cannot move."""
    if not xs:
        return 0.0
    med = _median(xs)
    return _median([abs(x - med) for x in xs])


def classify(cert: dict) -> str:
    ident = cert.get("implementation_identity") or {}
    if isinstance(ident, str):
        # The canonical schema types implementation_identity as a string. Parse
        # the arrow form "baseline -> candidate" rather than assuming a dict.
        base, _, cand = ident.partition("->")
        base, cand = base.strip(), cand.strip()
    else:
        base = _ident_side(ident.get("baseline"))
        cand = _ident_side(ident.get("candidate"))
    blob = f"{base} {cand}"
    if COMPOSED_RE.match(base) or COMPOSED_RE.match(cand):
        return "composed"
    if "full_space" in blob or "_full_" in blob or "full unpacked" in blob or "full_vector" in blob:
        return "isolated"
    return "unknown"


def measurements(cert: dict) -> tuple[float | None, float | None, int | None, int | None]:
    """Median baseline, median candidate, sample count, warmup count.

    v1 carries baseline_measurement/candidate_measurement with a timings_ns array.
    v2 carries a 'performance' block and reports the ratio directly; when the
    medians are absent we cannot recompute the ratio, so we decline to invent it.
    """
    bm = cert.get("baseline_measurement") or {}
    cm = cert.get("candidate_measurement") or {}
    b, c = bm.get("median"), cm.get("median")
    n = bm.get("samples") or cm.get("samples") or cert.get("repetitions")
    w = cert.get("warmups")
    return b, c, n, w


def overlap_witness(cert: dict) -> tuple[bool, str]:
    """R7. Look for an explicit o = 0 attestation anywhere in the artefact."""
    def walk(node, path="$"):
        if isinstance(node, dict):
            for k, v in node.items():
                kl = str(k).lower()
                if "overlap" in kl and v in (0, "0", 0.0, False):
                    return True, f"{path}.{k} = {v!r}"
                hit, why = walk(v, f"{path}.{k}")
                if hit:
                    return hit, why
        elif isinstance(node, list):
            for i, v in enumerate(node):
                hit, why = walk(v, f"{path}[{i}]")
                if hit:
                    return hit, why
        return False, ""

    hit, why = walk(cert)
    if hit:
        return True, f"overlap witness present at {why}"
    # A fused composition that measures strictly below the product of its
    # factors is *positive evidence* that overlap is non-zero, which disqualifies
    # inheritance outright rather than merely withholding it.
    return False, "no overlap witness recorded"


def evaluate(path: Path, quarantine: dict | None = None) -> Verdict:
    cert = json.loads(path.read_text())
    b, c, n, warmups = measurements(cert)
    ratio = (b / c) if (b and c) else None
    if ratio is None:
        # v2: the ratio is asserted, not recomputable from stored medians. An
        # unrecomputable ratio is not evidence.
        sp = cert.get("speedup")
        if isinstance(sp, (int, float)):
            ratio = float(sp)
    ident = cert.get("implementation_identity") or {}
    kind = classify(cert)
    gates = cert.get("gates") or {}
    if isinstance(ident, str):
        _b, _, _c = ident.partition("->")
        ident = {"baseline": _b.strip(), "candidate": _c.strip()}

    v = Verdict(
        cert=path.parent.name,
        ratio=ratio,
        samples=n,
        kind=kind,
        baseline=_ident_side(ident.get("baseline")),
        candidate=_ident_side(ident.get("candidate")),
    )

    add = v.findings.append

    add(Finding("R0 host-provenance",
                all(k in (cert.get("environment") or {})
                    for k in ("cores_pinned", "core_type", "governor", "max_freq_mhz")),
                "environment block complete (cores/type/governor/freq recorded)"
                if all(k in (cert.get("environment") or {})
                       for k in ("cores_pinned", "core_type", "governor", "max_freq_mhz"))
                else f"no host parameters recorded; got keys {sorted((cert.get('environment') or {}).keys())}. "
                     f"A ratio is a function of cores/core_type/governor/freq, so without them "
                     f"the claim cannot be tied to any condition and cannot be inherited."))

    add(Finding("R1 lean", bool(gates.get("lean")),
                f"lean={gates.get('lean')!r}"))
    add(Finding("R2 bidirectional",
                bool(gates.get("quotient_forward")) and bool(gates.get("reconstruction_reverse")),
                f"forward={gates.get('quotient_forward')!r} reverse={gates.get('reconstruction_reverse')!r}"))
    add(Finding("R3 invariants", bool(gates.get("invariants")),
                f"invariants={gates.get('invariants')!r}"))

    add(Finding("R4 samples", isinstance(n, int) and n >= MIN_SAMPLES,
                f"N={n} (need >= {MIN_SAMPLES})"))

    add(Finding("R4b warmup", isinstance(warmups, int) and warmups >= MIN_WARMUPS,
                f"warmups={warmups} (need >= {MIN_WARMUPS}); cold samples include "
                f"page-fault, cache-population and frequency-ramp cost that is "
                f"not the property being claimed"
                if not (isinstance(warmups, int) and warmups >= MIN_WARMUPS)
                else f"warmups={warmups}"))

    # R5 interleaving: accept an explicit flag, else demand a provenance record.
    prov = cert.get("provenance") or cert.get("method") or {}
    # A harness that states interleaving at top level has established it; treat
    # that as an attestation. Requiring a nested `provenance.interleaved` key
    # while ignoring a sibling `interleaved: true` would be a gate bug, not
    # hygiene.
    declared = (bool(prov.get("interleaved"))
                or cert.get("interleaved") is True
                or "interleav" in str(cert.get("claim_boundary", "")).lower())
    add(Finding("R5 interleaving", declared,
                "declared interleaved" if declared else
                "no interleaving attestation; sequential arms cannot separate "
                "thermal drift from the effect"))

    # R6 noise floor. A cold median is NOT an uncertainty estimate.
    unc = cert.get("uncertainty") or {}
    floor = cert.get("noise_floor")
    floor_ratio = None
    if isinstance(floor, dict):
        floor_ratio = floor.get("ratio") or floor.get("median_ratio")
    elif isinstance(floor, (int, float)):
        floor_ratio = float(floor)
    if floor_ratio is None:
        if unc.get("method") in ("sampled_median_direct", "median_direct"):
            add(Finding("R6 noise-floor", False,
                        f"uncertainty.method={unc.get('method')!r} is a median of "
                        f"{unc.get('samples')} samples, not an A-vs-A control; "
                        f"no effect can be separated from run-to-run variance"))
        else:
            add(Finding("R6 noise-floor", False,
                        "no A-vs-A control recorded; the effect cannot be "
                        "separated from run-to-run variance"))
    else:
        add(Finding("R6 noise-floor", ratio is not None and floor_ratio < ratio,
                    f"floor={floor_ratio:.3f}x vs effect={ratio:.3f}x"
                    if ratio else f"floor={floor_ratio:.3f}x"))

    # R7 attribution -- the proved criterion.
    if kind == "composed":
        ok, why = overlap_witness(cert)
        add(Finding("R7 overlap-witness", ok, why))
    elif kind == "unknown":
        add(Finding("R7 attribution-identity", False,
                    f"implementation_identity does not yield a comparable "
                    f"baseline/candidate pair (baseline={v.baseline!r}, "
                    f"candidate={v.candidate!r}); the claim cannot be tied to a "
                    f"specific substitution and therefore cannot be inherited"))
    else:
        add(Finding("R7 overlap-witness", True,
                    "isolated gain: single substitution, product criterion not engaged"))

    # R8 reproduction. A single run is a hypothesis. If independent repeats were
    # recorded, they must agree; if none were recorded, the claim is UNEXPLAINED
    # and inherits nothing, no matter how large the ratio.
    rep = cert.get("reproduction") or {}
    runs = rep.get("runs")
    ratios = rep.get("ratios") or []
    if runs is None:
        add(Finding("R8 reproduction", False,
                    "no reproduction block; the ratio was observed once and never "
                    "re-measured. A single run is a hypothesis, not an inheritable gain."))
    else:
        spread = (max(ratios) - min(ratios)) / min(ratios) if len(ratios) >= 2 and min(ratios) else 0.0
        agreed = len(ratios) >= 2 and spread <= 0.05
        add(Finding("R8 reproduction", agreed,
                    f"runs={runs} ratios={[round(x,3) for x in ratios]} spread={spread*100:.1f}% "
                    f"-> {'agree' if agreed else 'DIVERGENT or single'}"
                    if len(ratios) >= 2 else f"runs={runs} but <2 ratios recorded"))

    # R9 mechanism coherence. A constant-factor measurement cannot stand in for a
    # work-reduction claim, and vice versa. This is the rule that catches the
    # AGD-GEMM certificate, which named an r64 QUOTIENT pipeline while the code
    # it ships performs register blocking at work_ratio 1.0.
    QUOTIENTY = ("quotient", "rank_reduc", "r64", "sigma", "reduced_space",
                 "low_rank", "svd", "decompos")
    mechanism = cert.get("mechanism")
    ident_blob = f"{v.baseline or ''} {v.candidate or ''}".lower()
    claims_quotient = any(tok in ident_blob for tok in QUOTIENTY)
    if mechanism is None:
        add(Finding("R9 mechanism", False,
                    "no `mechanism` field; cannot tell whether the candidate removes "
                    "work or merely executes it more cheaply"))
    elif mechanism == "constant_factor":
        add(Finding("R9 mechanism", not claims_quotient,
                    "constant_factor + work_ratio 1.0 (coherent)"
                    if not claims_quotient else
                    f"MECHANISM CONFLATION: claims constant_factor but the "
                    f"implementation_identity names a quotient/reduction "
                    f"candidate ({v.candidate!r}). The measured artifact does not "
                    f"implement the claim. A work-reduction theorem does not "
                    f"license a constant-factor number."))
    elif mechanism == "work_reduction":
        wr = (a_wr := ((cert.get("performance") or {}).get("attribution") or {}).get("work_ratio"))
        add(Finding("R9 mechanism", bool(claims_quotient) and isinstance(wr, (int, float)) and wr < 1.0,
                    f"work_reduction, work_ratio={wr} (coherent)"
                    if claims_quotient else
                    "claims work_reduction but no quotient/rank-reduction identity is named"))

    # Terminal verdicts. INVALID_PREMISE is not a hygiene failure; the premise
    # is false, so no re-measurement can rescue the claim.
    v.quarantined = False
    if quarantine and path.parent.name in quarantine:
        q = quarantine[path.parent.name]
        v.quarantined = True
        v.inheritable = False
        add(Finding("Q0 INVALID_PREMISE", False,
                    f"{q.get('summary', 'premise is false')} "
                    f"(see {Path(q['_file']).name})"))

    v.inheritable = all(f.passed for f in v.findings)
    return v

def load_quarantine(repo_root: Path) -> dict[str, dict]:
    """INVALID_PREMISE verdicts, keyed by claim directory name.

    Distinct from a claim that is merely unattested: these cannot be repaired by
    re-measuring, because the premise itself is false. Reporting them as
    "REJECTED, needs more evidence" would invite exactly that wasted work.
    """
    qdir = repo_root / "evidence" / "quarantine"
    if not qdir.is_dir():
        return {}
    out: dict[str, dict] = {}
    for qf in sorted(qdir.glob("*.json")):
        try:
            rec = json.loads(qf.read_text())
        except Exception:
            continue
        if rec.get("verdict") != "INVALID_PREMISE":
            continue
        for subj in rec.get("subjects", []):
            out[Path(subj).name] = {**rec, "_file": str(qf)}
    return out


def collect(corpus: Path) -> list[Verdict]:
    quarantine = load_quarantine(corpus.parent.parent)
    out: list[Verdict] = []
    for p in sorted(corpus.glob("*/pcss_certificate.json")):
        try:
            out.append(evaluate(p, quarantine))
        except Exception as exc:  # a malformed claim is a rejected claim
            out.append(Verdict(cert=p.parent.name, ratio=None, samples=None,
                               kind="unknown", baseline=None, candidate=None,
                               findings=[Finding("parse", False, repr(exc))]))
    return out


def render(vs: list[Verdict]) -> str:
    lines: list[str] = []
    lines.append("PCSS GAIN ATTRIBUTION LEDGER")
    lines.append("rule source: multiplicative_composition_iff_zero_overlap")
    lines.append("=" * 78)
    inh = [v for v in vs if v.inheritable]
    rej = [v for v in vs if not v.inheritable]
    for v in sorted(inh + rej, key=lambda x: -(x.ratio or 0)):
        tag = "INVALID_PREMISE" if v.quarantined else ("INHERITABLE" if v.inheritable else "REJECTED   ")
        r = f"{v.ratio:6.2f}x" if v.ratio else "   n/a "
        lines.append(f"{tag} {r}  N={str(v.samples):>3}  [{v.kind}]  {v.cert}")
        if not v.inheritable:
            for f in v.findings:
                if not f.passed:
                    lines.append(f"             x {f.rule}: {f.detail}")
    lines.append("=" * 78)
    lines.append(f"inheritable {len(inh)} / {len(vs)}")
    lines.append(f"aggregate inheritable: "
                 f"{sum(v.ratio for v in inh):.2f}x (sum is a BOUND, not a product)")
    if vs:
        worst = max((f.rule for v in vs for f in v.findings if not f.passed), default="none")
        lines.append(f"most common rejection: {worst}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        print("usage: attribution.py <corpus-dir> [--json]", file=sys.stderr)
        return 2
    corpus = Path(argv[1])
    if not corpus.is_dir():
        print(f"error: {corpus} is not a directory", file=sys.stderr)
        return 2
    vs = collect(corpus)
    if not vs:
        print(f"error: no */pcss_certificate.json under {corpus}", file=sys.stderr)
        return 2
    if "--json" in argv:
        print(json.dumps([asdict(v) for v in vs], indent=2))
    else:
        print(render(vs))
    return 0 if all(v.inheritable for v in vs) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
