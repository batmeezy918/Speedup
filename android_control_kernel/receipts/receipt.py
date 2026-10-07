"""Runtime receipt schema for baseline vs transformed execution."""
from dataclasses import dataclass, asdict
from time import time_ns
import json, hashlib

@dataclass
class RuntimeReceipt:
    request_id: str
    operation: str
    operator_chain: list[str]
    baseline_ns: int
    optimized_ns: int
    correctness: str
    observed_speedup: float
    timestamp_ns: int

    def digest(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def to_json(self) -> str:
        payload = asdict(self)
        payload["receipt_sha256"] = self.digest()
        return json.dumps(payload, indent=2, sort_keys=True)
