import json, hashlib, time, os, resource
from pathlib import Path
from typing import Dict, List, Optional, Any
from agd_framework.utils import *
from agd_framework.canonical import Phase1Canonical, CanonicalState
from agd_framework.omega import OmegaObservable, OmegaSignature
from agd_framework.quotient import Phase3Quotient, QuotientResult
from agd_framework.decision import Phase4Decision, DecisionResult
from agd_framework.factorization import Phase6Factorization, FactorizationReport
from agd_framework.false_merge import Phase5FalseMerge
from agd_framework.operator import Phase7OperatorDescent
from agd_framework.reconstruction import Phase8Reconstruction

@dataclass
class CostMetrics:
    baseline_total_time: float = 0.0
    canonicalization_time: float = 0.0
    omega_time: float = 0.0
    quotient_construction_time: float = 0.0
    lookup_time: float = 0.0
    representative_execution_time: float = 0.0
    reconstruction_time: float = 0.0
    validation_time: float = 0.0
    artifact_write_time: float = 0.0
    model_calls_baseline: int = 0
    model_calls_AGD: int = 0
    tool_calls_baseline: int = 0
    tool_calls_AGD: int = 0
    tokens_baseline: int = 0
    tokens_AGD: int = 0
    wall_time: float = 0.0
    cpu_time: float = 0.0
    memory_peak: float = 0.0

class Phase9Modes:
    def __init__(self, framework):
        self.framework = framework
        self.mode_a_results: Dict = {}
        self.mode_b_results: Dict = {}
        self.mode_c_results: Dict = {}

    def run_mode_a_official_baseline(self, tasks: List) -> dict:
        start = time.time()
        results = {"tasks_executed": 0, "total_time": 0.0}
        for task_data in tasks:
            results["tasks_executed"] += 1
        results["total_time"] = time.time() - start
        self.mode_a_results = results
        return results

    def run_mode_b_control_optimization(self, tasks: List,
                                         states: List[CanonicalState]) -> dict:
        start = time.time()
        seen = set()
        deduped = 0
        for state in states:
            if state.sha256 not in seen:
                seen.add(state.sha256)
            else:
                deduped += 1
        results = {
            "unique_states": len(seen),
            "deduplicated": deduped,
            "total_time": time.time() - start,
            "method": "exact_hash_dedup",
        }
        self.mode_b_results = results
        return results

    def run_mode_c_agd(self, tasks: List,
                        states: List[CanonicalState],
                        omega: OmegaObservable,
                        quotient: Phase3Quotient) -> dict:
        start = time.time()
        omega_sigs = {}
        for state in states:
            tpath = Path(state.source_file)
            parsed = parse_task_md(tpath)
            sig = omega.compute(parsed, tpath)
            omega_sigs[state.state_id] = sig
        omega_time = time.time() - start

        start = time.time()
        qr = quotient.construct(states, omega_sigs)
        quotient_time = time.time() - start

        results = {
            "quotient_classes": qr.classes_count,
            "total_states": qr.states_count,
            "rho_Q": qr.rho_Q,
            "omega_time": omega_time,
            "quotient_time": quotient_time,
        }
        self.mode_c_results = results
        return results

class Phase10CostAccounting:
    def __init__(self):
        self.costs = CostMetrics()

    def compute_speedup(self) -> float:
        agd_total = (self.costs.canonicalization_time +
                     self.costs.omega_time +
                     self.costs.quotient_construction_time +
                     self.costs.lookup_time +
                     self.costs.representative_execution_time +
                     self.costs.reconstruction_time +
                     self.costs.validation_time +
                     self.costs.artifact_write_time)
        if agd_total == 0:
            return float("inf")
        return self.costs.baseline_total_time / agd_total

    def compute_ratio(self) -> float:
        return self.costs.model_calls_baseline / max(self.costs.model_calls_AGD, 1)
