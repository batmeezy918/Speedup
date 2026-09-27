# Repo architecture v2 — lead-architect cut

Date: 2026-09-26
Status: GOVERNANCE (does not publish speedup)

This is the operating model for the ChronoFold / Speedup / OIC / vault
system. It does not invent new theorems. It assigns every existing
artifact a home, a claim class, and a permission.

## Five repos, five jobs

Keep the existing GitHub orgs/accounts. Stop using one repo as kernel,
attic, press office, and product at once.

| Repo | Job | May contain | Must not contain |
|---|---|---|---|
| `batmeezy918/chronofold` | Kernel | Lean modules, theorem inventory, sorry-scan CI | speedup press, 254× ledgers, product UI |
| `batmeezy918/OIC-Core-Calculus` | Diagnostic kernel | extracted operators, boundary totality | AGD marketing, wall-clock claims |
| `batmeezy918/Speedup` | Law + gates | constitution, publisher, gap isolator, claim registry | raw Graph500 dumps, unofficial coco-equivalent winners |
| `batmeezy918/chronofold-evidence-vault` | Attic | raw runs, stdout, TEPS, Termux logs | the word VERIFIED |
| `batmeezy918/EMV` + apps | Product | runtime that *consumes* certificates | theorem counts |

`Testsuite` stays a sandbox. It is not a green kernel and not a referee.

## Connect with pins, not copies

Today Speedup copies Lean files into `verified/theorem_corpus/proofs/`.
That creates a second source of truth and silent drift.

Required connections:

1. Speedup `lean4/chronofold` → git submodule or Lake require of
   `chronofold` at a tagged commit.
2. Speedup `lean4` OIC attachments → Lake require of `OIC-Core-Calculus`
   at a tagged commit.
3. Every certificate `source_hash` → exact commit of the kernel that
   licensed the run.
4. Vault run folders → Speedup `evidence/normalized/<id>/scenario.json`
   as the only public pointer.
5. Gap isolator CI on every certificate under `evidence/` and
   `claims/REGISTRY.json`.

Forbidden connections:

- ledger row → `verified/`
- May-15 coco-equivalent score → official cocoex claim
- `lean: false` packet → directory named `verified/`
- work-ratio 16 or 1024 → published wall-clock

## What to formalize next (order)

Do not formalize more refl/symm/trans. Formalize the missing *licenses*.

1. **Claim class kernel** (`lean4/ClaimRegistry.lean`, this PR).
   Classes are data. Elevation is a function of gates, not of folder names.
2. **Certificate identity binding.** Lean proves
   `publishable cert → cert.lean = true`, not that a phone was fast.
   Bind `scenarioHash` as a parameter of the obligation, not as a
   wall-clock theorem.
3. **Section / reconstruction operators** called out as missing in
   `THM_000004` (`O_section_from_core`, SemPres, OCR).
4. **One compiled cross-repo edge:** AGD intertwiner imported by OIC
   as a parameter, not as a copied file. Until that Lake require
   exists, “independent derivation” is a split, not a proof.
5. **Negative theorems as first-class:**
   `work_ratio_is_not_runtime` already exists in spirit
   (`AGDGemmSpeedup.measured_hundredths_neq_work_ratio_times_100`).
   Keep adding *refusals*, not slogans.

Do not formalize: Graph500 TEPS, SNAP 9/24, 254× simulated, 1024×
theoretical scaling, merchant-assurance marketing.

## What to elevate, and what that word means

Elevation is a class change in `claims/REGISTRY.json` after
`publisher/gate.py` returns publishable. It is never a README edit.

| From | To | Allowed when |
|---|---|---|
| QUARANTINED | CANDIDATE | scenario.json + hashes exist |
| CANDIDATE | STRONG_LOCAL | I,R,Q,Q⁻¹,Ω,X true on a named substrate; L may be false |
| STRONG_LOCAL | VERIFIED | all seven true, including Lean binding of *identity*, not timing |
| any | NEGATIVE | a gate failed and the failure is itself published |
| THEORETICAL / SIMULATED | never VERIFIED | by construction |

This pack performs only the elevations that evidence already supports:

- SIM2XR 2026-09-08 → **STRONG_LOCAL** (explicit; folder notice added)
- QRT-EJ 20260910 → **STRONG_LOCAL**
- AGD gauntlet 6.26× → **STRONG_LOCAL** (closed-world work model)
- Official cocoex 360 → **NEGATIVE** (Q 0/360, 0.85×)
- Graph500 official BFS → **MEASURED_BASELINE** (no candidate ratio)
- 254.30× / 1024× / 209.23× → **THEORETICAL_OR_SIMULATED**
- Vault 1.021× → **CANDIDATE**
- S6/S7/S8 20260515 → remain **QUARANTINED** until cocoex rebind

Nothing in this pack is moved to VERIFIED.

## Operational function this architecture turns on

Once classes are the only public API:

- A governor may refuse an operator (T0 / admissibility). That is live.
- A scheduler may substitute `TBar^n` for `T^n` on a declared
  observable when an intertwiner is certified. That is live as math.
- A publisher may print STRONG_LOCAL numbers with substrate, seed,
  and error. That becomes live when REGISTRY is the only index.
- A publisher may not print VERIFIED. That stays dead until L binds.

## What a later human still has to do

This pack cannot:

- re-run cocoex until Q passes
- bind SIM2XR hashes into Lean
- replace Speedup file copies with Lake requires
- implement a faster Graph500 kernel
- delete historical 254× files (they stay, relabeled)

Those are the next four engineering tickets, in that order.
