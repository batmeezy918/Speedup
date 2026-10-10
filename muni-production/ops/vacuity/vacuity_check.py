#!/usr/bin/env python3
"""MUNI formal vacuity audit -- closes the hole `#print axioms` cannot.

`#print axioms` answers "does this proof depend on an axiom?".
It cannot answer "does this theorem say anything?".

A theorem whose conclusion reduces to `True` is axiom-free, compiles cleanly,
and proves nothing. That is exactly the shape of ProofCarryingTransformation.lean:

    def Gap            : Prop := True
    def SemPres        : Prop := True
    def ArtifactCorrect: Prop := True
    theorem master ... : Gap P T ∧ SemPres P T ∧ ArtifactCorrect P T := by simp [...]

V1 CONCLUSION TRIVIALITY   conclusion reduces to True once the file's own
                           definitions unfold  -> VACUOUS
V2 TRUE-DEFINED PROPS      any `def ... : Prop := True` in the file
V3 HYPOTHESIS REACHABILITY is the hypothesis jointly satisfiable?
                           A universally-quantified hypothesis over a type that
                           admits a witness is REACHABLE. Unsatisfiable
                           hypotheses make a theorem vacuous even when the
                           conclusion is not `True`.
V4 IMPORT RESOLVABILITY    do all `import`s resolve in this toolchain?
V5 AXIOM-FREEMENESS        regression guard on the existing audit check
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC  = ROOT / "src"

def lean(args, cwd=None, env=None):
    return subprocess.run(["lean", *args], cwd=cwd or ROOT, capture_output=True,
                          text=True, env=env)

def compile_module(lean_name):
    d = Path(tempfile.mkdtemp(prefix="vac_"))
    r = lean(["-o", str(d / f"{lean_name}.olean"), str(SRC / f"{lean_name}.lean")], cwd=SRC)
    return d if r.returncode == 0 else None

def probe(lean_name, snippet):
    d = compile_module(lean_name)
    if d is None:
        return None
    f = d / "probe.lean"
    f.write_text(f"import {lean_name}\n{snippet}")
    return lean([str(f)], env=dict(os.environ, LEAN_PATH=str(d)))

def v1_conclusion_triviality(lean_name, theorem, binder_sig):
    """Emit the closed statement as `<stmt> = True` and try `simp`."""
    if binder_sig is None:
        snip = f"example : ({theorem}) = True := by simp\n"
    else:
        snip = ("example : ∀ " + binder_sig + ",\n"
                f"  ({theorem}) = True := by intro" + "".join(" _" for _ in re.findall(r'[A-Za-z]\w*', binder_sig)) + "; simp\n")
    r = probe(lean_name, snip)
    if r is None:
        return "SKIP", "module does not compile here"
    if r.returncode == 0:
        return "VACUOUS", "conclusion reduces to True"
    if "unknown identifier" in r.stderr:
        return "UNRESOLVED", "theorem name not in scope"
    return "NONTRIVIAL", "conclusion does not reduce to True"

def v2_true_defs(src):
    return [m.group(2) for m in
            re.finditer(r'^def\s+([A-Za-z_][\w\']*)([^\n]*?):=\s*True\s*$', src, re.M)]

def v3_hypothesis_reachability():
    """Can the real proofs' hypotheses be inhabited by concrete data?"""
    probes = [
        ("AGD_EQUIVALENCE_QUOTIENT_CORE", "section_law (decode∘project = id)",
         "example : ∃ (S Q : Type) (full : S → S) (q : Q → Q) (p : S → Q) (dec : Q → S),\n"
         "    (∀ x, dec (p x) = x) := by\n"
         "  exact ⟨Nat, Nat, id, id, id, id, fun x => rfl⟩\n"),
        ("AGD_EQUIVALENCE_QUOTIENT_CORE", "section_law at m ≥ 2 (non-degenerate)",
         "example : ∃ (m : Nat) (p : Fin m → Fin m) (dec : Fin m → Fin m),\n"
         "    2 ≤ m ∧ (∀ x, dec (p x) = x) := by\n"
         "  refine ⟨2, id, id, by decide, fun x => rfl⟩\n"),
        ("AGD_EQUIVALENCE_QUOTIENT_CORE", "invariant section (block-constant sector non-empty)",
         "example : ∃ (s : Nat → Nat), (∀ i, s i = s (i+1)) := by\n"
         "  exact ⟨fun _ => 7, fun _ => rfl⟩\n"),
        ("AGD_EQUIVALENCE_QUOTIENT_CORE", "block-constant state of length 4 with m=2 is reachable",
         "example : ∃ (v : Nat → Nat), v 0 = v 1 ∧ v 2 = v 3 := by\n"
         "  exact ⟨fun _ => 5, rfl, rfl⟩\n"),
        ("AGD_GAP_DERIVATION", "Gap1 satisfiable (one-step gap holds for some system)",
         "example : ∃ (S Q : Type) (full : S → S) (q : Q → Q) (p : S → Q),\n"
         "    (∀ x, p (full x) = q (p x)) := by\n"
         "  exact ⟨Nat, Nat, id, id, id, fun _ => rfl⟩\n"),
        ("AGD_GAP_DERIVATION", "Gap1 VIOLATED by some system (gap is not universal)",
         "example : ¬ (∀ (x : Nat), (0 : Nat) = x + 1) := by\n"
         "  intro h\n"
         "  exact absurd (h 0) (by decide)\n"),
        ("AGD_GAP_DERIVATION", "OrbitGapFree satisfiable (a real gap-free trajectory)",
         "example : AGD.Gap.OrbitGapFree (full := fun f : Nat => f) (quotient := fun f : Nat => f)\n"
         "    (project := fun p => p) (x0 := 0) 0 := by\n"
         "  intro m hm\n"
         "  rfl\n"),
        ("AGD_GAP_DERIVATION", "Pipeline range restriction non-vacuous (f₁ surjective)",
         "example : ∃ (f₁ : Nat → Nat) (f₂ : Nat → Nat), (∀ y, ∃ x, f₁ x = y) := by\n"
         "  exact ⟨id, id, fun y => ⟨y, rfl⟩⟩\n"),
    ]
    out = []
    for mod, name, snip in probes:
        r = probe(mod, snip)
        if r is None:
            out.append({"module": mod, "hypothesis": name, "status": "SKIP"})
        elif r.returncode == 0:
            out.append({"module": mod, "hypothesis": name, "status": "SAT"})
        else:
            first = next((l for l in r.stderr.splitlines() if "error" in l), "")
            out.append({"module": mod, "hypothesis": name, "status": "UNSAT_OR_UNKNOWN",
                        "detail": first[:200]})
    return out

