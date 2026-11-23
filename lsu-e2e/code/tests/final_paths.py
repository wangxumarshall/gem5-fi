#!/usr/bin/env python3
"""Locate the authoritative evidence/report files in both supported layouts.

Two layouts are supported and contain the same authoritative data:

* extracted package::

      <root>/code/tests/test_*.py
      <root>/evidence/causal_chains/
      <root>/evidence/rp01/
      <root>/evidence/controls/
      <root>/evidence/semantic/
      <root>/reports/

* working tree::

      <root>/tests/test_*.py
      <root>/evidence/causal_chains/
      <root>/evidence/strict_chains/          (RP01 observation chains)
      <root>/evidence/rp01_stall_traces/
      <root>/reports/                         (controls + semantic in R1)

The root is found by walking up from this file until a directory that has
both ``evidence/causal_chains`` and ``reports`` is reached.  No server
absolute path is used.
"""
from __future__ import annotations

import gzip
from pathlib import Path


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for cand in here.parents:
        if (cand / "evidence" / "causal_chains").is_dir() and (
                cand / "reports").is_dir():
            return cand
    raise RuntimeError(
        "cannot locate evidence/causal_chains and reports above %s" % here)


ROOT = _find_root()
REPORTS = ROOT / "reports"


def _chain_dir() -> Path:
    """Authoritative 180-chain directory.

    The working tree contains a stale ``evidence/causal_chains`` snapshot
    (45,890 edges).  The frozen delivery chains are
    ``evidence/strict_delivery/causal_chains`` (712,998 edges), which the
    package ships as ``evidence/causal_chains``.  Never mix the two.
    """
    delivery = ROOT / "evidence" / "strict_delivery" / "causal_chains"
    if len(list(delivery.glob("E2E-*-FAULT.causal_chain.json"))) == 180:
        return delivery
    return ROOT / "evidence" / "causal_chains"


CHAINS = _chain_dir()


def rp01_chains() -> Path:
    """Directory holding RP01OBS-*-FAULT.strict.json."""
    packaged = ROOT / "evidence" / "rp01"
    if packaged.is_dir() and any(packaged.glob("RP01OBS-*-FAULT.strict.json")):
        return packaged
    return ROOT / "evidence" / "strict_chains"


def stall_traces() -> Path:
    """Directory holding the canonical RP01 *.csv.gz stall traces."""
    packaged = ROOT / "evidence" / "rp01" / "stall_traces"
    if packaged.is_dir():
        return packaged
    return ROOT / "evidence" / "rp01_stall_traces"


def controls() -> Path:
    """Directory holding the 60-control evidence indexes."""
    packaged = ROOT / "evidence" / "controls"
    if packaged.is_dir():
        return packaged
    return REPORTS


def semantic() -> Path:
    """Directory holding the semantic reconciliation/revalidation files."""
    packaged = ROOT / "evidence" / "semantic"
    if packaged.is_dir():
        return packaged
    return REPORTS


def squash() -> Path:
    """Directory holding the six historical squash audit files."""
    packaged = ROOT / "evidence" / "squash"
    if packaged.is_dir():
        return packaged
    return REPORTS


def all180_ledger() -> Path:
    """Path to SEMANTIC_REVALIDATION_ALL_180.csv(.gz)."""
    d = semantic()
    plain = d / "SEMANTIC_REVALIDATION_ALL_180.csv"
    if plain.exists():
        return plain
    return d / "SEMANTIC_REVALIDATION_ALL_180.csv.gz"


def open_text(path: Path):
    """Open a plain or gzip-compressed text file."""
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", newline="")
    return open(path, newline="")
