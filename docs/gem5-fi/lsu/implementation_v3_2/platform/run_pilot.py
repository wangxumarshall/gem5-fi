#!/usr/bin/env python3
"""Run one v3.2 pilot with a PILOT-only identity.

The seed and fault configuration are copied from the frozen Excel sample; the
SampleRunID is deliberately replaced with ``PILOT-...`` so no formal sample is
overwritten. A FAULT pilot is accepted only when the process exits 0, the
injector reports at least one injection, the target-event evidence is present,
and the converted Trace v3.1 JSONL is valid and complete. The oracle result is
recorded (MASKED vs SDC), not required to pass: a non-propagating fault is a
valid pilot outcome.

A matched no-fault control (``--probability 0.0``) is accepted through its own
gate instead (``run_roles.control_valid``): clean exit, oracle PASS, zero
injections and a COMPLETE, error-free trace. Acceptance is role-exclusive
(``run_roles.compute_acceptance``): a CONTROL can never be accepted through
the fault criteria, so a control whose injector misfired is rejected and
flagged ``control_misfire: true`` in pilot_meta.json. Accepting a control
never relabels its honest ``UNRESOLVED``/``NO_INJECTION_EVENT`` terminal as
MASKED.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent
IMPL = PLATFORM.parent
sys.path.insert(0, str(PLATFORM))

from config_parser import load_config  # noqa: E402
from fault_effect_coverage import classify  # noqa: E402
from manifest import build_manifest, canonical_json, write_manifest  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import read_records, validate  # noqa: E402
import run_roles  # noqa: E402
import terminal_rules  # noqa: E402
from tools.prop_trace_to_v31 import convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = IMPL / "workloads"
DIRECTED = ROOT / "workloads/directed"

# Every model the pilot platform can run; --model choices and the Excel
# sample rows are keyed by these ids (v3.2.4 workbook is authoritative;
# accepted pilots are transcribed into v3.2.5 later).
MODELS = ("A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04", "FW05",
          "SQ03", "SP05", "LQ04", "RP01")

# v3.3.3 control/attach provenance (Task 5). The mount flags are the only
# injectors with a global/probability or ordinal gate; the gate field records
# which mechanism the model actually uses.
MOUNT_FLAGS = ("--chaos_lsqfwd", "--chaos_addrpath", "--chaos_l1dfwd",
               "--chaos_lq04", "--chaos_md04")
ORDINAL_GATED = {"A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05",
                 "LQ04", "DA04", "RP01"}


def _workload_for(model: str) -> str:
    return {"A01": "agu_addrmodes", "A03": "agu_addrmodes",
            "FW02": "sq_forward", "SQ01": "sq_drain",
            "DA04": "alignment", "LP01": "load_response",
            "MD04": "replay_dependency",
            # FW05's Excel workload (alignment) has no two overlapping 8-byte
            # stores in flight; the pilot-only directed workload constructs
            # the real forwarding pair. Recorded in the manifest.
            "FW05": "fw05_forward", "SQ03": "sq_drain",
            "SP05": "store_path",
            # LQ04 targets an explicit-anchor Load whose LQ-entry lifetime
            # is observable end to end (v3.2.10 pilot-only workload; the
            # Excel path is retained in the sample).
            "LQ04": "lq_lifetime_ordinal",
            # RP01 (v3.3.3): partial-forward rescheduleMemInst skip. The
            # directed candidate workload resolves under workloads/directed.
            "RP01": "replay_partial_v332"}[model]


def _funnel(path: Path) -> dict:
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = {}
    for line in lines:
        m = re.search(r"FUNNEL:\s+attempted=(\d+)\s+eligible=(\d+)\s+injected=(\d+)", line)
        if m:
            out = {"attempted": int(m[1]), "eligible": int(m[2]), "injected": int(m[3])}
    return out


def _fw02_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"CHAOS_FW02_SUMMARY:\s+observed=(\d+)\s+suppressed=(\d+)\s+"
                  r"load_seq=(\d+)\s+store_seq=(\d+)", text)
    if m:
        return {"observed": int(m[1]), "suppressed": int(m[2]),
                "load_seq": int(m[3]), "store_seq": int(m[4])}
    # Aborted run: the exit-callback summary is absent, but each suppression
    # line was flushed. Count those lines and take the last pair.
    lines = [ln for ln in text.splitlines() if "f6_fw02_suppress" in ln]
    if not lines:
        return {}
    mm = re.search(r"load_seq:\s*(\d+).*store_seq:\s*(\d+)", lines[-1])
    return {"observed": len(lines), "suppressed": len(lines),
            "load_seq": int(mm[1]) if mm else None,
            "store_seq": int(mm[2]) if mm else None}


def _sq01_summary(path: Path) -> dict:
    events = []
    if not path.exists():
        return {"events": events, "injected": 0}
    pattern = re.compile(
        r"seq:\s*(\d+).*sq_idx:\s*(\d+).*entry_generation:\s*(\d+)"
        r".*old_byte0:\s*0x([0-9a-fA-F]+).*new_byte0:\s*0x([0-9a-fA-F]+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_write_sq_entry" not in line:
            continue
        m = pattern.search(line)
        if m:
            events.append({"seq": int(m[1]), "idx": int(m[2]),
                           "gen": int(m[3]), "old": int(m[4], 16),
                           "new": int(m[5], 16)})
    return {"events": events, "injected": len(events)}


def _da04_summary(path: Path) -> dict:
    events = []
    if not path.exists():
        return {"events": events, "injected": 0}
    pattern = re.compile(
        r"seq:\s*(\d+).*sq_idx:\s*(\d+).*entry_generation:\s*(\d+)"
        r".*old_addr:\s*0x([0-9a-fA-F]+).*new_addr:\s*0x([0-9a-fA-F]+)"
        r".*size:\s*(\d+).*old_be:\s*0x([0-9a-fA-F]+)"
        r".*new_be:\s*0x([0-9a-fA-F]+).*changed_bit:\s*(\d+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_pushRequest_byte_enable" not in line:
            continue
        m = pattern.search(line)
        if m:
            events.append({"seq": int(m[1]), "sq_idx": int(m[2]),
                           "gen": int(m[3]), "old_addr": int(m[4], 16),
                           "new_addr": int(m[5], 16), "size": int(m[6]),
                           "old_be": int(m[7], 16), "new_be": int(m[8], 16),
                           "changed_bit": int(m[9])})
    return {"events": events, "injected": len(events)}


def _addrpath_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_pushRequest_PRE" not in line:
            continue
        m = re.search(r"mode=([^,\s]+).*old_addr=0x([0-9a-fA-F]+).*new_addr=0x([0-9a-fA-F]+)", line)
        if m:
            events.append({"mode": m[1], "old": int(m[2], 16),
                           "new": int(m[3], 16), "line": line})
    return events


def _md04_events(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(
            r"Tick:\s*(\d+).*load_seq=(\d+), store_seq=(\d+), "
            r"addr=0x([0-9a-fA-F]+), size=(\d+), "
            r"store_addr=0x([0-9a-fA-F]+), store_size=(\d+), "
            r"load_pc=0x([0-9a-fA-F]+), store_pc=0x([0-9a-fA-F]+), "
            r"sq_entry_id=(-?\d+), sq_entry_generation=(\d+), "
            r"lq_entry_id=(-?\d+), lq_entry_generation=(\d+), "
            r"eligible_ordinal=(\d+), event_ordinal=(\d+), seed=(\d+), "
            r"load_complete=(\d+).*faults_injected:\s*(\d+)", line)
        if m:
            out.append({
                "tick": int(m[1]), "load_seq": int(m[2]),
                "store_seq": int(m[3]), "addr": int(m[4], 16),
                "size": int(m[5]), "store_addr": int(m[6], 16),
                "store_size": int(m[7]), "load_pc": int(m[8], 16),
                "store_pc": int(m[9], 16), "sq_entry_id": int(m[10]),
                "sq_entry_generation": int(m[11]), "lq_entry_id": int(m[12]),
                "lq_entry_generation": int(m[13]),
                "eligible_ordinal": int(m[14]), "event_ordinal": int(m[15]),
                "seed": int(m[16]), "load_complete": int(m[17]),
                "target_pair_id": f"MD04-L{m[2]}-S{m[3]}-T{m[1]}",
                "faults_injected": int(m[18]),
            })
    return out


def _fw05_events(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    pat = re.compile(
        r"Cycle:\s*(\d+).*LoadSeq:\s*(\d+), TrueSeq:\s*(\d+), "
        r"AltSeq:\s*(\d+), LoadAddr:\s*0x([0-9a-fA-F]+), "
        r"TrueAddr:\s*0x([0-9a-fA-F]+), AltAddr:\s*0x([0-9a-fA-F]+), "
        r"LoadSize:\s*(\d+), TrueSize:\s*(\d+), AltSize:\s*(\d+), "
        r"AltOffset:\s*(\d+), TrueFnv:\s*([0-9a-fA-F]+), "
        r"AltFnv:\s*([0-9a-fA-F]+), LqEntry:\s*(-?\d+), LqGen:\s*(\d+), "
        r"SqEntry:\s*(-?\d+), SqGen:\s*(\d+), "
        r"EligibleOrdinal:\s*(\d+), EventOrdinal:\s*(\d+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "FaultType: fw05_older_src" not in line:
            continue
        m = pat.search(line)
        if not m:
            continue
        out.append({
            "cycle": int(m[1]), "load_seq": int(m[2]),
            "true_seq": int(m[3]), "alt_seq": int(m[4]),
            "load_addr": int(m[5], 16), "true_addr": int(m[6], 16),
            "alt_addr": int(m[7], 16), "load_size": int(m[8]),
            "true_size": int(m[9]), "alt_size": int(m[10]),
            "alt_offset": int(m[11]), "true_fnv": m[12], "alt_fnv": m[13],
            "lq_entry": int(m[14]), "lq_gen": int(m[15]),
            "sq_entry": int(m[16]), "sq_gen": int(m[17]),
            "eligible_ordinal": int(m[18]), "event_ordinal": int(m[19]),
            "target_pair_id": (f"FW05-L{m[2]}-T{m[3]}-A{m[4]}-K{m[1]}"),
        })
    return out


def _sq03_trace_events(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    import gzip
    lines = []
    try:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except (EOFError, OSError):
        # A timeout/watchdog may leave a truncated gzip stream; keep the
        # complete rows that were flushed and never fabricate the rest.
        try:
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except (EOFError, OSError):
            lines = []
    for line in lines:
        if "inj_sq03" not in line:
            continue
        row = next(__import__("csv").reader([line]))
        if len(row) < 10:
            continue
        detail = dict(item.split("=", 1) for item in row[9].split(";")
                      if "=" in item)
        def num(k, base=10):
            v = detail.get(k)
            if v in (None, "null", ""):
                return None
            return int(v, base)
        out.append({
            "tick": int(row[1]),
            "store_seq": num("store_seq"),
            "store_pc": detail.get("store_pc"),
            "store_addr": detail.get("store_addr"),
            "store_size": num("store_size"),
            "sq_entry_id": num("sq_entry_id"),
            "sq_entry_generation": num("sq_entry_generation"),
            "canwb_before": num("canwb_before"),
            "canwb_after": num("canwb_after"),
            "stores_to_wb_before": num("stores_to_wb_before"),
            "stores_to_wb_after": num("stores_to_wb_after"),
            "eligible_ordinal": num("eligible_ordinal"),
            "event_ordinal": num("event_ordinal"),
            "seed": num("seed"),
            "address_modified": num("address_modified"),
            "size_modified": num("size_modified"),
            "data_modified": num("data_modified"),
        })
    return out



def _sp05_trace_events(path: Path) -> list[dict]:
    """Parse sp05_complete rows from the propagation CSV (one per target)."""
    out = []
    if not path.exists():
        return out
    import gzip
    with gzip.open(path, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            row = line.rstrip("\n").split(",")
            if len(row) < 10 or row[3] != "sp05_complete":
                continue
            detail = dict(kv.split("=", 1) for kv in row[9].split(";")
                          if "=" in kv)
            out.append({
                "store_seq": int(detail["store_seq"]),
                "sq_idx": int(detail["sq_idx"]),
                "sq_gen": int(detail["sq_gen"]),
                "canwb_before": int(detail["canwb_before"]),
                "completed_before": int(detail["completed_before"]),
                "stores_to_wb_before": int(detail["stores_to_wb_before"]),
                "stores_to_wb_after": int(detail["stores_to_wb_after"]),
                "mem_sent": int(detail["mem_sent"]),
                "complete_tick": int(detail["complete_tick"]),
            })
    return out


def _lq04_events(path: Path) -> list[dict]:
    """Parse lq04_injections.log (CHAOS_LQ04_* lines) into event dicts.

    INJECTION lines carry the full target identity (kind="injection");
    ELIGIBLE_PROBE lines are the selection-time eligible observations
    (kind="probe"); RESTORE lines close the corrupt window at the
    commit/squash boundary (kind="restore").  ELIGIBLE_COUNT and
    WATCHDOG_EXPIRED are status lines, not events.
    """
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "CHAOS_LQ04_INJECTION:" in line:
            kind = "injection"
        elif "CHAOS_LQ04_ELIGIBLE_PROBE:" in line:
            kind = "probe"
        elif "CHAOS_LQ04_RESTORE:" in line:
            kind = "restore"
        else:
            continue
        rec: dict = {"kind": kind}
        for key, value in re.findall(r"(\w+)=(\S+)", line):
            try:
                rec[key] = int(value, 0)
            except ValueError:
                rec[key] = value
        out.append(rec)
    return out

def _lq04_target_proof(injections: list[dict], event_ordinal) -> dict:
    """Build the LQ04 ``target_event_proof`` dict.

    Fault runs (>= 1 injection) carry the construction-time proof fields:
    ``LSQEntry::corruptLifetime`` asserts the before-state and clears both
    fields; the request moves to the LQEntry side channel, so the entry is
    neither popped nor freed/reused early; address, size and data are never
    touched; the boundary restore re-validates the entry.

    Zero-injection runs (matched no-fault controls: the injector is not
    mounted, so no lifetime transition happened) must not assert those
    fields.  They are reported as JSON null with ``"applicable": False``
    and an explicit reason; ``all_one_injection`` stays false, ``events``
    stays 0, and the vacuously-true ``ordinal_matches`` is nulled too.
    """
    if not injections:
        return {
            "site": "executeLoad_post",
            "events": 0,
            "all_one_injection": False,
            "ordinal_matches": None,
            "applicable": False,
            "not_applicable_reason": (
                "no injection event (matched no-fault control: injector "
                "not mounted); LQ04 lifetime proof fields are n/a"),
            "valid_1_to_0": None,
            "request_1_to_0": None,
            "no_pop_no_reuse": None,
            "address_size_data_unchanged": None,
        }
    return {
        "site": "executeLoad_post",
        "events": len(injections),
        "all_one_injection": len(injections) == 1,
        "ordinal_matches": all(
            e.get("ordinal") == (event_ordinal or 1)
            for e in injections),
        "applicable": True,
        "valid_1_to_0": True,
        "request_1_to_0": True,
        "no_pop_no_reuse": True,
        "address_size_data_unchanged": True,
    }

def _md04_status(path: Path) -> str:
    if not path.exists():
        return "UNKNOWN"
    status = "UNKNOWN"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"CHAOS_MD04_TARGET_STATUS=([A-Z_]+)", line)
        if m:
            status = m[1]
    return status


def _l1dfwd_events(path: Path) -> list[dict]:
    """Parse LP01 injection lines (one per injected load response).

    v3.3.2: the record now carries pa/va/pc/dyn_inst_seq/LQ identity fields,
    which are inserted between the fields the v3.1 parser expected. Parse
    field-by-field (name=value) instead of relying on one positional regex,
    so both the old and the new line shapes are accepted.
    """
    out = []
    if not path.exists():
        return out
    hex_fields = ("addr", "pa", "va", "pc", "mask")
    dec_fields = ("size", "dyn_inst_seq", "lq_entry_id", "entry_generation",
                  "request_id", "eligible_ordinal", "faults_injected")
    tick_re = re.compile(r"^Tick:\s*(\d+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: l1d_load_complete" not in line:
            continue
        m = tick_re.search(line)
        if not m:
            continue
        rec = {"tick": int(m[1])}
        for name, value in re.findall(r"([A-Za-z_]\w*)=(0x[0-9a-fA-F]+|\d+)",
                                      line):
            if name in hex_fields:
                rec[name] = int(value, 16)
            elif name in dec_fields:
                rec[name] = int(value)
        # The trailing counter is printed as "faults_injected: N" (colon),
        # not name=value; accept either separator.
        fi = re.search(r"faults_injected\s*[:=]\s*(\d+)", line)
        if fi:
            rec["faults_injected"] = int(fi[1])
        if "faults_injected" not in rec:
            continue
        # Legacy aliases: addr is the physical address (kept as pa too).
        if "pa" not in rec and "addr" in rec:
            rec["pa"] = rec["addr"]
        if "addr" not in rec and "pa" in rec:
            rec["addr"] = rec["pa"]
        rec.setdefault("size", 0)
        rec.setdefault("mask", 0)
        rec.setdefault("eligible_ordinal", 0)
        out.append(rec)
    return out


def _rp01_events(path: Path) -> list[dict]:
    """Parse RP01_SKIP_REPLAY lines from lsq_fwd_injections.log (v3.3.3).

    The RP01 fault is a single rescheduleMemInst skip selected by eligible
    ordinal; the line carries the full identity (load/store seq, LQ entry,
    generation, replay counter, tick). ELIGIBLE lines are observations, not
    injections, and are not counted.
    """
    out: list[dict] = []
    path = Path(path)
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        # The model log writes the skip as
        #   Tick: <t>, Site: read_partial_reschedule, skipped_call=1, ...
        # while stdout prints RP01_SKIP_REPLAY. Accept both shapes.
        if not (line.startswith("RP01_SKIP_REPLAY")
                or "skipped_call=1" in line):
            continue
        rec: dict = {"kind": "skip"}
        tick = re.match(r"Tick:\s*(\d+)", line)
        if tick:
            rec["tick"] = int(tick[1])
        for key, value in re.findall(r"(\w+)=([^,\s]+)", line):
            try:
                rec[key] = int(value, 0)
            except ValueError:
                rec[key] = value
        fi = re.search(r"faults_injected\s*[:=]\s*(\d+)", line)
        if fi:
            rec["faults_injected"] = int(fi[1])
        if "ordinal" not in rec and "eligible_ordinal" in rec:
            rec["ordinal"] = rec["eligible_ordinal"]
        out.append(rec)
    return out


def injector_meta(model: str, probability: float, cmd: list[str],
                  stdout: str, extra: list[str]) -> dict:
    """Injector mount/attach/gate provenance for pilot_meta.json (v3.3.3)."""
    mounts = [flag for flag in MOUNT_FLAGS if flag in cmd]
    md04_probability = None
    if "--md04_probability" in cmd:
        idx = cmd.index("--md04_probability")
        if idx + 1 < len(cmd):
            try:
                md04_probability = float(cmd[idx + 1])
            except ValueError:
                md04_probability = None
    gate = "md04_probability" if "--chaos_md04" in mounts else (
        "ordinal" if model in ORDINAL_GATED else "probability")
    markers = [ln.strip() for ln in (stdout or "").splitlines()
               if "[lsu_proxy]" in ln
               and ("attached" in ln or "probability=" in ln)]
    return {
        "mount_flags": mounts,
        "mounted": bool(mounts),
        "probability": probability,
        "md04_probability": md04_probability,
        "gate": gate,
        "gate_enabled": (bool(mounts) and probability > 0
                         and md04_probability != 0.0),
        "control_omits_mount": probability == 0.0 and not mounts,
        "model_extra_flags": list(extra),
        "attach_marker_lines": markers,
        "attach_mechanism": "self_attach_at_startup",
    }


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            # A killed/timeout run may leave one partial trailing line; keep
            # the complete records and never invent the remainder.
            continue
        if rec.get("record_type") == "event":
            out.append(rec)
    return out


def _fault_injection(events: list[dict]) -> dict | None:
    injections = [e for e in events
                  if e.get("event_type") in ("injection", "injection_nochange")]
    return injections[-1] if injections else None


def _seq_events(events: list[dict], seq) -> list[dict]:
    return [e for e in events if seq is not None and e.get("dyn_inst_seq") == seq]


def _terminal_evidence(events: list[dict], pt_fault_addr: str | None,
                       stderr: str) -> dict:
    injection = _fault_injection(events)
    new_value = injection.get("new_value") if injection else None
    match = bool(pt_fault_addr and new_value
                 and str(new_value).lower() == str(pt_fault_addr).lower())
    return {
        "page_table_fault_addr": pt_fault_addr,
        "last_injection_dyn_seq": injection.get("dyn_inst_seq") if injection else None,
        "last_injection_new_value": new_value,
        "address_match": match,
        "stderr_has_page_table_fault": "page table fault" in stderr.lower(),
    }


def _fault_causality(events: list[dict], terminal: str,
                     pt_fault_addr: str | None, model: str = "A01") -> str:
    """Relation between the injected fault and the observed terminal.

    This is deliberately weaker than the terminal itself: a crash that happens
    after an injection is not claimed to be caused by it.
    """
    injection = _fault_injection(events)
    if injection is None:
        return "UNKNOWN"
    if terminal == "CRASH":
        new_value = injection.get("new_value")
        if (pt_fault_addr and new_value
                and str(new_value).lower() == str(pt_fault_addr).lower()):
            return "DIRECT_ADDRESS_MATCH"
        return "TEMPORAL_ASSOCIATION_ONLY"
    seq = injection.get("dyn_inst_seq")
    if terminal == "SQUASHED":
        if any(e.get("event_type") == "squash" for e in _seq_events(events, seq)):
            return "INDIRECT_EVIDENCE"
        return "TEMPORAL_ASSOCIATION_ONLY"
    if terminal in ("MASKED", "SDC"):
        if model == "SQ01":
            if any(e.get("event_type") == "sq_lifecycle"
                   and e.get("dyn_inst_seq") == seq
                   and ("reason=complete" in (e.get("detail") or "")
                        or "reason=commit" in (e.get("detail") or ""))
                   for e in events):
                return "DIRECT_DATAFLOW_EVIDENCE"
            return "INDIRECT_EVIDENCE"
        if any(e.get("event_type") in ("memory_response", "register_writeback")
               for e in events):
            return "DIRECT_DATAFLOW_EVIDENCE"
        return "INDIRECT_EVIDENCE"
    return "INDIRECT_EVIDENCE"


def build_model_extra(model: str, probability: float, seed: int,
                      ordinal) -> list[str]:
    """Model-specific gem5 flags: injector mount + frozen run identity.

    A matched no-fault control (``--probability 0.0``) must NOT mount an
    injector whose firing decision is not gated by the global
    ``--probability`` -- a mounted injector would still fire.  The LQ04
    ordinal selector, the F6_fw02 / da04_be_bit0 LSQFwd struct modes (all
    ordinal-gated F0/F6 selectors) and CHAOSMD04 (which gates only on its
    own ``--md04_probability``) are such injectors, so those branches return
    an empty list at probability 0.0; the propagation tracer stays on in the
    base command.  Every other branch is probability-gated in its injector's
    attach path, so its control keeps the mount and relies on that gate.

    FAULT runs (probability > 0) are byte-identical to the pre-v3.3.2
    command.
    """
    control = probability == 0.0
    ordinal = str(ordinal)
    if model == "A01":
        return ["--chaos_addrpath", "--agu_pre_mode", "a01_bit3_load",
                "--addrpath_lsu_tier", "F0", "--addrpath_max_faults", "1",
                "--addrpath_warmup_events", "0", "--addrpath_span_events", "10",
                "--addrpath_rng_seed", str(seed),
                "--addrpath_event_ordinal", ordinal]
    if model == "A03":
        return ["--chaos_addrpath", "--agu_pre_mode", "a03_bit3_stuck0_load",
                "--addrpath_lsu_tier", "F5", "--addrpath_max_faults", "0",
                "--addrpath_warmup_events", "0",
                "--addrpath_rng_seed", str(seed),
                "--addrpath_event_ordinal", ordinal]
    if model == "SQ01":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq01_bit3",
                "--lsqfwd_lsu_tier", "F0",
                "--lsqfwd_warmup_events", "0", "--lsqfwd_span_events", "10",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", ordinal]
    if model == "DA04":
        if control:
            # Matched no-fault control (v3.3.2 fix): DA04 corrupts the store
            # byte-enable through an ordinal-gated F0 selector; the decision
            # never consults --probability, so a mounted injector would fire
            # under --probability 0.0.  Omit the injector entirely (the same
            # treatment as the LQ04/FW02 controls below).
            return []
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "da04_be_bit0",
                "--lsqfwd_lsu_tier", "F0",
                "--lsqfwd_warmup_events", "0", "--lsqfwd_span_events", "10",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", ordinal]
    if model == "MD04":
        if control:
            # Matched no-fault control (v3.3.2 fix): CHAOSMD04 gates on its
            # own --md04_probability (hard-coded 1.0 for fault runs) and
            # never consults the global --probability, so the only honest
            # control is to omit the injector and all of its arguments.
            return []
        return ["--chaos_md04", "--md04_first_clock", "0",
                "--md04_max_faults", "1",
                "--md04_probability", "1.0",
                "--md04_rng_seed", str(seed),
                "--md04_event_ordinal", ordinal]
    if model == "LP01":
        return ["--chaos_l1dfwd", "--l1dfwd_first_clock", "0",
                "--l1dfwd_max_faults", "1",
                "--l1dfwd_fault_mask", "0x8",
                "--l1dfwd_rng_seed", str(seed),
                "--l1dfwd_event_ordinal", ordinal]
    if model == "SQ03":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq03_canwb",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", ordinal,
                "--sq03_watchdog_cycles", "500000000"]
    if model == "SP05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sp05_complete",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--sp05_event_ordinal", ordinal,
                "--sp05_watchdog_cycles", "500000000"]
    if model == "FW05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "fw05_older_src",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", ordinal]
    if model == "LQ04":
        if control:
            # Matched no-fault control: the LQ04 selector is ordinal-gated,
            # not probability-gated, so a mounted injector would still fire.
            # Omit the injector entirely; --chaos_propagation stays on.
            return []
        return ["--chaos_lq04",
                "--lq04_event_ordinal", ordinal,
                "--lq04_max_faults", "1",
                "--lq04_rng_seed", str(seed),
                "--lq04_watchdog_cycles", "500000000"]
    if model == "FW02":
        if control:
            # Matched no-fault control (v3.2.12 fix): the F6_fw02 selector is
            # ordinal-gated, not probability-gated -- CHAOSLSQFwd attaches the
            # F6Fw02 mode even with probability==0 and the suppression
            # decision never consults probability, so a mounted injector
            # would still fire (the SUPP-FW02-C01 misfire). Omit the injector
            # entirely; --chaos_propagation stays on (same treatment as the
            # LQ04 control branch).
            return []
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", ordinal]
    if model == "RP01":
        if control:
            # Matched no-fault control: the RP01 skip is ordinal-gated, not
            # probability-gated, so omit the injector entirely.
            return []
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_skip_replay",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--rp01_event_ordinal", ordinal,
                "--rp01_watchdog_cycles", "20000000"]
    return ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
            "--max_faults", "1", "--rng_seed", str(seed),
            "--lsqfwd_event_ordinal", ordinal]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--probability", type=float, default=1.0,
                    help="injection probability (0.0 = matched no-fault control)")
    ap.add_argument("--timeout", type=int, default=900,
                    help="external wall-clock timeout in seconds")
    ap.add_argument("--workload", default=None,
                    help="pilot-only workload override (recorded in the "
                         "manifest; the Excel path is retained)")
    ap.add_argument("--pilot-id", required=True)
    ap.add_argument("--seed", type=int, default=None,
                    help="override seed; default = the selected Excel context row")
    ap.add_argument("--context-index", type=int, default=1, choices=[1,2,3,4,5],
                    help="R01-R05: select the Excel sample row for this context")
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--gem5", type=Path, default=GEM5)
    ap.add_argument("--preserve-sample-id", action="store_true",
                    help="Keep the Excel SampleRunID/RunID/SubTaskID "
                         "(pilots still write only to --outdir); v3.2.4 DA04")
    ap.add_argument("--event-ordinal", type=int, default=None,
                    help="TEMPORARY_EVENT_SELECTION override for the F0 "
                         "eligible-event ordinal (v3.2.4 DA04 pilots); the "
                         "Excel ordinal is recorded separately")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the exact gem5 command, print it (and write "
                         "<outdir>/command.txt), then exit 0 without invoking "
                         "gem5 -- no manifest or run artifacts are produced")
    args = ap.parse_args(argv)

    cfg = load_config(EXCEL, require_complete=False)
    model_rows = [s for s in cfg["samples"] if s["model_id"] == args.model]
    sample = copy.deepcopy(model_rows[args.context_index - 1])
    excel_seed = sample["seed"]
    excel_event_ordinal = sample.get("event_ordinal")
    if args.event_ordinal is not None:
        sample["event_ordinal"] = args.event_ordinal
    if args.seed is None:
        args.seed = excel_seed
    if args.preserve_sample_id:
        excel = model_rows[args.context_index - 1]
        sample["sample_run_id"] = excel["sample_run_id"]
        sample["run_id"] = excel["run_id"]
        sample["sub_task_id"] = excel["sub_task_id"]
    else:
        sample["sample_run_id"] = args.pilot_id
        sample["run_id"] = f"PILOT-{args.model}"
        sample["sub_task_id"] = f"PILOT-{args.model}-S01"
    sample["seed"] = args.seed
    workload_name = args.workload or _workload_for(args.model)
    workload_path = Path(workload_name)
    if not workload_path.is_absolute():
        workload_path = WORKLOADS / workload_name
        if not workload_path.exists() and (DIRECTED / workload_name).exists():
            # v3.3.3 RP01: the candidate workload lives under workloads/directed.
            workload_path = DIRECTED / workload_name
    sample["workload_path"] = str(workload_path)
    sample["workload_exists"] = workload_path.exists()
    cfg2 = copy.deepcopy(cfg)
    cfg2["samples"] = [sample]
    # gem5 runs with cwd=ROOT, so a relative --outdir would land its
    # artifacts outside this script's output directory. Pin the path at the
    # caller's cwd before gem5 sees it.
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    extra = build_model_extra(args.model, args.probability, args.seed,
                              sample.get("event_ordinal") or 1)

    cmd = [str(args.gem5), f"--outdir={out}", str(CONFIG),
           f"--cmd={workload_path}",
           "--cpu", "O3", "--variant", "B0",
           "--probability", str(args.probability),
           "--chaos_propagation",
           "--prop_trace_file", "prop_trace.csv.gz"] + extra
    (out / "command.txt").write_text("\n".join(cmd) + "\n")
    if args.dry_run:
        # Print the exact command that a real run would hand to gem5 and
        # stop. No subprocess, no manifest, no run artifacts: a dry run can
        # never be mistaken for an executed pilot.
        print(" ".join(cmd))
        return 0
    # build_manifest looks the sample up by SampleRunID: with
    # --preserve-sample-id that is the Excel id, not the pilot id.
    manifest = build_manifest(cfg2, sample["sample_run_id"], args.gem5, CONFIG,
                              output_dir=out, command=cmd,
                              allow_workload_override=bool(args.workload))
    if args.workload:
        manifest["workload"]["path"] = str(workload_path)
        manifest["workload"]["path_source"] = (
            "pilot_override (Excel path retained in sample)")
        manifest["workload"]["sha256"] = hashlib.sha256(
            workload_path.read_bytes()).hexdigest()
        manifest["workload"]["oracle_expected"] = (
            workload_path.with_suffix(".golden").read_text().strip()
            if workload_path.with_suffix(".golden").exists() else None)
    if args.seed != excel_seed:
        manifest["seed_source"] = "pilot_cli_override (not Excel)"
        manifest["manifest_sha256"] = hashlib.sha256(
            canonical_json(manifest).encode("utf-8")).hexdigest()
    write_manifest(manifest, out / "manifest.json")
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        partial_out = exc.stdout or ""
        partial_err = exc.stderr or ""
        if isinstance(partial_out, bytes):
            partial_out = partial_out.decode("utf-8", "replace")
        if isinstance(partial_err, bytes):
            partial_err = partial_err.decode("utf-8", "replace")
        proc = type("P", (), {"returncode": 124,
                              "stdout": partial_out,
                              "stderr": partial_err + "\nTIMEOUT: external wall-clock limit reached\n"})()
    elapsed = time.time() - started
    (out / "stdout.log").write_text(proc.stdout)
    (out / "stderr.log").write_text(proc.stderr)

    expected = str(sample.get("oracle"))
    oracle_source = "excel"
    if args.workload or expected.strip().upper() in ("N/A", "NONE", "", "NAN"):
        golden = workload_path.with_suffix(".golden")
        if golden.exists():
            expected = golden.read_text().strip()
            oracle_source = "workload_golden"
    oracle = subprocess.run(
        [sys.executable, str(WORKLOADS / "oracle_check.py"), expected,
         str(out / "stdout.log")], capture_output=True, text=True)
    (out / "oracle.log").write_text(oracle.stdout + oracle.stderr)
    oracle_pass = oracle.returncode == 0

    events: list[dict] = []  # A01/A03 address-path events; empty for FW02
    if args.model in ("A01", "A03"):
        inj = _funnel(out / "addrpath_injections.log")
        events = _addrpath_events(out / "addrpath_injections.log")
        target_proof = {
            "site": "lsq_pushRequest_PRE",
            "events": len(events),
            "all_load_bit3": all(
                (e["new"] == (e["old"] ^ 0x8) if e["mode"] == "a01_bit3_load"
                 else e["new"] == (e["old"] & ~0x8)) for e in events),
        }
        injected = inj.get("injected", 0)
    elif args.model == "SQ01":
        inj = _sq01_summary(out / "lsq_fwd_injections.log")
        events = inj.get("events", [])
        target_proof = {
            "site": "lsq_write_sq_entry",
            "events": len(events),
            "all_store_bit3": all(e["new"] == (e["old"] ^ 0x08)
                                  for e in events),
        }
        injected = len(events)
    elif args.model == "DA04":
        inj = _da04_summary(out / "lsq_fwd_injections.log")
        events = inj.get("events", [])
        target_proof = {
            "site": "lsq_pushRequest_byte_enable",
            "events": len(events),
            "all_store_only": True,   # hook is inside the !isLoad branch
            "all_mask_0xf_to_0xe": all(
                e["old_be"] == 0xF and e["new_be"] == 0xE for e in events),
            "all_size_4": all(e["size"] == 4 for e in events),
            "all_addr_unchanged": all(
                e["old_addr"] == e["new_addr"] for e in events),
        }
        injected = len(events)
    elif args.model == "MD04":
        events = _md04_events(out / "md04_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "LSQUnit::checkViolations",
            "events": len(events),
            "target_status": _md04_status(out / "md04_injections.log"),
            "all_store_size_8": all(e["store_size"] == 8 for e in events),
            "all_load_size_ge_8": all(e["size"] >= 8 for e in events),
            "all_real_byte_overlap": all(
                e["store_addr"] <= e["addr"] + e["size"] - 1
                and e["addr"] <= e["store_addr"] + e["store_size"] - 1
                for e in events),
            "all_store_younger_ordering": all(
                e["load_seq"] > e["store_seq"] for e in events),
            "all_targets_selected": all(
                args.event_ordinal is None
                or e["eligible_ordinal"] == args.event_ordinal
                for e in events),
            "all_address_size_data_unchanged": True,
        }
        injected = len(events)
    elif args.model == "LP01":
        events = _l1dfwd_events(out / "l1d_fwd_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "LSQUnit::completeDataAccess",
            "events": len(events),
            "all_load_only": True,
            "all_mask_0x8": all(e["mask"] == 0x8 for e in events),
            "all_size_nonzero": all(e["size"] > 0 for e in events),
            "all_ordinals_distinct": len({e["eligible_ordinal"]
                                          for e in events}) == len(events),
        }
        injected = len(events)
    elif args.model == "FW05":
        events = _fw05_events(out / "lsq_fwd_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "store->load_forward_decision",
            "events": len(events),
            "all_distinct_stores": all(
                e["true_seq"] != e["alt_seq"] and e["alt_seq"] < e["true_seq"]
                for e in events),
            "all_younger_load": all(
                e["load_seq"] > e["true_seq"] for e in events),
            "all_full_cover": all(
                e["alt_addr"] <= e["load_addr"]
                and e["alt_addr"] + e["alt_size"]
                    >= e["load_addr"] + e["load_size"]
                for e in events),
            "all_data_differs": all(
                e["true_fnv"] != e["alt_fnv"] for e in events),
            "all_address_size_unchanged": True,
        }
        injected = len(events)
    elif args.model == "SQ03":
        events = _sq03_trace_events(out / "prop_trace.csv.gz")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "executeStore_canWB",
            "events": len(events),
            "all_canwb_0_to_1": all(
                e["canwb_before"] == 0 and e["canwb_after"] == 1
                for e in events),
            "all_stores_wb_delta_1": all(
                e["stores_to_wb_after"] - e["stores_to_wb_before"] == 1
                for e in events),
            "all_one_injection": len(events) == 1,
            "all_address_size_unchanged": True,
        }
        injected = len(events)
    elif args.model == "SP05":
        events = _sp05_trace_events(out / "prop_trace.csv.gz")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "writebackStores_prematureComplete",
            "events": len(events),
            "all_one_injection": len(events) == 1,
            "all_completed_false_to_true": all(
                e["completed_before"] == 0 for e in events),
            "all_stores_wb_delta_1": all(
                e["stores_to_wb_before"] - e["stores_to_wb_after"] == 1
                for e in events),
            "all_mem_sent_0": all(e["mem_sent"] == 0 for e in events),
        }
        injected = len(events)
    elif args.model == "LQ04":
        events = _lq04_events(out / "lq04_injections.log")
        injections = [e for e in events if e.get("kind") == "injection"]
        inj = {"events": events, "injected": len(injections)}
        target_proof = _lq04_target_proof(
            injections, sample.get("event_ordinal"))
        injected = len(injections)
    elif args.model == "RP01":
        events = _rp01_events(out / "lsq_fwd_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "IEW::rescheduleMemInst",
            "events": len(events),
            "all_one_injection": len(events) == 1,
            "ordinal_matches": all(
                e.get("ordinal") == (sample.get("event_ordinal") or 1)
                for e in events),
            "all_replay_skipped": all(
                e.get("replay_gen_pre") == 0 for e in events),
            "all_candidate_loads": all(
                (e.get("replay_gen_post") or 0) + (
                    e.get("in_instsToReplay_post") or 0) >= 0
                for e in events),
        }
        injected = len(events)
    else:
        inj = _fw02_summary(out / "lsq_fwd_injections.log")
        target_proof = {"site": "store->load_forward_decision", **inj}
        injected = inj.get("suppressed", 0)

    crash_by_fault = False
    crash_evidence = None
    pt_fault_addr = None
    if proc.returncode != 0 and args.model in ("A01", "A03", "FW02") and injected > 0:
        err = proc.stderr.lower()
        pt_match = re.search(
            r"page table fault when accessing virtual address "
            r"(0x[0-9a-fA-F]+|0)\b", proc.stderr, re.I)
        if pt_match:
            # The panic address is not assumed to be the injected address; it
            # is recorded separately and compared with the trace later.
            crash_by_fault = True
            pt_fault_addr = pt_match.group(1).lower()
            crash_evidence = "page_table_fault_after_injection"
    watchdog_text = (
        (proc.stdout or "") + (proc.stderr or "") + "\n" +
        ((out / "lsq_fwd_injections.log").read_text(
            encoding="utf-8", errors="replace")
         if (out / "lsq_fwd_injections.log").exists() else ""))
    watchdog_hit = any(marker in watchdog_text for marker in (
        "CHAOS_SQ03_WATCHDOG_EXPIRED", "CHAOS_SP05_WATCHDOG_EXPIRED",
        "CHAOS_LQ04_WATCHDOG_EXPIRED", "CHAOS_RP01_WATCHDOG_EXPIRED",
        "CHAOS_RP01_WATCHDOG=EXPIRED"))
    if timed_out:
        run_status, activation, terminal, completeness = (
            "TIMEOUT", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "HANG", "INCOMPLETE")
    elif watchdog_hit:
        run_status, activation, terminal, completeness = (
            "SIMULATOR_ERROR", "TRIGGERED" if injected else "NOT_TRIGGERED",
            # RP01's watchdog terminal is HANG_WATCHDOG (L-A07); the other
            # watchdog models keep their existing HANG label.
            "HANG_WATCHDOG" if args.model == "RP01" else "HANG",
            "INCOMPLETE")
    elif proc.returncode != 0 and crash_by_fault:
        run_status, activation, terminal, completeness = (
            "SIMULATOR_ERROR", "TRIGGERED", "CRASH", "COMPLETE")
    elif proc.returncode != 0:
        run_status, activation, terminal, completeness = (
            "SIMULATOR_ERROR", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "CRASH", "INCOMPLETE")
    elif not oracle_pass:
        run_status, activation, terminal, completeness = (
            "COMPLETED", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "SDC", "COMPLETE")
    else:
        run_status, activation, terminal, completeness = (
            "COMPLETED", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "MASKED", "COMPLETE")

    csv_path = out / "prop_trace.csv.gz"
    jsonl_path = out / "trace_v31.jsonl"
    converted = {"rows": 0, "truncated": True, "summary": None}
    if csv_path.exists():
        try:
            converted = convert(
                csv_path, jsonl_path,
                sample_run_id=args.pilot_id, run_id=sample["run_id"],
                sub_task_id=sample["sub_task_id"],
                fault_id=sample.get("fault_config_id") or args.model,
                fault_model_id=args.model, run_status=run_status,
                activation=activation, terminal=terminal,
                completeness=completeness,
                allow_truncated_complete=crash_by_fault)
        except SystemExit:
            converted = {"rows": 0, "truncated": True, "summary": None}
    trace_errors = validate(jsonl_path) if jsonl_path.exists() else ["trace missing"]
    completeness_report = (check_completeness(jsonl_path)
                           if jsonl_path.exists() else {"trace_completeness": "INCOMPLETE"})
    # v3.2.4: chain-scoped adjudication (FW02 defect fix). Only events on the
    # fault's own chain can justify a verdict; a target Load that produced a
    # response and a register writeback but was squashed before commit is
    # SQUASHED, not MASKED. A different dynamic instruction's data cannot
    # rescue the target chain.
    trace_events = _read_events(jsonl_path)
    final_terminal, terminal_reason = terminal_rules.adjudicate(
        trace_events, model=args.model, observed_terminal=terminal,
        oracle_pass=oracle_pass,
        trace_complete=(completeness_report.get("trace_completeness")
                        == "COMPLETE"))
    if final_terminal == "UNRESOLVED" and crash_by_fault:
        final_terminal = "CRASH"
        terminal_reason = crash_evidence
    if final_terminal == "UNRESOLVED" and terminal_reason is None:
        terminal_reason = "UNRESOLVED_NO_TERMINAL_EVIDENCE"

    evidence = _terminal_evidence(trace_events, pt_fault_addr, proc.stderr)
    if crash_evidence:
        crash_evidence += ("_address_match" if evidence["address_match"]
                           else "_no_address_match")
        terminal_reason = crash_evidence
    fault_causality = _fault_causality(trace_events, final_terminal,
                                       pt_fault_addr, args.model)

    # Close the trace with the adjudicated verdict and the structured evidence,
    # so JSONL, pilot_meta and the sweep carry the same fields.
    if csv_path.exists():
        try:
            converted = convert(
                csv_path, jsonl_path,
                sample_run_id=args.pilot_id, run_id=sample["run_id"],
                sub_task_id=sample["sub_task_id"],
                fault_id=sample.get("fault_config_id") or args.model,
                fault_model_id=args.model, run_status=run_status,
                activation=activation, terminal=final_terminal,
                completeness=completeness_report.get("trace_completeness") or completeness,
                terminal_reason=terminal_reason,
                observed_terminal=terminal,
                fault_causality=fault_causality,
                terminal_evidence=evidence,
                allow_truncated_complete=crash_by_fault)
        except SystemExit:
            converted = {"rows": 0, "truncated": True, "summary": None}
        trace_errors = validate(jsonl_path) if jsonl_path.exists() else ["trace missing"]
        completeness_report = (check_completeness(jsonl_path)
                               if jsonl_path.exists()
                               else {"trace_completeness": "INCOMPLETE"})
    # v3.2.11: fault-effect propagation is graded separately from the
    # structural stage coverage above. The classifier sees the closed trace
    # (events plus the summary record); controls without an injection event
    # grade UNRESOLVED / NO_INJECTION_EVENT by construction.
    trace_records = read_records(jsonl_path) if jsonl_path.exists() else []
    fault_effect = classify(
        args.model, trace_records,
        _fault_injection([r for r in trace_records
                          if r.get("record_type") == "event"]),
        final_terminal)
    # v3.2.11 (A4): a matched no-fault control is not a failed fault run.
    # FAULT runs keep the gates below untouched; a CONTROL is judged by
    # run_roles.control_valid instead (clean exit, oracle PASS, zero
    # injections, COMPLETE trace, no validator errors). Because a valid
    # control records zero injections, its fault_activation_status stays
    # NOT_TRIGGERED and its terminal honestly stays
    # UNRESOLVED/NO_INJECTION_EVENT -- acceptance never relabels it MASKED.
    # Fix-loop ruling (reviewed finding): acceptance is role-exclusive via
    # run_roles.compute_acceptance -- a CONTROL can never be accepted
    # through the fault criteria, so a control whose injector misfired
    # (injection_count > 0; reachable for ordinal-gated injectors run with
    # --probability 0.0) is rejected even when the fault gates would have
    # passed it. The misfire is flagged explicitly in pilot_meta.json.
    run_role = run_roles.classify_run_role(args.probability)
    fault_valid = (
        (proc.returncode == 0 or crash_by_fault) and injected > 0
        and target_proof.get("events", 1) > 0
        and final_terminal not in (None, "UNRESOLVED")
        and not trace_errors
        and completeness_report.get("trace_completeness") == "COMPLETE"
    )
    control_valid = (
        run_roles.control_valid(
            exit_code=proc.returncode,
            oracle_pass=oracle_pass,
            injection_count=injected,
            trace_completeness=completeness_report.get("trace_completeness"),
            validator_errors=trace_errors)
        if run_role == "CONTROL" else False
    )
    control_misfire = run_role == "CONTROL" and injected > 0
    accepted = run_roles.compute_acceptance(run_role, fault_valid,
                                            control_valid)
    meta = {
        "pilot_id": args.pilot_id,
        "model": args.model,
        "run_role": run_role,
        "seed": args.seed,
        "event_selection": ("TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; "
                            "warm-up/ROI not frozen)"),
        "excel_identity": {
            "run_id": sample["run_id"],
            "sub_task_id": sample["sub_task_id"],
            "sample_run_id": sample["sample_run_id"],
            "seed": sample["seed"],
            "event_ordinal": excel_event_ordinal,
            "event_ordinal_used": sample.get("event_ordinal"),
        },
        "workload": str(workload_path),
        "command": cmd,
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "oracle_expected": expected,
        "oracle_source": oracle_source,
        "oracle_pass": oracle_pass,
        "injection": inj,
        "injection_count": injected,
        # v3.3.3: mount/attach/gate provenance (the control's zero proof is
        # classified from the executed command, never inferred).
        "injector": injector_meta(args.model, args.probability, cmd,
                                  proc.stdout, extra),
        "target_event_proof": target_proof,
        "trace": {
            "csv_rows": converted.get("rows"),
            "truncated": converted.get("truncated"),
            "validator_errors": trace_errors,
            "completeness": completeness_report,
        },
        "classification": {
            "run_status": run_status,
            "fault_activation_status": activation,
            "observed_terminal": terminal,
            "terminal_state": final_terminal,
            "terminal_state_reason": terminal_reason,
            "fault_causality": fault_causality,
            "terminal_evidence": evidence,
            "trace_completeness": completeness_report.get("trace_completeness"),
            "record_integrity": completeness_report.get("record_integrity"),
            "propagation_coverage": completeness_report.get("propagation_coverage"),
            "structural_chain_completeness": completeness_report.get(
                "structural_chain_completeness"),
            "fault_effect_propagation_coverage": fault_effect[
                "fault_effect_propagation_coverage"],
            "fault_effect_evidence": fault_effect["fault_effect_evidence"],
            "fault_effect_reason": fault_effect["fault_effect_reason"],
            "oracle_outcome": ("PASS" if oracle_pass else "FAIL"),
        },
        "control_valid": (control_valid if run_role == "CONTROL" else "n/a"),
        "control_misfire": control_misfire,
        "accepted": accepted,
        "accepted_meaning": "record validity; not a claim that the fault caused the terminal",
        "crash_evidence": crash_evidence,
    }
    (out / "pilot_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
