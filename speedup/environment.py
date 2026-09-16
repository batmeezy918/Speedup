"""PCSS environment fingerprinting.

A complete environment hash captures platform, CPU, kernel, and toolchain
identities.  The runner emits this fingerprint for every execution; the
certificate binds it to prevent silent re-use across different silicon.
"""
from __future__ import annotations

import os
import platform
import sys
import time
from typing import Any, Dict

from .jsonutil import sha256


def capture_environment(toolchain: str | None = None) -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "pid": os.getpid(),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        env["cpu_count"] = os.cpu_count()
    except Exception:
        env["cpu_count"] = None

    try:
        with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
            if "MemTotal" in first_line:
                env["mem_total_kb"] = int(first_line.split()[1])
    except Exception:
        pass

    if toolchain is not None:
        env["toolchain"] = toolchain
    env["environment_hash"] = sha256(env)
    return env