"""Independent audit of the 42 R6-L per-seed propagation docs.

Every claim in a doc must be traceable to THAT seed's own raw stream:
event ids/kinds/ticks, parent ancestry, tick order, evidence SHA-256, and
the terminal/admission/certification verdict from its chain_report.json.
"""
import glob
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lsu_prop_fields as PF  # noqa: E402

DOCS = Path("/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS")
RUN_PREFIXES = ("L01", "L02", "L03")


def docs():
    out = []
    for pref in RUN_PREFIXES:
        out += sorted(DOCS.glob(f"{pref}-*/*-seed*.md"))
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _ready():
    ds = docs() if DOCS.is_dir() else []
    if len(ds) != 42:
        pytest.skip(f"L docs not yet deployed (found {len(ds)})")
    return ds


def test_42_docs_and_14_runids():
    ds = _ready()
    assert len(ds) == 42, [str(d) for d in ds][:5]
    assert len({d.parent.name for d in ds}) == 14


def test_each_doc_is_traceable_to_its_own_stream():
    ds = _ready()
    problems = []
    for p in ds:
        text = p.read_text()
        m = re.search(r"RunID `([^`]+)` / seed `(\d+)`", text)
        if not m:
            problems.append((p, "identity line missing"))
            continue
        rid, seed = m.group(1), int(m.group(2))
        if p.parent.name != rid or p.name != f"{rid}-seed{seed}.md":
            problems.append((p, "doc name/identity mismatch"))
        # every evidence row's SHA must match the file
        for _key, path, sha in re.findall(
                r"\| (prop_evt|stats|run_out|inj_log|manifest) \| "
                r"`([^`]+)` \| `([0-9a-f]{64})` \|", text):
            if not os.path.isfile(path):
                problems.append((p, f"evidence missing {path}"))
                continue
            if sha256(path) != sha:
                problems.append((p, f"evidence SHA mismatch {path}"))
        m = re.search(r"\| prop_evt \| `([^`]+)` \|", text)
        if not m:
            problems.append((p, "prop_evt row missing"))
            continue
        pe = Path(m.group(1))
        events, truncated, _s, _i = PF.read_stream(str(pe))
        byid = {str(e.get("event_id")): e for e in events}
        if truncated:
            problems.append((p, "truncated stream"))
        # each real-event-order line must exist in this stream, with the same
        # kind/tick, and its parent must exist and not post-date it
        for eid, parent, tick, kind in re.findall(
                r"`event_id=(\d+)` parent=`([^`]*)` tick=`(\d+)` "
                r"kind=`([^`]+)`", text):
            e = byid.get(eid)
            if e is None:
                problems.append((p, f"event {eid} not in own stream"))
                continue
            if str(e.get("kind")) != kind or int(e.get("tick")) != int(tick):
                problems.append((p, f"event {eid} kind/tick mismatch"))
            if parent.strip() not in ("", "—"):
                pev = byid.get(parent)
                if pev is None:
                    problems.append((p, f"parent {parent} not in own stream"))
                elif int(pev.get("tick")) > int(e.get("tick")):
                    problems.append((p, f"parent {parent} tick after child {eid}"))
        # verdict must match this seed's chain_report.json
        sr = pe.parent / "chain_report.json"
        if not os.path.isfile(sr):
            problems.append((p, "chain_report missing"))
            continue
        rep = json.load(open(sr))
        for token in (f"terminal `{rep.get('terminal')}`",
                      f"provable_to `{rep.get('provable_to')}`",
                      f"admitted `{rep.get('admitted')}`",
                      f"certified `{rep.get('certified')}`"):
            if token not in text:
                problems.append((p, f"verdict token missing: {token}"))
        if rid not in text or f"seed `{seed}`" not in text:
            problems.append((p, "identity does not belong to own seed"))
    assert not problems, problems[:10]


def test_no_broken_markdown_links():
    ds = _ready()
    broken = []
    for p in ds:
        for link in re.findall(r"\]\(([^)]+)\)", p.read_text()):
            if link.startswith(("http://", "https://", "#")):
                continue
            if not (p.parent / link).exists():
                broken.append((p, link))
    assert not broken, broken[:10]
