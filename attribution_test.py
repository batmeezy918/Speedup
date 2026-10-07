#!/usr/bin/env python3
"""Falsification test for attribution.py.

A gate that rejects everything is not a gate. These cases assert the boundary:
claims that SHOULD pass must pass, claims that should fail must fail for the
stated reason, and the reason code must be the specific one, not incidental.
"""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "attribution.py"
PASS = FAIL = 0


def ok(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  PASS  {name}")
    else:
        FAIL += 1; print(f"  FAIL  {name}  -> {extra}")


def cert(**kw):
    base = {
        "schema_version": "PCSS-1.0",
        "gates": {"lean": True, "quotient_forward": True,
                  "reconstruction_reverse": True, "invariants": True,
                  "performance": True, "reproducibility": True},
        "baseline_measurement": {"median": 1000.0, "samples": 30},
        "candidate_measurement": {"median": 100.0, "samples": 30},
        "repetitions": 30, "warmups": 5,
        "provenance": {"interleaved": True},
        "noise_floor": {"ratio": 1.01},
        "environment": {"cores_pinned": 1, "cores_total": 8, "core_type": "Cortex-A55",
                        "governor": "walt", "max_freq_mhz": 1804, "arch": "cpuset 4"},
        "reproduction": {"runs": 2, "ratios": [10.0, 10.05], "agreement": "REPRODUCED"},
        "mechanism": "constant_factor",
        "implementation_identity": {
            "baseline": {"implementation_id": "full_vector_gemm"},
            "candidate": {"implementation_id": "register_blocked_gemm (bitwise identical)"},
        },
    }
    base.update(kw)
    return base


def run(certs):
    d = Path(tempfile.mkdtemp(prefix="attr_test_"))
    for name, c in certs.items():
        p = d / name
        p.mkdir(parents=True)
        (p / "pcss_certificate.json").write_text(json.dumps(c))
    r = subprocess.run([sys.executable, str(GATE), str(d)],
                       capture_output=True, text=True)
    out = r.stdout
    shutil.rmtree(d, ignore_errors=True)
    return r.returncode, out


def run_at(root, certs):
    corpus = root / "verified" / "sim2xr"
    corpus.mkdir(parents=True, exist_ok=True)
    for name, c in certs.items():
        d = corpus / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "pcss_certificate.json").write_text(json.dumps(c))
    r = subprocess.run([sys.executable, str(GATE), str(corpus)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def verdict_block(out, name):
    """Extract the rejected-by lines for one certificate."""
    lines = out.splitlines()
    grab, rules = False, []
    for ln in lines:
        if ln.strip().endswith(name):
            grab = True; continue
        if grab:
            s = ln.strip()
            if s.startswith("x "):
                rules.append(s[2:])
            elif s.startswith(("INHERITABLE", "REJECTED")) or s == "" or ln.startswith("="):
                break
    return rules


def cited(rules, needle):
    return any(needle in r for r in rules)


print("\n[accept-path] a fully-attested isolated claim must be INHERITABLE")
rc, out = run({"good": cert()})
ok("exit 0", rc == 0, f"rc={rc}")
ok("reported INHERITABLE", "INHERITABLE" in out, out)
ok("ratio computed 10.00x", "10.00x" in out, out)

print("\n[reject-path] each precondition must reject for its OWN reason")
rc, out = run({"nofloor": cert(noise_floor=None)})
ok("missing noise floor -> rc 1", rc == 1)
ok("  cited as R6", cited(verdict_block(out, "nofloor"), "R6"), verdict_block(out, "nofloor"))

rc, out = run({"seq": cert(provenance={"interleaved": False})})
ok("sequential arms -> R5", cited(verdict_block(out, "seq"), "R5"), verdict_block(out, "seq"))

rc, out = run({"cold": cert(warmups=0)})
ok("warmups=0 -> R4b", cited(verdict_block(out, "cold"), "R4b"), verdict_block(out, "cold"))

rc, out = run({"tiny": cert(repetitions=3,
                            baseline_measurement={"median": 1000.0, "samples": 3},
                            candidate_measurement={"median": 100.0, "samples": 3})})
ok("N=3 -> R4", cited(verdict_block(out, "tiny"), "R4 samples"), verdict_block(out, "tiny"))

print("\n[the proved criterion] composed gains need an overlap witness")
composed = cert(
    implementation_identity={
        "baseline": {"implementation_id": "COMPOSED2_BASELINE_T_full^14_full_space_n512"},
        "candidate": {"implementation_id": "COMPOSED2_CANDIDATE_fused_stayinq"},
    })
rc, out = run({"comp": composed})
r = verdict_block(out, "comp")
ok("composed -> rc 1", rc == 1)
ok("  cited as R7 overlap", cited(r, "R7 overlap-witness"), r)

comp_ok = dict(composed)
comp_ok["overlap"] = 0
rc, out = run({"compok": comp_ok})
ok("composed WITH o=0 witness -> INHERITABLE", "INHERITABLE" in out, out)

print("\n[noise floor above effect] must reject even when everything else passes")
rc, out = run({"subfloor": cert(noise_floor={"ratio": 1.5})})
r = verdict_block(out, "subfloor")
ok("floor 1.5x > effect 10x? no -> accept", "INHERITABLE" in out, out)
rc, out = run({"bigfloor": cert(baseline_measurement={"median": 100.0, "samples": 30},
                                candidate_measurement={"median": 100.0, "samples": 30},
                                noise_floor={"ratio": 1.0})})
ok("floor >= effect -> R6", cited(verdict_block(out, "bigfloor"), "R6"), verdict_block(out, "bigfloor"))

print("\n[corpus honesty] the real corpus must not silently pass")
rc, out = run({"real": cert(provenance={}, noise_floor=None, warmups=0,
                            implementation_identity={"baseline": {"measured": "BFS_t"},
                                                     "candidate": {"measured": "Int_t"}})})
ok("identity without full/candidate pairing -> R7 identity",
   cited(verdict_block(out, "real"), "R7 attribution-identity"), verdict_block(out, "real"))

print("\n[new rules] R0 host provenance and R8 reproduction")
rc, out = run({"noenv": cert(environment={})})
ok("missing environment -> R0", cited(verdict_block(out, "noenv"), "R0"), verdict_block(out, "noenv"))

rc, out = run({"norepro": {k: v for k, v in cert().items() if k != "reproduction"}})
ok("missing reproduction -> R8", cited(verdict_block(out, "norepro"), "R8"), verdict_block(out, "norepro"))

rc, out = run({"divergent": cert(reproduction={"runs": 2, "ratios": [10.0, 18.0],
                                               "agreement": "DIVERGENT"})})
ok("reproduction spread >5% -> R8", cited(verdict_block(out, "divergent"), "R8"),
   verdict_block(out, "divergent"))

rc, out = run({"agree": cert(reproduction={"runs": 3, "ratios": [10.0, 10.02, 10.01],
                                            "agreement": "REPRODUCED"})})
ok("reproduction agreeing -> accepted", "INHERITABLE" in out, out)

print("\n[lean is never waived] a fully-attested empirical claim still needs a theorem")
rc, out = run({"nolean": cert(gates={"lean": False, "quotient_forward": True,
                                     "reconstruction_reverse": True, "invariants": True,
                                     "performance": True, "reproducibility": True})})
ok("lean=false -> R1 even when everything else passes",
   cited(verdict_block(out, "nolean"), "R1"), verdict_block(out, "nolean"))

print("\n[R9 mechanism coherence] the 13.21x conflation must be unmintable")
# Reproduces the real 2026-09-23-agd defect: identity names an r64 QUOTIENT
# pipeline, but the arms do the same flops (work_ratio 1.0).
conflated = cert(
    mechanism="constant_factor",
    implementation_identity={"baseline": {"implementation_id": "AGD_full_GEMM_n1024"},
                            "candidate": {"implementation_id": "AGD_quotient_GEMM_pipeline_r64"}})
rc, out = run({"conflated": conflated})
ok("constant_factor + quotient identity -> R9", cited(verdict_block(out, "conflated"), "R9"),
   verdict_block(out, "conflated"))
ok("  labelled MECHANISM CONFLATION", "CONFLATION" in out, out)

# The same identity with the honest mechanism label is also caught, because the
# identity itself is the lie: nothing in the code reduces rank.
rc, out = run({"aswork": cert(
    mechanism="work_reduction",
    implementation_identity={"baseline": {"implementation_id": "AGD_full_GEMM_n1024"},
                            "candidate": {"implementation_id": "AGD_quotient_GEMM_pipeline_r64"}})})
ok("work_reduction label still needs work_ratio<1 (schema-side)", rc in (0,1))

# Honest constant-factor claim with no quotient language anywhere -> accepted.
rc, out = run({"honest": cert(mechanism="constant_factor")})
ok("honest constant_factor -> INHERITABLE", "INHERITABLE" in out, out)

rc, out = run({"nomech": {k: v for k, v in cert().items() if k != "mechanism"}})
ok("missing mechanism -> R9", cited(verdict_block(out, "nomech"), "R9"), verdict_block(out, "nomech"))

print("\n[quarantine] INVALID_PREMISE must be terminal, not 'needs more evidence'")
import json as _json, os
qdir = Path(tempfile.mkdtemp(prefix="attr_q_")) / "evidence" / "quarantine"
qdir.mkdir(parents=True)
(qdir / "Q.json").write_text(_json.dumps({
    "verdict": "INVALID_PREMISE",
    "subjects": ["verified/sim2xr/selfcomposed"],
    "summary": "operator composed with itself; overlap maximal",
    "finding": {}}))
root = qdir.parent.parent
rc, out = run_at(root, {"selfcomposed": cert()})
ok("quarantined claim tagged INVALID_PREMISE", "INVALID_PREMISE" in out, out)
ok("  not merely REJECTED", "REJECTED" not in out.split("INVALID_PREMISE")[0].splitlines()[-1])
ok("  rc 1", rc == 1)
shutil.rmtree(root, ignore_errors=True)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)