import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from gap_isolator import extract


def test_all_false_yields_all_gate_gaps():
    cert = {"run_id": "T", "gates": {g: False for g in ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")}}
    gaps = extract(cert)
    assert len(gaps) == 7


def test_quotient_only_gap():
    gates = {g: True for g in ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")}
    gates["quotient_forward"] = False
    gaps = extract({"run_id": "T", "gates": gates})
    assert [g["type"] for g in gaps] == ["EQUIVALENCE_GAP"]
    assert gaps[0]["status"] == "OPEN"
