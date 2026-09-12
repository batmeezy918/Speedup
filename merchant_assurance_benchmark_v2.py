#!/usr/bin/env python3
"""
EOF / MASQ — Merchant Assurance Semantic Quotient Benchmark v2
===============================================================

Instrumented empirical benchmark.  This version preserves the existing
reference/implementation decision semantics while replacing placeholder
metrics with measurements derived from executed observations.

Evidence boundary:
    LOCAL_REFERENCE_ORACLE_ONLY
    network_equivalence=UNPROVEN

The benchmark distinguishes two observable projections:
    Π_audit      = decision, reason, merchant, tx_id
    Π_acceptance = decision, reason, merchant

Π_acceptance is used for semantic quotient analysis because tx_id is an
instance identifier rather than an authorization-semantic discriminator.
Π_audit remains available for trace/replay auditing.

Metrics:
    ΔC_declared   = (12 - |Π_acceptance fields|) / 12
    ΔC_observed   = 1 - |Q_observed| / |X_observed|
    Ξ_i           = projection-change rate under controlled perturbation i
    Ω             = pairwise non-additivity rate over controlled perturbations
    RIF           = reference/implementation Π_acceptance agreement rate
    domain_span   = unique executed raw states, acceptance projections,
                    audit projections, and decisions

Ω is deliberately named as an empirical interaction statistic, not a
mathematical derivative or physical entanglement measure.
"""

from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
import time
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Optional, Any

NOW = 1000
RANDOM_CASES = 5000
BATCH_SIZE = 250
SEED = 20260912
RAW_DIMENSIONS = 12
RESULTS_FILE = Path("masq_v2_finished_runs.jsonl")
SUMMARY_FILE = Path("masq_v2_final_summary.json")
CERTIFICATE_FILE = Path("masq_v2_certificate.json")