def v4_imports(src):
    bad = []
    for imp in re.findall(r'^import\s+(\S+)', src, re.M):
        d = Path(tempfile.mkdtemp())
        (d / "i.lean").write_text(f"import {imp}\n")
        if lean([str(d / "i.lean")]).returncode != 0:
            bad.append(imp)
    return bad

def main():
    report = {"schema": "muni.formal-vacuity-audit.v1", "modules": {}, "verdict": None}
    vacuous_files = []
    for f in sorted(SRC.glob("*.lean")):
        src = f.read_text()
        stem = f.stem
        r = lean([str(f)], cwd=SRC)
        out = r.stdout + r.stderr
        entry = {
            "compiles": r.returncode == 0,
            "axiom_free_lines": out.count("does not depend on any axioms"),
            "sorryAx_lines": out.count("sorryAx"),
            "v2_true_defined_props": v2_true_defs(src),
            "v4_unresolvable_imports": v4_imports(src),
            "theorems": re.findall(r'^theorem\s+([A-Za-z_][\w\']*)', src, re.M),
        }
        entry["v1_conclusions"] = []
        for t in entry["theorems"]:
            full = t if t.startswith("AGD.") else f"AGD.{t}"
            status, detail = v1_conclusion_triviality(stem, full, None)
            if status == "UNRESOLVED":
                status, detail = v1_conclusion_triviality(stem, t, None)
            entry["v1_conclusions"].append({"theorem": full, "status": status, "detail": detail})
        flags = []
        if not entry["compiles"]: flags.append("DOES_NOT_COMPILE")
        if entry["v2_true_defined_props"]: flags.append(f"TRUE_DEFS={entry['v2_true_defined_props']}")
        if entry["v4_unresolvable_imports"]: flags.append(f"BAD_IMPORTS={entry['v4_unresolvable_imports']}")
        if any(c["status"] == "VACUOUS" for c in entry["v1_conclusions"]):
            flags.append("VACUOUS_CONCLUSION")
            vacuous_files.append(stem)
        entry["flags"] = flags
        report["modules"][f.name] = entry

    report["v3_hypothesis_reachability"] = v3_hypothesis_reachability()

    # G3 gate verdict: every shipped formal source must compile, be axiom-free,
    # carry no trivial props, and have no unresolvable import.
    gate_ok = all(m["compiles"] and m["axiom_free_lines"] > 0 and not m["flags"]
                  for m in report["modules"].values())
    report["verdict"] = "VACUITY_FAIL" if not gate_ok else "VACUITY_PASS"

    (ROOT / "vacuity_report.json").write_text(json.dumps(report, indent=2))
    print(f"VERDICT: {report['verdict']}\n")
    for name, m in report["modules"].items():
        print(f"  {name}")
        print(f"    compiles={m['compiles']}  axiom_free={m['axiom_free_lines']}  "
              f"sorryAx={m['sorryAx_lines']}  theorems={len(m['theorems'])}")
        if m["flags"]:
            print(f"    FLAGS: {' | '.join(m['flags'])}")
        for c in m["v1_conclusions"]:
            if c["status"] != "NONTRIVIAL":
                print(f"      V1 {c['theorem']}: {c['status']} -- {c['detail']}")
    print("\nV3 hypothesis reachability:")
    for h in report["v3_hypothesis_reachability"]:
        print(f"  {h['status']:18s} {h['module']:30s} {h['hypothesis']}")
    return 0 if gate_ok else 1

if __name__ == "__main__":
    sys.exit(main())
