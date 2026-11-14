"""Resolve repository paths shared by the Phase-0/Phase-1 tools.

The repository ships two gem5 build directories:

* ``build/ARM/gem5.opt``              native AArch64 host build (this machine)
* ``build/ARM_ACE_IBR_AUDIT/gem5.opt`` pre-built audit binary (may be x86-64)

Historically the Python tools defaulted to the second one, which fails with
``Exec format error`` on an AArch64 host.  Resolve the native build first and
keep the audit build only as a fallback.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEM5_SRC = ROOT / "CHAOS/gem5"

# Ordered candidates used when the caller does not pass --gem5/GEM5_OPT.
GEM5_CANDIDATES = (
    GEM5_SRC / "build/ARM/gem5.opt",
    GEM5_SRC / "build/ARM_ACE_IBR_AUDIT/gem5.opt",
)


def default_gem5() -> Path:
    """Return the gem5 binary Phase-0/Phase-1 tools should use by default.

    ``GEM5_OPT`` wins when set (this is the same variable the shell scripts
    use).  Otherwise prefer the native ARM build and fall back to the audit
    build.  The path is returned even when it does not exist so callers can
    emit a useful "binary not found" error instead of silently selecting a
    different build.
    """

    override = os.environ.get("GEM5_OPT")
    if override:
        return Path(override)
    for candidate in GEM5_CANDIDATES:
        if candidate.is_file():
            return candidate
    return GEM5_CANDIDATES[0]


def default_cc() -> str:
    """Return the AArch64 cross compiler installed on this host.

    openEuler ships ``aarch64-openEuler-linux-gcc``; Debian/Ubuntu ships
    ``aarch64-linux-gnu-gcc``.  ``ARM_CC`` always wins.
    """

    override = os.environ.get("ARM_CC")
    if override:
        return override
    for name in ("aarch64-openEuler-linux-gcc", "aarch64-linux-gnu-gcc"):
        if shutil.which(name):
            return name
    return "aarch64-openEuler-linux-gcc"
