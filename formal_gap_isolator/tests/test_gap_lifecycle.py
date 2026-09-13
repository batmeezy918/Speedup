import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from gap_lifecycle import append_event


def test_valid_transition_is_append_only(tmp_path):
    p = tmp_path / "gaps.jsonl"
    e = append_event(p, "GAP-X", "OPEN", "READY")
    assert e["from"] == "OPEN"
    assert e["to"] == "READY"
    assert len(p.read_text().splitlines()) == 1


def test_illegal_transition_rejected(tmp_path):
    with pytest.raises(ValueError):
        append_event(tmp_path / "gaps.jsonl", "GAP-X", "OPEN", "CLOSED")
