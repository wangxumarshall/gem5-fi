#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSU active-scope policy (F0/F5) and formal-run frequency gate.

The source registry (173 RunIDs / 519 seeds) is never rewritten. The active
scope is a separate, machine-readable view:

  active_frequencies = F0, F5
  active_runids      = 80
  active_seeds       = 240

F1–F4 are DEFERRED_BY_USER, not failed/missing/deleted. Historical seeds that
were completed before the scope decision remain
HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "configs/fsu/ACTIVE_SCOPE.json"
DEFAULT_RUNIDS = ROOT / "docs/gem5-fi/fsu/runids.json"

SCOPE_ERROR = "frequency outside active scope"


class ScopeError(ValueError):
    """Formal run rejected because its frequency is not F0/F5."""


def load_scope(path: Path = DEFAULT_SCOPE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def frequency_from_runid(runid: str):
    m = re.search(r"-F(\d+)-W\d+$", str(runid))
    return f"F{m.group(1)}" if m else ""


def is_active_freq(freq: str, scope=None):
    scope = scope or load_scope()
    return str(freq) in scope["active_frequencies"]


def enforce_active_freq(freq: str, runid: str = "", scope=None):
    """Raise ScopeError for a formal run outside F0/F5."""
    if is_active_freq(freq, scope):
        return
    scope = scope or load_scope()
    raise ScopeError(
        f"{SCOPE_ERROR}: run_id={runid or '?'} freq={freq!r} "
        f"active={scope['active_frequencies']} "
        f"policy=DEFERRED_BY_USER (not a failure)")


RUNID_FREQ_RE = re.compile(r"FSU-[A-Za-z0-9]+-(F\d+)-W\d+")


def deferred_frequencies_in(obj, scope=None):
    """Frequencies referenced by RunIDs inside a campaign payload that are
    outside the active scope, sorted. Empty list == gate passes.

    Shared by tools/campaign.py so the YAML-wide frequency gate and its
    regression tests use one implementation.
    """
    scope = scope or load_scope()
    freqs = set(RUNID_FREQ_RE.findall(json.dumps(obj)))
    return sorted(f for f in freqs if not is_active_freq(f, scope))


def scope_status(freq: str, admitted_seeds: int, scope=None, proxy_seeds=0):
    """Map a RunID's completion to the active-scope vocabulary."""
    scope = scope or load_scope()
    if is_active_freq(freq, scope):
        if admitted_seeds >= 3:
            return "ACTIVE_COMPLETE_3_OF_3"
        if admitted_seeds > 0:
            return f"ACTIVE_PARTIAL_{admitted_seeds}_OF_3"
        if proxy_seeds > 0:
            # Real, preserved evidence at a non-workbook injection site; it
            # must never read as "not run" or as certified.
            return "ACTIVE_PROXY_ONLY"
        return "ACTIVE_NOT_RUN"
    if admitted_seeds >= 3:
        return "HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE"
    if admitted_seeds > 0:
        return "HISTORICAL_PARTIAL_OUT_OF_ACTIVE_SCOPE"
    return "DEFERRED_BY_USER"


def verify_scope_against_registry(scope_path: Path = DEFAULT_SCOPE,
                                  runids_path: Path = DEFAULT_RUNIDS):
    """Assert the declared active counts match the real registry."""
    scope = load_scope(scope_path)
    data = json.loads(Path(runids_path).read_text(encoding="utf-8"))
    items = data.get("runids", data if isinstance(data, list) else [])
    counts = {}
    for x in items:
        f = x["频率"]
        counts[f] = counts.get(f, 0) + 1
    errors = []
    if len(items) != scope["source_registry_count"]:
        errors.append(f"source_registry_count {scope['source_registry_count']} "
                      f"!= actual {len(items)}")
    if data.get("count") is not None and data.get("count") != len(items):
        errors.append(f"runids.json count {data.get('count')} "
                      f"!= list length {len(items)}")
    ids = [x["RunID"] for x in items]
    if len(set(ids)) != len(ids):
        errors.append("duplicate RunID in source registry")
    want_sha = scope.get("source_registry_sha256")
    if want_sha:
        got_sha = hashlib.sha256(Path(runids_path).read_bytes()).hexdigest()
        if got_sha != want_sha:
            errors.append(f"source_registry_sha256 {got_sha} != {want_sha}")
    if (set(scope.get("active_frequency_counts", {}))
            != set(scope["active_frequencies"])):
        errors.append("active_frequency_counts keys != active_frequencies")
    active = sum(counts.get(f, 0) for f in scope["active_frequencies"])
    if active != scope["active_runid_count"]:
        errors.append(f"active_runid_count {scope['active_runid_count']} "
                      f"!= actual {active}")
    if scope["active_seed_target"] != active * 3:
        errors.append("active_seed_target != active_runid_count*3")
    if scope["source_seed_target"] != len(items) * 3:
        errors.append("source_seed_target != source_registry_count*3")
    for f, want in scope.get("active_frequency_counts", {}).items():
        if counts.get(f, 0) != want:
            errors.append(f"active_frequency_counts[{f}] {want} "
                          f"!= actual {counts.get(f, 0)}")
    return {"ok": not errors, "errors": errors, "counts": counts,
            "active_runid_count": active,
            "active_seed_target": active * 3}


def formal_out_root_allowed(manifest: dict, out_root: Path):
    """A scope test-mode run must never write the formal runs/fsu root."""
    test_mode = bool(manifest.get("scope_test_mode"))
    if not test_mode:
        return True, ""
    out = Path(out_root).resolve()
    formal = (ROOT / "runs/fsu").resolve()
    if out == formal or formal in out.parents:
        return False, ("scope test mode may not write formal runs/fsu; "
                       "use a temporary out-root")
    return True, ""