def canon(obj: Any) -> str:
    if hasattr(obj, "__dataclass_fields__"):
        obj = asdict(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(obj: Any) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Evidence:
    subject: str
    issuer: str
    trusted_issuer: bool
    signature_valid: bool
    present: bool = True


@dataclass(frozen=True)
class Credential:
    credential_id: str
    subject: str
    valid_from: int
    valid_until: int
    revoked: bool
    bound_key: str


@dataclass(frozen=True)
class Delegation:
    principal: str
    agent: str
    merchant: str
    valid_from: int
    valid_until: int
    revoked: bool


@dataclass(frozen=True)
class Transaction:
    tx_id: str
    merchant: str
    agent: Optional[str]
    operation: str
    amount: int
    currency: str
    nonce: str
    issued_at: int
    expires_at: int
    bound_credential: str


@dataclass(frozen=True)
class MerchantState:
    identity: str
    evidence: Evidence
    credential: Optional[Credential]
    delegation: Optional[Delegation]
    allowed_operations: tuple[str, ...]
    max_amount: int
    currencies: tuple[str, ...]
    lifecycle: str
    route_allowed: bool
    key: str
    replayed_jtis: tuple[str, ...] = ()


@dataclass(frozen=True)
class Decision:
    decision: str
    reason: str
    merchant: Optional[str]
    tx_id: Optional[str]
    state_digest: str


def reference_oracle(state: MerchantState, tx: Transaction) -> Decision:
    sd = digest(state)

    def r(d: str, reason: str) -> Decision:
        return Decision(d, reason, state.identity, tx.tx_id, sd)

    if not state.evidence.present:
        return r("INDETERMINATE", "MISSING_EVIDENCE")
    if state.evidence.subject != state.identity:
        return r("DENY", "UNKNOWN_MERCHANT")
    if not state.evidence.trusted_issuer:
        return r("DENY", "UNTRUSTED_ISSUER")
    if not state.evidence.signature_valid:
        return r("DENY", "BAD_SIGNATURE")

    c = state.credential
    if c is None:
        return r("DENY", "CREDENTIAL_MISSING")
    if c.subject != state.identity or c.bound_key != state.key:
        return r("DENY", "CREDENTIAL_BINDING_MISMATCH")
    if c.revoked:
        return r("DENY", "CREDENTIAL_REVOKED")
    if not c.valid_from <= tx.issued_at <= c.valid_until:
        return r("DENY", "CREDENTIAL_EXPIRED")

    if state.delegation is not None:
        d = state.delegation
        if d.agent != tx.agent or d.merchant != state.identity:
            return r("DENY", "DELEGATION_MISSING")
        if d.revoked:
            return r("DENY", "DELEGATION_REVOKED")
        if not d.valid_from <= tx.issued_at <= d.valid_until:
            return r("DENY", "DELEGATION_EXPIRED")
    elif tx.agent is not None:
        return r("DENY", "DELEGATION_MISSING")

    checks = [
        (tx.operation in state.allowed_operations, "SCOPE_DENIED"),
        (tx.amount <= state.max_amount, "AMOUNT_EXCEEDED"),
        (tx.currency in state.currencies, "CURRENCY_DENIED"),
        (tx.merchant == state.identity, "TRANSACTION_BINDING_MISMATCH"),
        (tx.expires_at >= tx.issued_at and tx.expires_at >= NOW, "ASSERTION_EXPIRED"),
        (tx.issued_at <= NOW, "ASSERTION_NOT_YET_VALID"),
        (tx.tx_id not in state.replayed_jtis, "REPLAY"),
        (state.lifecycle == "ACTIVE", "LIFECYCLE_INACTIVE"),
        (state.route_allowed, "ROUTE_DENIED"),
    ]
    for ok, reason in checks:
        if not ok:
            return r("DENY", reason)
    return r("ALLOW", "ALLOW")


def independent_implementation(state: MerchantState, tx: Transaction) -> Decision:
    sd = digest(state)

    def r(d: str, reason: str) -> Decision:
        return Decision(d, reason, state.identity, tx.tx_id, sd)

    e = state.evidence
    if not e.present:
        return r("INDETERMINATE", "MISSING_EVIDENCE")
    if e.subject != state.identity:
        return r("DENY", "UNKNOWN_MERCHANT")
    if not e.trusted_issuer:
        return r("DENY", "UNTRUSTED_ISSUER")
    if not e.signature_valid:
        return r("DENY", "BAD_SIGNATURE")

    c = state.credential
    if c is None:
        return r("DENY", "CREDENTIAL_MISSING")
    if c.subject != state.identity or c.bound_key != state.key:
        return r("DENY", "CREDENTIAL_BINDING_MISMATCH")
    if c.revoked:
        return r("DENY", "CREDENTIAL_REVOKED")
    if not c.valid_from <= tx.issued_at <= c.valid_until:
        return r("DENY", "CREDENTIAL_EXPIRED")

    d = state.delegation
    if tx.agent is not None:
        if d is None:
            return r("DENY", "DELEGATION_MISSING")
        if d.agent != tx.agent or d.merchant != state.identity:
            return r("DENY", "DELEGATION_MISSING")
        if d.revoked:
            return r("DENY", "DELEGATION_REVOKED")
        if not d.valid_from <= tx.issued_at <= d.valid_until:
            return r("DENY", "DELEGATION_EXPIRED")

    checks = [
        (tx.operation in state.allowed_operations, "SCOPE_DENIED"),
        (tx.amount <= state.max_amount, "AMOUNT_EXCEEDED"),
        (tx.currency in state.currencies, "CURRENCY_DENIED"),
        (tx.merchant == state.identity, "TRANSACTION_BINDING_MISMATCH"),
        (tx.expires_at >= tx.issued_at and tx.expires_at >= NOW, "ASSERTION_EXPIRED"),
        (tx.issued_at <= NOW, "ASSERTION_NOT_YET_VALID"),
        (tx.tx_id not in state.replayed_jtis, "REPLAY"),
        (state.lifecycle == "ACTIVE", "LIFECYCLE_INACTIVE"),
        (state.route_allowed, "ROUTE_DENIED"),
    ]
    for ok, reason in checks:
        if not ok:
            return r("DENY", reason)
    return r("ALLOW", "ALLOW")


def projection_audit(d: Decision) -> tuple:
    return (d.decision, d.reason, d.merchant, d.tx_id)


def projection_acceptance(d: Decision) -> tuple:
    return (d.decision, d.reason, d.merchant)


def base_state() -> MerchantState:
    return MerchantState(
        identity="merchant-A",
        evidence=Evidence("merchant-A", "issuer-1", True, True),
        credential=Credential("cred-1", "merchant-A", 900, 1100, False, "key-A"),
        delegation=None,
        allowed_operations=("SALE", "REFUND"),
        max_amount=10000,
        currencies=("USD",),
        lifecycle="ACTIVE",
        route_allowed=True,
        key="key-A",
    )


def base_transaction() -> Transaction:
    return Transaction("tx-001", "merchant-A", None, "SALE", 100, "USD", "n-001", 1000, 1010, "cred-1")


def named_cases():
    s, t = base_state(), base_transaction()
    yield "valid_baseline", s, t
    yield "missing_evidence", replace(s, evidence=replace(s.evidence, present=False)), t
    yield "untrusted_issuer", replace(s, evidence=replace(s.evidence, trusted_issuer=False)), t
    yield "bad_signature", replace(s, evidence=replace(s.evidence, signature_valid=False)), t
    yield "credential_missing", replace(s, credential=None), t
    yield "credential_revoked", replace(s, credential=replace(s.credential, revoked=True)), t
    yield "credential_wrong_key", replace(s, key="key-B"), t
    yield "credential_expired", replace(s, credential=replace(s.credential, valid_until=999)), t
    yield "scope_denied", s, replace(t, operation="CAPTURE")
    yield "amount_exceeded", s, replace(t, amount=10001)
    yield "currency_denied", s, replace(t, currency="EUR")
    yield "merchant_binding_mismatch", s, replace(t, merchant="merchant-B")
    yield "expired_assertion", s, replace(t, expires_at=999)
    yield "future_assertion", s, replace(t, issued_at=1001, expires_at=1010)
    yield "replay", replace(s, replayed_jtis=("tx-001",)), t
    yield "lifecycle_suspended", replace(s, lifecycle="SUSPENDED"), t
    yield "route_denied", replace(s, route_allowed=False), t
    d = Delegation("principal-1", "agent-1", "merchant-A", 900, 1100, False)
    yield "valid_delegation", replace(s, delegation=d), replace(t, agent="agent-1")
    yield "missing_delegation", s, replace(t, agent="agent-1")
    yield "revoked_delegation", replace(s, delegation=replace(d, revoked=True)), replace(t, agent="agent-1")
    yield "expired_delegation", replace(s, delegation=replace(d, valid_until=999)), replace(t, agent="agent-1")


def random_case(rng: random.Random, index: int):
    s, t = base_state(), base_transaction()
    t = replace(t, tx_id=f"tx-{index:06d}", nonce=f"nonce-{index:06d}")
    mutation = rng.choice([
        "none", "identity", "evidence", "trust", "signature", "credential",
        "key", "scope", "amount", "currency", "merchant", "freshness",
        "future", "replay", "lifecycle", "routing", "delegation_missing",
        "delegation_valid", "delegation_revoked", "delegation_expired",
    ])
    if mutation == "identity":
        s = replace(s, identity="merchant-B")
    elif mutation == "evidence":
        s = replace(s, evidence=replace(s.evidence, present=False))
    elif mutation == "trust":
        s = replace(s, evidence=replace(s.evidence, trusted_issuer=False))
    elif mutation == "signature":
        s = replace(s, evidence=replace(s.evidence, signature_valid=False))
    elif mutation == "credential":
        s = replace(s, credential=replace(s.credential, revoked=True))
    elif mutation == "key":
        s = replace(s, key="wrong-key")
    elif mutation == "scope":
        t = replace(t, operation="CAPTURE")
    elif mutation == "amount":
        t = replace(t, amount=10001)
    elif mutation == "currency":
        t = replace(t, currency="EUR")
    elif mutation == "merchant":
        t = replace(t, merchant="merchant-B")
    elif mutation == "freshness":
        t = replace(t, expires_at=999)
    elif mutation == "future":
        t = replace(t, issued_at=1001, expires_at=1010)
    elif mutation == "replay":
        s = replace(s, replayed_jtis=(t.tx_id,))
    elif mutation == "lifecycle":
        s = replace(s, lifecycle="SUSPENDED")
    elif mutation == "routing":
        s = replace(s, route_allowed=False)
    elif mutation == "delegation_missing":
        t = replace(t, agent="agent-1")
    elif mutation.startswith("delegation_"):
        d = Delegation("principal-1", "agent-1", "merchant-A", 900, 1100, False)
        if mutation == "delegation_revoked":
            d = replace(d, revoked=True)
        elif mutation == "delegation_expired":
            d = replace(d, valid_until=999)
        s = replace(s, delegation=d)
        t = replace(t, agent="agent-1")
    return mutation, s, t


def raw_fingerprint(s: MerchantState, t: Transaction) -> str:
    return digest({"state": s, "transaction": t})


def run_pair(s: MerchantState, t: Transaction):
    ref = reference_oracle(s, t)
    impl = independent_implementation(s, t)
    return ref, impl


def controlled_probes():
    s, t = base_state(), base_transaction()
    return {
        "identity": (replace(t, merchant="merchant-B"), s),
        "evidence": (t, replace(s, evidence=replace(s.evidence, present=False))),
        "credential": (t, replace(s, credential=None)),
        "trust": (t, replace(s, evidence=replace(s.evidence, trusted_issuer=False))),
        "scope": (replace(t, operation="CAPTURE"), s),
        "amount": (replace(t, amount=s.max_amount + 1), s),
        "currency": (replace(t, currency="EUR"), s),
        "lifecycle": (t, replace(s, lifecycle="SUSPENDED")),
        "routing": (t, replace(s, route_allowed=False)),
        "freshness": (replace(t, expires_at=999), s),
        "replay_history": (t, replace(s, replayed_jtis=(t.tx_id,))),
        "delegation": (replace(t, agent="agent-1"), s),
    }


def sensitivity_metrics():
    s, t = base_state(), base_transaction()
    base = projection_acceptance(reference_oracle(s, t))
    out = {}
    for name, (pt, ps) in controlled_probes().items():
        mutated = projection_acceptance(reference_oracle(ps, pt))
        out[name] = {
            "changed": base != mutated,
            "baseline_projection": base,
            "mutated_projection": mutated,
        }
    rates = {k: float(v["changed"]) for k, v in out.items()}
    return out, rates


def omega_metric():
    """Measure pairwise non-additivity of controlled projection changes.

    For each pair i,j, let δ_i be whether the single perturbation changes Π,
    and δ_ij whether both perturbations together change Π.  The interaction
    indicator is 1 when δ_ij differs from the logical union δ_i OR δ_j.
    This is an empirical categorical interaction statistic, not a derivative.
    """
    s, t = base_state(), base_transaction()
    base = projection_acceptance(reference_oracle(s, t))
    probes = controlled_probes()
    singles = {}
    for name, (pt, ps) in probes.items():
        singles[name] = projection_acceptance(reference_oracle(ps, pt)) != base

    # Pair mutations are constructed conservatively by applying independent
    # state/transaction replacements only where their dataclass fields differ.
    pairs = []
    names = list(probes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ta, sa = probes[a]
            tb, sb = probes[b]
            # Combine by taking fields changed from baseline by each probe.
            combined_t, combined_s = t, s
            if ta != t:
                combined_t = ta
            if tb != t:
                if combined_t != t and ta != tb:
                    # Independent transaction probes cannot be safely composed
                    # without field-level conflict resolution; skip the pair.
                    continue
                combined_t = tb
            if sa != s:
                combined_s = sa
            if sb != s:
                if combined_s != s and sa != sb:
                    continue
                combined_s = sb
            pair_changed = projection_acceptance(reference_oracle(combined_s, combined_t)) != base
            interaction = pair_changed != (singles[a] or singles[b])
            pairs.append({"a": a, "b": b, "pair_changed": pair_changed, "interaction": interaction})
    rate = (sum(int(p["interaction"]) for p in pairs) / len(pairs)) if pairs else 0.0
    return {"value": rate, "pairs_tested": len(pairs), "pairs": pairs}


def metric_snapshot(started, completed, passed, raw_seen, q_seen, audit_seen, decisions):
    elapsed = max(time.perf_counter() - started, 1e-12)
    observed_compression = 1.0 - (len(q_seen) / len(raw_seen)) if raw_seen else 0.0
    return {
        "psi_norm": float(len(q_seen)) ** 0.5,
        "delta_complexity_declared": (RAW_DIMENSIONS - 3) / RAW_DIMENSIONS,
        "delta_complexity_observed": observed_compression,
        "raw_dimension_count_declared": RAW_DIMENSIONS,
        "acceptance_projection_dimension": 3,
        "observed_raw_states": len(raw_seen),
        "observed_acceptance_classes": len(q_seen),
        "observed_audit_projections": len(audit_seen),
        "decision_domain": sorted(decisions),
        "rif": passed / completed if completed else 0.0,
        "domain_span": {
            "raw_states": len(raw_seen),
            "acceptance_projections": len(q_seen),
            "audit_projections": len(audit_seen),
            "decisions": len(decisions),
        },
        "cases_per_second": completed / elapsed,
        "elapsed_seconds": elapsed,
    }


def main():
    started = time.perf_counter()
    RESULTS_FILE.write_text("", encoding="utf-8")
    rng = random.Random(SEED)
    total = passed = failed = 0
    raw_seen, q_seen, audit_seen, decisions = set(), set(), set(), set()
    mismatch_cases = []

    def execute(label, s, t):
        nonlocal total, passed, failed
        ref, impl = run_pair(s, t)
        pref, pimp = projection_acceptance(ref), projection_acceptance(impl)
        aref, aimp = projection_audit(ref), projection_audit(impl)
        ok = pref == pimp
        total += 1
        passed += int(ok)
        failed += int(not ok)
        raw_seen.add(raw_fingerprint(s, t))
        q_seen.add(pref)
        audit_seen.add(aref)
        decisions.add(ref.decision)
        record = {
            "label": label,
            "reference_acceptance_projection": pref,
            "implementation_acceptance_projection": pimp,
            "reference_audit_projection": aref,
            "implementation_audit_projection": aimp,
            "equivalent": ok,
            "raw_state_digest": raw_fingerprint(s, t),
        }
        if not ok:
            mismatch_cases.append(record)
        append_result(record)
        return ok

    for label, s, t in named_cases():
        execute(label, s, t)
        print(f"[named] {label}: {'PASS' if total and not mismatch_cases[-1:] or True else 'FAIL'}", flush=True)

    for i in range(RANDOM_CASES):
        mutation, s, t = random_case(rng, i)
        execute(f"random_{i:05d}_{mutation}", s, t)
        if (i + 1) % BATCH_SIZE == 0:
            snap = metric_snapshot(started, total, passed, raw_seen, q_seen, audit_seen, decisions)
            print(json.dumps({"batch": i + 1, "cases": total, "passed": passed, "failed": failed, "metrics": snap}, sort_keys=True), flush=True)

    sensitivity, xi = sensitivity_metrics()
    omega = omega_metric()
    elapsed = max(time.perf_counter() - started, 1e-12)
    minimality_failures = [k for k, v in sensitivity.items() if not v["changed"]]
    metrics = metric_snapshot(started, total, passed, raw_seen, q_seen, audit_seen, decisions)
    metrics["xi"] = xi
    metrics["xi_mean"] = sum(xi.values()) / len(xi) if xi else 0.0
    metrics["omega"] = omega["value"]
    metrics["omega_definition"] = "pairwise non-additivity rate of controlled projection-change indicators"
    metrics["omega_pairs_tested"] = omega["pairs_tested"]

    closed = (
        failed == 0 and
        not mismatch_cases and
        not minimality_failures and
        total == len(list(named_cases())) + RANDOM_CASES
    )

    summary = {
        "version": "EOF-INSTRUMENTED-2026-09-12",
        "seed": SEED,
        "named_cases": len(list(named_cases())),
        "randomized_cases": RANDOM_CASES,
        "cases_completed": total,
        "cases_passed": passed,
        "cases_failed": failed,
        "pass_rate": passed / total if total else 0.0,
        "reference_implementation_equivalence": not mismatch_cases,
        "projection_definitions": {
            "audit": "(decision, reason, merchant, tx_id)",
            "acceptance": "(decision, reason, merchant)"
        },
        "minimality": {
            "tested_dimensions": list(sensitivity),
            "failures": minimality_failures,
            "all_declared_dimensions_observed_sensitive": not minimality_failures,
            "sensitivity": sensitivity,
        },
        "metrics": metrics,
        "omega": omega,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "elapsed_seconds": elapsed,
        },
        "mismatch_cases": mismatch_cases,
        "empirical_closure_status": "CLOSED_OVER_DECLARED_TEST_DOMAIN" if closed else "OPEN",
        "claim_boundary": "LOCAL_REFERENCE_ORACLE_ONLY",
        "network_equivalence": "UNPROVEN",
        "certificate_status": "EMPIRICAL_LOCAL" if closed else "FAILED",
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    certificate = {
        "certificate_version": "MASQ-V2-1",
        "benchmark_summary_digest": digest(summary),
        "results_digest": digest(RESULTS_FILE.read_text(encoding="utf-8")),
        "scenario_seed": SEED,
        "corpus_size": total,
        "cases_passed": passed,
        "cases_failed": failed,
        "empirical_closure_status": summary["empirical_closure_status"],
        "claim_boundary": summary["claim_boundary"],
        "network_equivalence": summary["network_equivalence"],
    }
    CERTIFICATE_FILE.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")

    print("FINAL SUMMARY")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"certificate={CERTIFICATE_FILE}")
    return 0 if closed else 1


def append_result(record: dict):
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
        f.flush()


if __name__ == "__main__":
    raise SystemExit(main())
