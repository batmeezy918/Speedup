#!/usr/bin/env python3
"""AGD recursive formal-gap ledger.

This is the engine that turns the formal gap derivation (lean4/AGDGapDerivation.lean:
admissibility is SUFFICIENT and its failure is NECESSARY -> a real gap) into an
operational, recursive process over MUNI:

  1. Enumerate the obligations the "exact + faster" claim depends on.
  2. Probe each with a CONCRETE test that produces evidence.
  3. Closing an obligation may REVEAL successors (e.g. closing "native path
     agreement" reveals "C-vs-model binding"). Enqueue and recurse.
  4. Iterate until a fixed point: every obligation is CLOSED, or is a named
     RESIDUAL with a stated next discriminating test.
  5. For every obligation still OPEN, emit a concrete MUNI hardening.

The point (per the brief) is NOT to re-test the adversarial suite, but to use
the derivation to STRENGTHEN MUNI: gaps found here become guards/tests there.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "bin")
REC = os.path.join(HERE, "receipts")
LEAN_DIR = "/root/Speedup/lean4"
os.environ["LEAN_PATH"] = LEAN_DIR + os.pathsep + os.environ.get("LEAN_PATH", "")


def run(cmd, timeout=900):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:  # noqa
        return -1, f"probe error: {e}"


def parse(out, key, cast=float):
    m = re.search(rf"{key}=([-\w.]+)", out)
    return cast(m.group(1)) if m else None


# ---------------------------------------------------------------- probes ----

def probe_lean_axioms():
    """Build the refinement + gap files and capture axiom footprints."""
    log = []
    ok = True
    for f in ("AGDRefinement", "AGDGapDerivation"):
        src = os.path.join(LEAN_DIR, f + ".lean")
        if not os.path.exists(src):
            return False, f"{f}.lean missing"
        rc, out = run(["lean", "--root=" + LEAN_DIR, "-o",
                       os.path.join(LEAN_DIR, f + ".olean"), src],
                      timeout=600)
        log.append(out.strip())
        if rc != 0 or "sorryAx" in out or "error" in out.lower():
            ok = False
    with open(os.path.join(REC, "lean_refinement.log"), "w") as fh:
        fh.write("\n".join(log) + "\n")
    return ok, "; ".join(l for l in log if "axioms" in l)


def probe_admissibility_soundness():
    rc, out = run([os.path.join(BIN, "agd_fuzz"), "5000"], timeout=600)
    return rc == 0 and "FUZZ_RESULT=PASS" in out, out.strip().splitlines()[-3:]


def probe_cert_failclosed():
    rc, out = run([os.path.join(BIN, "agd_fuzz"), "5000"], timeout=600)
    return (rc == 0 and "FUZZ_RESULT=PASS" in out and "tampered=" in out), \
        [l for l in out.splitlines() if "FUZZ cases" in l]


def probe_native_selftest():
    rc, out = run([os.path.join(BIN, "agd_elev"), "selftest"], timeout=120)
    return (rc == 0 and "REFINE_SELFTEST=PASS" in out), out.strip()


def probe_exactness():
    rc, out = run([os.path.join(BIN, "agd_elev"), "heat", "2048", "64", "32",
                   "3", "2", os.path.join(REC, "heat_probe.json")], timeout=600)
    err = parse(out, "max_abs_error_quotient")
    return (rc == 0 and err == 0.0), f"heat max_abs_error={err}"


def probe_honest_baseline():
    rc, out = run([os.path.join(BIN, "agd_elev"), "bench", "2048", "64", "32",
                   "3", "2", os.path.join(REC, "bench_probe.json")], timeout=600)
    derr = parse(out, "dense_abs_error")
    dx = parse(out, "speedup_vs_dense")
    return (rc == 0 and derr == 0.0 and dx and dx > 1), f"dense_abs_error={derr} speedup_vs_dense={dx}"


def probe_noise_floor():
    sf = os.path.join(REC, "session_stats.json")
    if not os.path.exists(sf):
        return False, "session_stats.json missing (run run_sessions.sh)"
    with open(sf) as fh:
        d = json.load(fh)
    nf = d.get("noise_floor_aa") or {}
    return (nf.get("n", 0) >= 5), f"A/A n={nf.get('n')} median={nf.get('median')} max={nf.get('max')}"


def probe_tol_accumulation():
    """Is a nonzero tolerance safe over many steps? Measure accumulation."""
    rc, out = run([os.path.join(BIN, "agd_fuzz"), "20000"], timeout=900)
    ratio = parse(out, "ratio")
    max_err = parse(out, "max_err", float)
    max_tol = parse(out, "max_tol", float)
    safe = (ratio is not None and ratio <= 1.0)
    return safe, f"max_tol={max_tol} max_err={max_err} err/tol={ratio}"


def probe_tol_claim_guard():
    """MUNI hardening check: does the tool distinguish EXACT (tol=0) from
    APPROX (tol>0), so it can never overstate a tolerance-gated result?"""
    rc, out = run([os.path.join(BIN, "agd_elev"), "selftest"], timeout=120)
    ok = ("CLAIM_TOL0=EXACT_BITWISE" in out and "CLAIM_TOLPOS=APPROX_UNBOUNDED" in out)
    return ok, "guard present" if ok else out.strip()


# ------------------------------------------------------------- obligations --

OBLIGATIONS = [
    dict(id="O1", name="operator is the certified tensor-separable U(x)I_m",
         probe=None, assumed=True,
         note="ASSUMED BY DESIGN: the chosen invariant. Auto-discovery is explicitly out of scope."),
    dict(id="O2", name="admissibility gate is sound (admitted => exact at tol=0)",
         probe="admissibility_soundness",
         hardening="keep gate; add the tol=0 exhaustiveness is already enforced"),
    dict(id="O2b", name="nonzero tolerance bounds error over many steps",
         probe="tol_accumulation",
         hardening="certificate must distinguish EXACT (tol=0) from APPROX (tol>0); "
                   "refuse to call tol>0 results 'bit-exact'; document error-growth bound or require contraction"),
    dict(id="O2b_guard", name="MUNI refuses to label tol>0 as exact (hardening)",
         probe="tol_claim_guard"),
    dict(id="O3", name="certificate fails closed on tamper / unknown state",
         probe="cert_failclosed"),
    dict(id="O4a", name="refinement at model/operation-order level (Lean)",
         probe="lean_axioms", reveals=["O4b"]),
    dict(id="O4b", name="native binary path agreement (runtime witness)",
         probe="native_selftest", reveals=["O4c"]),
    dict(id="O4c", name="C binary == Lean float model (kernel-level binding)",
         probe=None, residual=True,
         note="RESIDUAL: cannot be closed by testing. Needs a verified-float / "
              "compiler-refinement proof (CompCert, Frama-C, or a proved IEEE model).",
         hardening="add certificate field binding_scope=\"matvec-order-pinned\" and "
                   "refuse native claim until a refinement artifact is attached"),
    dict(id="O5", name="exact reconstruction on the block-constant sector",
         probe="exactness"),
    dict(id="O6", name="baseline is a genuinely general dense operator",
         probe="honest_baseline"),
    dict(id="O7", name="timing claims exceed a measured A/A noise floor",
         probe="noise_floor"),
]

PROBES = {
    "admissibility_soundness": probe_admissibility_soundness,
    "cert_failclosed": probe_cert_failclosed,
    "lean_axioms": probe_lean_axioms,
    "native_selftest": probe_native_selftest,
    "exactness": probe_exactness,
    "honest_baseline": probe_honest_baseline,
    "noise_floor": probe_noise_floor,
    "tol_accumulation": probe_tol_accumulation,
    "tol_claim_guard": probe_tol_claim_guard,
}


def main():
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    queue = list(OBLIGATIONS)
    status = {}
    trace = []
    seen = set()
    it = 0
    while queue and it < depth * len(OBLIGATIONS) + 20:
        it += 1
        ob = queue.pop(0)
        if ob["id"] in status:
            continue
        seen.add(ob["id"])
        if ob.get("assumed"):
            status[ob["id"]] = dict(state="ASSUMED", evidence=ob.get("note", ""))
            trace.append(f"[{it}] {ob['id']} {ob['name']} -> ASSUMED")
            continue
        if ob.get("residual") and ob["probe"] is None:
            status[ob["id"]] = dict(state="RESIDUAL", evidence=ob.get("note", ""),
                                    next_test="attach a compiler/float refinement proof",
                                    hardening=ob.get("hardening", ""))
            trace.append(f"[{it}] {ob['id']} {ob['name']} -> RESIDUAL")
            for r in ob.get("reveals", []):
                pass
            continue
        fn = PROBES.get(ob["probe"])
        if fn is None:
            status[ob["id"]] = dict(state="UNKNOWN", evidence="no probe")
            continue
        ok, ev = fn()
        state = "CLOSED" if ok else "OPEN"
        status[ob["id"]] = dict(state=state, evidence=str(ev))
        trace.append(f"[{it}] {ob['id']} {ob['name']} -> {state} ({ev})")
        # RECURSION: closing may reveal successors; opening reveals the test that failed.
        if ok:
            for rid in ob.get("reveals", []):
                if rid not in status:
                    for cand in OBLIGATIONS:
                        if cand["id"] == rid:
                            queue.append(cand)
        else:
            status[ob["id"]]["next_test"] = "re-run this probe after a fix; keep open until evidence passes"
            status[ob["id"]]["hardening"] = ob.get("hardening", "")

    ledger = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "depth": depth, "iterations": it,
        "obligations": status,
        "n_closed": sum(1 for v in status.values() if v["state"] == "CLOSED"),
        "n_open": sum(1 for v in status.values() if v["state"] == "OPEN"),
        "n_residual": sum(1 for v in status.values() if v["state"] == "RESIDUAL"),
        "n_assumed": sum(1 for v in status.values() if v["state"] == "ASSUMED"),
        "trace": trace,
    }
    with open(os.path.join(REC, "gap_ledger.json"), "w") as fh:
        json.dump(ledger, fh, indent=2)
    with open(os.path.join(REC, "gap_ledger_trace.txt"), "w") as fh:
        fh.write("\n".join(trace) + "\n")

    print(json.dumps(ledger, indent=2))
    print("\n=== GAP LEDGER TRACE ===")
    print("\n".join(trace))
    print(f"\nclosed={ledger['n_closed']} open={ledger['n_open']} "
          f"residual={ledger['n_residual']} assumed={ledger['n_assumed']}")
    # A residual is acceptable; an OPEN obligation is a live gap.
    return 0


if __name__ == "__main__":
    sys.exit(main())
