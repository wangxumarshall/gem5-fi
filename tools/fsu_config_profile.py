#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSU config-profile constants and config.ini verification.

The workbook B0 row is the O3_ARM_v7a_3 point:
  ROB=40, unified IQ=32, fetch/decode/rename=3/3/3, dispatch=6,
  issue/wb/commit=8/8/8, PRF int/float/vec=128/192/48.
This module is the single source of truth for the Python-side gate; the
gem5 config applies the same constants and the runner/audit verify the real
config.ini written by gem5.

B0-core scope: the workbook-explicit rows above plus the v7a_3 LQ/SQ/
fetchBuffer/squash values. The custom 2-FU FP pool is not part of this
gate (documented as a remaining gap, not silently claimed).
"""
from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path

PROFILES = {
    "B0": {
        "profile_version": "B0-core-v7a3-1",
        "fetchWidth": 3, "decodeWidth": 3, "renameWidth": 3,
        "dispatchWidth": 6, "issueWidth": 8, "wbWidth": 8,
        "commitWidth": 8, "numROBEntries": 40, "iqEntries": 32,
        "numPhysIntRegs": 128, "numPhysFloatRegs": 192,
        "numPhysVecRegs": 48, "LQEntries": 16, "SQEntries": 16,
        "fetchBufferSize": 16, "squashWidth": 8,
    },
    "C3": {
        "profile_version": "C3-actual-2026-11",
        "fetchWidth": 4, "decodeWidth": 4, "renameWidth": 4,
        "dispatchWidth": 4, "issueWidth": 4, "wbWidth": 8,
        "commitWidth": 4, "numROBEntries": 128, "iqEntries": 64,
        "numPhysIntRegs": 128, "numPhysFloatRegs": 192,
        "numPhysVecRegs": 48,
    },
}


def _first_section(cp, type_name):
    for name in cp.sections():
        if cp.get(name, "type", fallback="") == type_name:
            return name
    return None


def read_config_ini(path):
    """Return the profile-relevant values from a gem5 config.ini.

    Missing/unparseable input returns (None, [error]) rather than a guess.
    """
    p = Path(path)
    if not p.exists():
        return None, [f"missing config.ini: {p}"]
    cp = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        cp.read(p, encoding="utf-8")
    except configparser.Error as e:
        return None, [f"unparseable config.ini: {e}"]
    core = _first_section(cp, "BaseO3CPU")
    if core is None:
        return None, ["no type=BaseO3CPU section"]
    iq = None
    for name in cp.sections():
        if (cp.get(name, "type", fallback="") == "IQUnit"
                and name.endswith("instQueues")):
            iq = name
            break
    if iq is None:
        return None, ["no type=IQUnit instQueues section"]

    def num(section, key):
        raw = cp.get(section, key, fallback="")
        try:
            return int(raw)
        except ValueError:
            return None

    actual = {k: num(core, k) for k in (
        "fetchWidth", "decodeWidth", "renameWidth", "dispatchWidth",
        "issueWidth", "wbWidth", "commitWidth", "numROBEntries",
        "numPhysIntRegs", "numPhysFloatRegs", "numPhysVecRegs",
        "LQEntries", "SQEntries", "fetchBufferSize", "squashWidth")}
    actual["iqEntries"] = num(iq, "numEntries")
    return actual, []


def verify_config_profile(path, profile="B0"):
    """Compare a real config.ini against the named profile."""
    p = Path(path)
    expected = PROFILES.get(profile)
    if expected is None:
        return {"ok": False, "profile": profile, "errors":
                [f"unknown profile {profile!r}"], "actual": None}
    actual, errors = read_config_ini(path)
    if actual is None:
        return {"ok": False, "profile": profile, "errors": errors,
                "actual": None}
    for key, want in expected.items():
        if key == "profile_version":
            continue
        got = actual.get(key)
        if got != want:
            errors.append(f"{key}: expected {want}, got {got}")
    return {"ok": not errors, "profile": profile,
            "profile_version": expected["profile_version"],
            "expected": {k: v for k, v in expected.items()
                         if k != "profile_version"},
            "actual": actual, "errors": errors,
            "config_ini_sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def fingerprint(profile="B0"):
    doc = PROFILES[profile]
    return hashlib.sha256(json.dumps(doc, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()
