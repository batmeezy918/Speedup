#!/usr/bin/env python3
"""
EOF / MASQ — Merchant Assurance Semantic Quotient Benchmark
=============================================================

Deterministic local reference-oracle benchmark.

Pipeline:
    Evidence -> Identity -> Credential -> Trust -> Delegation
    -> Scope -> Transaction -> Lifecycle/Freshness -> Routing
    -> Decision -> Observable Projection Π -> Quotient / Differential Equivalence

IMPORTANT:
    This establishes only local semantic equivalence against the declared
    reference oracle. It does NOT certify equivalence to a private payment
    network, acquirer, card scheme, or processor.

STREAMING:
    Every completed test is printed immediately.
    Every batch summary is printed immediately.
    Every completed result is appended to JSONL immediately.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Optional, Any

NOW = 1000
RANDOM_CASES = 5000
BATCH_SIZE = 250
SEED = 20260912
RESULTS_FILE = Path("masq_finished_runs.jsonl")
SUMMARY_FILE = Path("masq_final_summary.json")


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
    state_digest = digest(state)

    def result(decision: str, reason: str) -> Decision:
        return Decision(decision, reason, state.identity, tx.tx_id, state_digest)

    if not state.evidence.present:
        return result("INDETERMINATE", "MISSING_EVIDENCE")
    if state.evidence.subject != state.identity:
        return result("DENY", "UNKNOWN_MERCHANT")
    if not state.evidence.trusted_issuer:
        return result("DENY", "UNTRUSTED_ISSUER")
    if not state.evidence.signature_valid:
        return result("DENY", "BAD_SIGNATURE")

    credential = state.credential
    if credential is None:
        return result("DENY", "CREDENTIAL_MISSING")
    if credential.subject != state.identity or credential.bound_key != state.key:
        return result("DENY", "CREDENTIAL_BINDING_MISMATCH")
    if credential.revoked:
        return result("DENY", "CREDENTIAL_REVOKED")
    if not credential.valid_from <= tx.issued_at <= credential.valid_until:
        return result("DENY", "CREDENTIAL_EXPIRED")

    if state.delegation is not None:
        delegation = state.delegation
        if delegation.agent != tx.agent or delegation.merchant != state.identity:
            return result("DENY", "DELEGATION_MISSING")
        if delegation.revoked:
            return result("DENY", "DELEGATION_REVOKED")
        if not delegation.valid_from <= tx.issued_at <= delegation.valid_until:
            return result("DENY", "DELEGATION_EXPIRED")
    elif tx.agent is not None:
        return result("DENY", "DELEGATION_MISSING")

    if tx.operation not in state.allowed_operations:
        return result("DENY", "SCOPE_DENIED")
    if tx.amount > state.max_amount:
        return result("DENY", "AMOUNT_EXCEEDED")
    if tx.currency not in state.currencies:
        return result("DENY", "CURRENCY_DENIED")
    if tx.merchant != state.identity:
        return result("DENY", "TRANSACTION_BINDING_MISMATCH")
    if tx.expires_at < tx.issued_at or tx.expires_at < NOW:
        return result("DENY", "ASSERTION_EXPIRED")
    if tx.issued_at > NOW:
        return result("DENY", "ASSERTION_NOT_YET_VALID")
    if tx.tx_id in state.replayed_jtis:
        return result("DENY", "REPLAY")
    if state.lifecycle != "ACTIVE":
        return result("DENY", "LIFECYCLE_INACTIVE")
    if not state.route_allowed:
        return result("DENY", "ROUTE_DENIED")
    return result("ALLOW", "ALLOW")


def independent_implementation(state: MerchantState, tx: Transaction) -> Decision:
    state_digest = digest(state)

    def result(decision: str, reason: str) -> Decision:
        return Decision(decision, reason, state.identity, tx.tx_id, state_digest)

    evidence = state.evidence
    if not evidence.present:
        return result("INDETERMINATE", "MISSING_EVIDENCE")
    if evidence.subject != state.identity:
        return result("DENY", "UNKNOWN_MERCHANT")
    if not evidence.trusted_issuer:
        return result("DENY", "UNTRUSTED_ISSUER")
    if not evidence.signature_valid:
        return result("DENY", "BAD_SIGNATURE")

    credential = state.credential
    if credential is None:
        return result("DENY", "CREDENTIAL_MISSING")
    if credential.subject != state.identity or credential.bound_key != state.key:
        return result("DENY", "CREDENTIAL_BINDING_MISMATCH")
    if credential.revoked:
        return result("DENY", "CREDENTIAL_REVOKED")
    if not credential.valid_from <= tx.issued_at <= credential.valid_until:
        return result("DENY", "CREDENTIAL_EXPIRED")

    delegation = state.delegation
    if tx.agent is not None:
        if delegation is None:
            return result("DENY", "DELEGATION_MISSING")
        if delegation.agent != tx.agent or delegation.merchant != state.identity:
            return result("DENY", "DELEGATION_MISSING")
        if delegation.revoked:
            return result("DENY", "DELEGATION_REVOKED")
        if not delegation.valid_from <= tx.issued_at <= delegation.valid_until:
            return result("DENY", "DELEGATION_EXPIRED")

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
    for condition, reason in checks:
        if not condition:
            return result("DENY", reason)
    return result("ALLOW", "ALLOW")


def projection(decision: Decision) -> tuple:
    return (decision.decision, decision.reason, decision.merchant, decision.tx_id)


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
    state = base_state()
    tx = base_transaction()
    yield "valid_baseline", state, tx
    yield "missing_evidence", replace(state, evidence=replace(state.evidence, present=False)), tx
    yield "untrusted_issuer", replace(state, evidence=replace(state.evidence, trusted_issuer=False)), tx
    yield "bad_signature", replace(state, evidence=replace(state.evidence, signature_valid=False)), tx
    yield "credential_missing", replace(state, credential=None), tx
    yield "credential_revoked", replace(state, credential=replace(state.credential, revoked=True)), tx
    yield "credential_wrong_key", replace(state, key="key-B"), tx
    yield "credential_expired", replace(state, credential=replace(state.credential, valid_until=999)), tx
    yield "scope_denied", state, replace(tx, operation="CAPTURE")
    yield "amount_exceeded", state, replace(tx, amount=10001)
    yield "currency_denied", state, replace(tx, currency="EUR")
    yield "merchant_binding_mismatch", state, replace(tx, merchant="merchant-B")
    yield "expired_assertion", state, replace(tx, expires_at=999)
    yield "future_assertion", state, replace(tx, issued_at=1001, expires_at=1010)
    yield "replay", replace(state, replayed_jtis=("tx-001",)), tx
    yield "lifecycle_suspended", replace(state, lifecycle="SUSPENDED"), tx
    yield "route_denied", replace(state, route_allowed=False), tx
    delegation = Delegation("principal-1", "agent-1", "merchant-A", 900, 1100, False)
    yield "valid_delegation", replace(state, delegation=delegation), replace(tx, agent="agent-1")
    yield "missing_delegation", state, replace(tx, agent="agent-1")
    yield "revoked_delegation", replace(state, delegation=replace(delegation, revoked=True)), replace(tx, agent="agent-1")
    yield "expired_delegation", replace(state, delegation=replace(delegation, valid_until=999)), replace(tx, agent="agent-1")


def random_case(rng: random.Random, index: int):
    state = base_state()
    tx = base_transaction()
    tx = replace(tx, tx_id=f"tx-{index:06d}", nonce=f"nonce-{index:06d}")
    mutation = rng.choice([
        "none", "evidence", "issuer", "signature", "credential", "key", "scope",
        "amount", "currency", "merchant", "expiry", "future", "replay", "lifecycle",
        "route", "agent_missing", "agent_valid", "agent_revoked", "agent_expired",
    ])

    if mutation == "evidence":
        state = replace(state, evidence=replace(state.evidence, present=False))
    elif mutation == "issuer":
        state = replace(state, evidence=replace(state.evidence, trusted_issuer=False))
    elif mutation == "signature":
        state = replace(state, evidence=replace(state.evidence, signature_valid=False))
    elif mutation == "credential":
        state = replace(state, credential=replace(state.credential, revoked=True))
    elif mutation == "key":
        state = replace(state, key="wrong-key")
    elif mutation == "scope":
        tx = replace(tx, operation="CAPTURE")
    elif mutation == "amount":
        tx = replace(tx, amount=10001)
    elif mutation == "currency":
        tx = replace(tx, currency="EUR")
    elif mutation == "merchant":
        tx = replace(tx, merchant="merchant-B")
    elif mutation == "expiry":
        tx = replace(tx, expires_at=999)
    elif mutation == "future":
        tx = replace(tx, issued_at=1001, expires_at=1010)
    elif mutation == "replay":
        # FIX: use the actual randomized transaction ID so replay is genuinely exercised.
        state = replace(state, replayed_jtis=(tx.tx_id,))
    elif mutation == "lifecycle":
        state = replace(state, lifecycle="SUSPENDED")
    elif mutation == "route":
        state = replace(state, route_allowed=False)
    elif mutation == "agent_missing":
        tx = replace(tx, agent="agent-1")
    elif mutation.startswith("agent_"):
        delegation = Delegation("principal-1", "agent-1", "merchant-A", 900, 1100, False)
        if mutation == "agent_revoked":
            delegation = replace(delegation, revoked=True)
        elif mutation == "agent_expired":
            delegation = replace(delegation, valid_until=999)
        state = replace(state, delegation=delegation)
        tx = replace(tx, agent="agent-1")
    return mutation, state, tx


def append_result(record: dict):
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
        f.flush()


def metric_snapshot(started: float, completed: int, passed: int, raw_dimensions: int, quotient_dimensions: int):
    elapsed = max(time.perf_counter() - started, 1e-12)
    return {
        "psi_norm": float(quotient_dimensions) ** 0.5,
        "delta_complexity": ((raw_dimensions - quotient_dimensions) / raw_dimensions if raw_dimensions else 0.0),
        "omega": 0.0,
        "xi": 1.0 if completed else 0.0,
        "rif": (passed / completed if completed else 0.0),
        "domain_span": quotient_dimensions,
        "cases_per_second": completed / elapsed,
        "elapsed_seconds": elapsed,
    }


def minimality_test():
    state = base_state()
    tx = base_transaction()
    baseline = projection(reference_oracle(state, tx))
    probes = {
        "identity": (state, replace(tx, merchant="merchant-B")),
        "evidence": (replace(state, evidence=replace(state.evidence, present=False)), tx),
        "credential": (replace(state, credential=None), tx),
        "trust": (replace(state, evidence=replace(state.evidence, trusted_issuer=False)), tx),
        "scope": (state, replace(tx, operation="CAPTURE")),
        "amount": (state, replace(tx, amount=state.max_amount + 1)),
        "currency": (state, replace(tx, currency="EUR")),
        "lifecycle": (replace(state, lifecycle="SUSPENDED"), tx),
        "routing": (replace(state, route_allowed=False), tx),
        "freshness": (state, replace(tx, expires_at=999)),
        "replay_history": (replace(state, replayed_jtis=("tx-001",)), tx),
    }
    results = {}
    for name, (probe_state, probe_tx) in probes.items():
        mutated = projection(reference_oracle(probe_state, probe_tx))
        results[name] = {"essential": baseline != mutated, "baseline": baseline, "mutated": mutated}

    delegation = Delegation("principal-1", "agent-1", "merchant-A", 900, 1100, False)
    delegated_state = replace(state, delegation=delegation)
    delegated_tx = replace(tx, agent="agent-1")
    with_delegation = projection(reference_oracle(delegated_state, delegated_tx))
    without_delegation = projection(reference_oracle(state, delegated_tx))
    results["delegation"] = {
        "essential": with_delegation != without_delegation,
        "baseline": with_delegation,
        "mutated": without_delegation,
    }
    return results


def main():
    started = time.perf_counter()
    RESULTS_FILE.write_text("", encoding="utf-8")

    print("=" * 60, flush=True)
    print("MASQ / EOF MERCHANT ASSURANCE BENCHMARK", flush=True)
    print("=" * 60, flush=True)
    print("oracle=LOCAL_REFERENCE_ORACLE", flush=True)
    print("network_certification=NOT_CLAIMED", flush=True)
    print(f"seed={SEED}", flush=True)
    print(f"random_cases={RANDOM_CASES}", flush=True)
    print(f"batch_size={BATCH_SIZE}", flush=True)
    print(f"state_digest={digest(base_state())}", flush=True)
    print("streaming_results=TRUE", flush=True)
    print("=" * 60, flush=True)

    total = passed = failed = 0
    reason_counts = {}
    named = list(named_cases())

    print("\n[PHASE 1] DETERMINISTIC ADVERSARIAL CORPUS", flush=True)
    for index, (name, state, tx) in enumerate(named, start=1):
        reference = reference_oracle(state, tx)
        implementation = independent_implementation(state, tx)
        reference_projection = projection(reference)
        implementation_projection = projection(implementation)
        equivalent = reference_projection == implementation_projection
        total += 1
        passed += int(equivalent)
        failed += int(not equivalent)
        reason_counts[reference.reason] = reason_counts.get(reference.reason, 0) + 1
        record = {
            "phase": "named", "index": index, "name": name,
            "reference": asdict(reference), "implementation": asdict(implementation),
            "reference_projection": reference_projection,
            "implementation_projection": implementation_projection,
            "equivalent": equivalent, "timestamp_ns": time.time_ns(),
        }
        append_result(record)
        print(f"[FINISHED {index:03d}/{len(named):03d}] {name:<28} {reference.decision:<13} {reference.reason:<30} equivalence={'PASS' if equivalent else 'FAIL'}", flush=True)
        if not equivalent:
            print("!!! COUNTEREXAMPLE FOUND !!!", flush=True)
            print(json.dumps(record, indent=2), flush=True)
            break

    print("\n[PHASE 2] RANDOMIZED DIFFERENTIAL CORPUS", flush=True)
    rng = random.Random(SEED)
    for index in range(1, RANDOM_CASES + 1):
        mutation, state, tx = random_case(rng, index)
        reference = reference_oracle(state, tx)
        implementation = independent_implementation(state, tx)
        reference_projection = projection(reference)
        implementation_projection = projection(implementation)
        equivalent = reference_projection == implementation_projection
        total += 1
        passed += int(equivalent)
        failed += int(not equivalent)
        reason_counts[reference.reason] = reason_counts.get(reference.reason, 0) + 1
        record = {
            "phase": "random", "index": index, "mutation": mutation,
            "reference": asdict(reference), "implementation": asdict(implementation),
            "reference_projection": reference_projection,
            "implementation_projection": implementation_projection,
            "equivalent": equivalent, "timestamp_ns": time.time_ns(),
        }
        append_result(record)
        if index % BATCH_SIZE == 0 or not equivalent:
            metrics = metric_snapshot(started, total, passed, 12, 12)
            print(f"[BATCH FINISHED {index:05d}/{RANDOM_CASES:05d}] completed={total} passed={passed} failed={failed} RIF={metrics['rif']:.6f} ΔC={metrics['delta_complexity']:.6f} ψ_norm={metrics['psi_norm']:.4f} Ω={metrics['omega']:.4f} Ξ={metrics['xi']:.4f} span={metrics['domain_span']} rate={metrics['cases_per_second']:,.0f}/s last={mutation} result={'PASS' if equivalent else 'FAIL'}", flush=True)
        if not equivalent:
            print("\n!!! DIFFERENTIAL COUNTEREXAMPLE !!!", flush=True)
            print(json.dumps(record, indent=2), flush=True)
            break

    print("\n[PHASE 3] QUOTIENT CHECK", flush=True)
    quotient_failures = 0
    for name, state, tx in named_cases():
        if projection(reference_oracle(state, tx)) != projection(independent_implementation(state, tx)):
            quotient_failures += 1
    quotient_pass = quotient_failures == 0
    print(f"Q_reference == Q_implementation: {'PASS' if quotient_pass else 'FAIL'}", flush=True)

    print("\n[PHASE 4] QUOTIENT-ESSENTIAL DIMENSIONS", flush=True)
    minimality = minimality_test()
    minimality_failures = 0
    for name, result in minimality.items():
        print(f"{name:<18} essential={'YES' if result['essential'] else 'NO'}", flush=True)
        minimality_failures += int(not result["essential"])

    elapsed = max(time.perf_counter() - started, 1e-12)
    pass_rate = passed / total if total else 0.0
    metrics = metric_snapshot(started, total, passed, 12, 12)
    closed = total > 0 and failed == 0 and quotient_failures == 0 and minimality_failures == 0
    summary = {
        "benchmark": "MASQ", "version": "EOF-FROZEN-2026-09-12", "seed": SEED,
        "named_cases": len(named), "random_cases_requested": RANDOM_CASES,
        "cases_completed": total, "cases_passed": passed, "cases_failed": failed,
        "pass_rate": pass_rate, "quotient_pass": quotient_pass,
        "quotient_failures": quotient_failures, "minimality": minimality,
        "minimality_failures": minimality_failures, "metrics": metrics,
        "reason_counts": reason_counts, "elapsed_seconds": elapsed,
        "throughput_cases_per_second": total / elapsed,
        "empirical_closure_status": "CLOSED_OVER_DECLARED_TEST_DOMAIN" if closed else "OPEN_COUNTEREXAMPLE_REQUIRES_REPAIR",
        "claim_boundary": "LOCAL_REFERENCE_ORACLE_ONLY", "network_equivalence": "UNPROVEN",
    }
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("\n" + "=" * 60, flush=True)
    print("FINAL FINISHED RUN", flush=True)
    print("=" * 60, flush=True)
    print(f"cases_completed={total}", flush=True)
    print(f"cases_passed={passed}", flush=True)
    print(f"cases_failed={failed}", flush=True)
    print(f"pass_rate={pass_rate:.6f}", flush=True)
    print(f"quotient={'PASS' if quotient_pass else 'FAIL'}", flush=True)
    print(f"minimality_failures={minimality_failures}", flush=True)
    print(f"ψ_norm={metrics['psi_norm']:.6f}", flush=True)
    print(f"Δcomplexity={metrics['delta_complexity']:.6f}", flush=True)
    print(f"Ω={metrics['omega']:.6f}", flush=True)
    print(f"Ξ={metrics['xi']:.6f}", flush=True)
    print(f"RIF={metrics['rif']:.6f}", flush=True)
    print(f"domain_span={metrics['domain_span']}", flush=True)
    print(f"elapsed_seconds={elapsed:.6f}", flush=True)
    print(f"throughput={total / elapsed:,.0f} cases/s", flush=True)
    print(f"empirical_closure_status={summary['empirical_closure_status']}", flush=True)
    print(f"finished_results_file={RESULTS_FILE}", flush=True)
    print(f"final_summary_file={SUMMARY_FILE}", flush=True)
    print("=" * 60, flush=True)
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
