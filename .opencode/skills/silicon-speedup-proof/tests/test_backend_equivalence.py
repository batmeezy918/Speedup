#!/usr/bin/env python3
"""Equivalence of the two JSON Schema backends, and the CLI cost of each.

The `--fast` path skips the `jsonschema` import because it dominates CLI
latency. That is only worth offering if the bundled checker produces the SAME
verdicts on the same inputs. This module asserts that over the entire fixture
corpus rather than over a sample.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

from _harness import (LEDGERS, PROJECT_ROOT, RUNS, S, validate_ledger,
                      validate_run)


def _corpus():
    files = sorted(LEDGERS.glob("*.jsonl")) + [Path(S.SKILL_ROOT) / "native/evidence/native_ledger.jsonl"]
    runs = sorted(RUNS.glob("*.json")) + [Path(S.SKILL_ROOT) / "native/evidence/native_blockdiag_evidence.json"]
    return [f for f in files if f.exists()], [f for f in runs if f.exists()]


def _code_signature(findings):
    """Compare on the finding codes and severities, not on message wording:
    the two backends word schema errors differently."""
    return sorted((f.code, f.severity) for f in findings)


class BackendsAgree(unittest.TestCase):
    """Same inputs, same verdicts, either backend."""

    def _both(self, fn, *args):
        S.set_backend("jsonschema")
        primary = _code_signature(fn(*args))
        S.set_backend("builtin")
        secondary = _code_signature(fn(*args))
        S.set_backend("jsonschema")
        return primary, secondary

    def test_ledgers_agree_on_every_fixture(self):
        files, _ = _corpus()
        self.assertGreater(len(files), 1)
        for path in files:
            with self.subTest(fixture=path.name):
                a, b = self._both(lambda p=path: validate_ledger.validate_ledger(
                    p, PROJECT_ROOT)[0])
                self.assertEqual(a, b)

    def test_run_records_agree_on_every_fixture(self):
        _, files = _corpus()
        self.assertGreater(len(files), 1)
        for path in files:
            with self.subTest(fixture=path.name):
                record = json.loads(path.read_text(encoding="utf-8"))
                a, b = self._both(lambda r=record, p=path: validate_run.validate_record(
                    r, where=p.name, repo_root=PROJECT_ROOT, record_path=p))
                self.assertEqual(a, b)

    def test_verdict_not_just_findings_agrees(self):
        for path in sorted(LEDGERS.glob("*.jsonl")):
            with self.subTest(fixture=path.name):
                S.set_backend("jsonschema")
                pa = subprocess.run(
                    [sys.executable, str(S.SCRIPTS_DIR / "validate-ledger.py"),
                     str(path), "--repo-root", str(PROJECT_ROOT), "--json"],
                    capture_output=True, text=True)
                S.set_backend("builtin")
                pb = subprocess.run(
                    [sys.executable, str(S.SCRIPTS_DIR / "validate-ledger.py"),
                     str(path), "--repo-root", str(PROJECT_ROOT), "--fast", "--json"],
                    capture_output=True, text=True)
                S.set_backend("jsonschema")
                self.assertEqual(pa.returncode, pb.returncode, path.name)
                self.assertEqual(json.loads(pa.stdout)["verdict"],
                                 json.loads(pb.stdout)["verdict"], path.name)

    def test_backend_is_reported_in_the_summary(self):
        _, summary = validate_ledger.validate_ledger(LEDGERS / "synthetic_valid.jsonl", None)
        self.assertIn(summary["schema_backend"], ("jsonschema", "builtin-mini"))

    def test_unknown_backend_name_is_refused(self):
        with self.assertRaises(ValueError):
            S.set_backend("not-a-backend")


class CLICost(unittest.TestCase):
    """The operational reason --fast exists, measured rather than asserted."""

    def _time_cli(self, extra_args, path, n=5):
        cmd = [sys.executable, str(S.SCRIPTS_DIR / "validate-ledger.py"), str(path),
               "--repo-root", str(PROJECT_ROOT), "--quiet", *extra_args]
        subprocess.run(cmd, capture_output=True)
        t0 = time.perf_counter()
        for _ in range(n):
            subprocess.run(cmd, capture_output=True)
        return (time.perf_counter() - t0) / n

    def test_fast_path_is_not_slower_than_the_default(self):
        path = Path(S.SKILL_ROOT) / "native/evidence/native_ledger.jsonl"
        slow = self._time_cli([], path)
        fast = self._time_cli(["--fast"], path)
        # The whole point is that skipping the import cannot cost more.
        self.assertLessEqual(fast, slow * 1.05,
                             msg=f"fast={fast*1000:.1f}ms slow={slow*1000:.1f}ms")

    def test_corpus_sweep_cost_is_recorded(self):
        # Not a threshold assertion: a CI-visible record of what a full sweep costs.
        ledgers, runs = _corpus()
        t0 = time.perf_counter()
        for path in ledgers:
            subprocess.run([sys.executable, str(S.SCRIPTS_DIR / "validate-ledger.py"),
                            str(path), "--repo-root", str(PROJECT_ROOT), "--quiet",
                            "--fast"], capture_output=True)
        for path in runs:
            subprocess.run([sys.executable, str(S.SCRIPTS_DIR / "validate-run.py"),
                            str(path), "--repo-root", str(PROJECT_ROOT), "--quiet",
                            "--fast"], capture_output=True)
        el = time.perf_counter() - t0
        self.assertGreater(len(ledgers) + len(runs), 10)
        # Guard against a pathological regression, not against normal variance.
        self.assertLess(el, 30.0, msg=f"full --fast sweep took {el:.1f}s")
        print(f"\n  corpus sweep (--fast): {len(ledgers)+len(runs)} files in {el:.2f}s")


if __name__ == "__main__":
    unittest.main(verbosity=2)