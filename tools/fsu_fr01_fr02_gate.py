#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_fr01_fr02_gate.py — FR01/FR02 transient Vec bit-flip lifecycle gate.

READ-ONLY evidence checker. It never runs gem5, never writes under runs/, and
never changes a RunID/seed. Given an attempt directory (a directory holding a
real gem5 CHAOSPhysReg output: prop_evt.txt[.gz], fault_injections.log,
config.ini, stats.txt) or a whole gate directory, it re-derives every FR01 /
FR02 fact from the files on disk and returns a JSON verdict.

Why this tool exists
--------------------
The C++ side (CHAOSPhysReg + chaos_vec_transient.hh) installs a ONE-SHOT
transient bit flip and emits L0/L1/L2/L5/lifecycle events. A host unit test can
prove the pure model; only the real stream can prove what the simulator did:

  FR01  exactly one bit; popcount(mask)==1; phys cell identity
        (reg_class/phys_reg/lane/lane_width/bit_in_lane/generation) consistent
        with the command and with every lifecycle event.
  FR02  exactly two DIFFERENT bits; popcount==2; no collision; only the two
        target bits changed (before/after cross-checked against
        full_before/full_after); adjacent/non-adjacent/cross-lane/cross-field
        classified from the real bit positions; a colliding configuration must
        be rejected BEFORE injection (VecFaultFailClosed, no L0 root).
  Lifecycle closure: consumer -> commit; pre-consumer overwrite; squash;
        free/realloc; no consumer (exposed_unconsumed / not_consumed);
        precision/lane mismatch fail-closed; consecutive writes must not turn
        the transient into a permanent stuck cell.

Honesty rules (hard-coded, not optional)
----------------------------------------
  * Missing evidence is reported as SKIP / `evidence_missing`, never filled
    with a default.
  * `Masked` is NOT certified just because a run ended or because the final
    workload hash happens to match. An L1 overwrite event only proves that a
    real write was observed on the target cell; proving the specified
    generation's defect is gone additionally needs (a) the overwrite event to
    carry the 128-bit flipped value and mask so the target bits can be shown
    restored, and (b) every post-overwrite read/write on that generation to
    be observed and clean. Streams emitted before those fields existed stay
    BLOCKED with `evidence_missing`; `CONTAINED_BY_OVERWRITE` is only issued
    when the full observation set is present and accounted for.
  * `not_consumed` / `exposed_unconsumed` are UNKNOWN terminal states, not
    Masked: the defect may still be live in the physical cell at run end.
  * A chain_end terminal that contradicts the events on disk is a FAIL, not a
    cosmetic warning (today a squashed consumer is emitted as
    exposed_unconsumed by finalizeVecTransient()).

Usage
-----
    python3 tools/fsu_fr01_fr02_gate.py <attempt-or-gate-dir> [more...]
        [--json-out FILE] [--expect FILE] [--quiet]

Exit codes: 0 = every attempt PASS, 1 = any FAIL, 3 = no FAIL but at least one
SKIP (unverifiable), 2 = no attempt found / usage error.

Per-attempt expectations are read from, in order of precedence:
    1. --expect FILE (JSON, applied to every attempt)
    2. <attempt>/expect.json (JSON)
    3. <attempt>/config.ini  ([board.chaos_phys] / [board.chaos_propagation])
A conflict between sources is a FAIL (`expectation_conflict`), never silently
resolved.

`expect.json` keys (all optional):
    model_id, bits, fault_mask, lane_width, lane_offset, semantic_role,
    phys_reg, run_id, sample_run_id, fault_type, precision,
    expect_fail_closed, allow_multiple_overwrites, require_allocated,
    injection_mode, reg_target_class, rng_seed, max_faults
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_prop_fields as P  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOOL = "fsu_fr01_fr02_gate"
TOOL_VERSION = 1

MODELS = ("FR01", "FR02")
LANE_WIDTHS = (8, 16, 32, 64)
VEC_BITS = 128
TERMINALS = ("committed", "overwritten", "squashed", "free_realloc",
             "exposed_unconsumed", "not_consumed")
# C++ finalizeVecTransient() vocabulary (FR01/FR02 F0), see
# CHAOSPhysReg.cc:727-796.
EMITTED_TERMINALS = ("committed", "overwritten", "exposed_unconsumed",
                     "not_consumed")
LIFECYCLE_KINDS = ("operand_read", "commit", "squash", "overwrite",
                   "chain_end", "generation_change", "cell_free", "cell_realloc",
                   "free", "realloc", "alloc", "cell_reuse")
STUCK_KINDS = ("fault_installed", "stuck_reapplied", "phys_write")
MAX_MASK = (1 << VEC_BITS) - 1

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"

INSTALL_RE = re.compile(r"VecTransientInstall:\s*(.*)$")
OVERWRITE_RE = re.compile(r"VecTransientOverwrite:\s*(.*)$")
FAILCLOSED_RE = re.compile(r"VecFaultFailClosed:\s*(.*)$")
SUMMARY_RE = re.compile(
    r"Cycle:\s*(?P<cycle>\d+).*?Mode:\s*(?P<mode>\w+).*?"
    r"RegClass:\s*(?P<cls>\w+).*?PhysReg\[(?P<phys>\d+)\]"
    r"\s*\((?P<state>[^)]*)\).*?FaultType:\s*(?P<ftype>\w+).*?"
    r"Mask:\s*(?P<mask>[01]+)")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _c(evt, key):
    return str(evt.get(key, "") or "").strip()


def _int_text(text, default=None):
    if text is None:
        return default
    t = str(text).strip()
    if t == "" or t.lower() in ("none", "unknown", "n/a"):
        return default
    try:
        return int(t, 0)
    except ValueError:
        try:
            return int(float(t))
        except ValueError:
            return default


def _i(evt, key):
    return _int_text(_c(evt, key))


def _hexval(text, bits=VEC_BITS):
    """Parse a 0x-prefixed hex value (or a decimal integer) to an int."""
    if text is None:
        return None
    t = str(text).strip()
    if t == "":
        return None
    try:
        if t.lower().startswith("0x"):
            v = int(t, 16)
        else:
            v = int(t, 0)
    except ValueError:
        return None
    if v < 0:
        return None
    return v & ((1 << bits) - 1)


def _popcount(v):
    return bin(v & MAX_MASK).count("1")


def _mask_bits(mask):
    return [b for b in range(VEC_BITS) if (mask >> b) & 1]


def _lane_of(flat, lw):
    return flat // lw if lw in LANE_WIDTHS else -1


def _bit_in_lane(flat, lw):
    return flat % lw if lw in LANE_WIDTHS else -1


def _lane_value(full, lw, lane):
    if full is None or lw not in LANE_WIDTHS or lane is None or lane < 0:
        return None
    nbytes = lw // 8
    base = lane * nbytes
    if base + nbytes > VEC_BITS // 8:
        return None
    return (full >> (base * 8)) & ((1 << lw) - 1)


def _lane_mask_for(flats, lw, lane):
    m = 0
    for f in flats:
        if _lane_of(f, lw) == lane:
            m |= 1 << _bit_in_lane(f, lw)
    return m


def _geometry(flats, lw):
    """Observed geometry of the selected bits under lane width `lw`."""
    out = {
        "lanes": [],
        "fields": [],
        "same_lane": False,
        "adjacent": False,
        "cross_lane": False,
        "cross_field": False,
        "label": "unknown",
    }
    if not flats or lw not in LANE_WIDTHS:
        return out
    lanes = sorted(set(_lane_of(f, lw) for f in flats))
    fields = sorted(set(f // 32 for f in flats))
    out["lanes"] = lanes
    out["fields"] = fields
    out["same_lane"] = len(lanes) == 1
    out["cross_lane"] = len(lanes) >= 2
    out["cross_field"] = len(fields) >= 2
    out["adjacent"] = (len(flats) == 2 and out["same_lane"]
                       and abs(flats[1] - flats[0]) == 1)
    if out["cross_lane"]:
        out["label"] = "cross_lane"
    elif out["adjacent"]:
        out["label"] = "same_lane_adjacent"
    elif out["same_lane"]:
        out["label"] = "same_lane_non_adjacent"
    if out["cross_field"]:
        out["field_label"] = "cross_field"
    return out


def _role_kind(role):
    """Recognise the workbook submodel in a freely formatted role string."""
    r = str(role or "").strip().lower()
    if not r:
        return None
    flat = r.replace("_", "-").replace(" ", "-")
    if "fr01" in flat or flat.startswith("fr01"):
        for tag in ("fr01-a", "fr01-b", "fr01-c"):
            if tag in flat:
                return tag
        return "fr01"
    if "fr02" in flat:
        if "fr02-d" in flat or "cross-field" in flat or "crossfield" in flat \
                or "exp+mant" in flat or "exp-mant" in flat:
            return "fr02-d"
        if "fr02-c" in flat or "cross-lane" in flat or "crosslane" in flat:
            return "fr02-c"
        if "fr02-b" in flat or "non-adjacent" in flat or "nonadjacent" in flat:
            return "fr02-b"
        if "fr02-a" in flat or "adjacent" in flat:
            return "fr02-a"
    if "cross-lane" in flat or "crosslane" in flat:
        return "fr02-c"
    if "cross-field" in flat or "crossfield" in flat:
        return "fr02-d"
    if "adjacent" in flat and "non" in flat:
        return "fr02-b"
    if "adjacent" in flat:
        return "fr02-a"
    return None


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# config.ini / expect.json expectations
# ---------------------------------------------------------------------------
def _cfg_get(cfg, section, key, default=None):
    sec = cfg.get(section) or {}
    if key in sec:
        return sec[key]
    for k, v in sec.items():
        if k.lower() == key.lower():
            return v
    return default


def read_config(path):
    cfg = {}
    if not path:
        return cfg
    p = Path(path)
    if not p.exists():
        return cfg
    cp = configparser.RawConfigParser()
    cp.optionxform = str
    try:
        cp.read(str(p), encoding="utf-8")
    except (configparser.Error, OSError):
        return cfg
    for sec in cp.sections():
        try:
            cfg[sec] = dict(cp.items(sec))
        except configparser.Error:
            cfg[sec] = {}
    return cfg


def expectations_from_config(cfg):
    exp = {}
    source = "config.ini"
    cp = "board.chaos_phys"
    prop = "board.chaos_propagation"

    def put(key, value):
        if value is None:
            return
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return
        exp[key] = value

    put("bits", _int_text(_cfg_get(cfg, cp, "bitsToChange")))
    mask = _int_text(_cfg_get(cfg, cp, "faultMask"))
    put("fault_mask", mask)
    put("lane_width", _int_text(_cfg_get(cfg, cp, "vecLaneWidth")))
    put("lane_offset", _int_text(_cfg_get(cfg, cp, "vecLaneOffset")))
    put("fault_type", _cfg_get(cfg, cp, "faultType"))
    put("semantic_role", _cfg_get(cfg, cp, "semanticRole"))
    put("injection_mode", _cfg_get(cfg, cp, "injectionMode"))
    put("reg_target_class", _cfg_get(cfg, cp, "regTargetClass"))
    put("target_phys_idx", _int_text(_cfg_get(cfg, cp, "targetPhysRegIdx")))
    put("rng_seed", _int_text(_cfg_get(cfg, cp, "rngSeed")))
    put("max_faults", _int_text(_cfg_get(cfg, cp, "maxFaults")))
    put("require_allocated",
        str(_cfg_get(cfg, cp, "requireAllocated", "")).strip().lower() == "true")
    put("run_id", _cfg_get(cfg, prop, "runId"))
    put("sample_run_id", _cfg_get(cfg, prop, "sampleRunId"))
    put("num_phys_vec_regs", _int_text(_cfg_get(cfg, prop, "numPhysVecRegs")))
    # numPhysVecRegs lives on the core, not on CHAOSPhysReg.
    if exp.get("num_phys_vec_regs") is None:
        for sec in cfg:
            if sec.startswith("board.processor") and \
                    "cores" in sec:
                v = _int_text(_cfg_get(cfg, sec, "numPhysVecRegs"))
                if v is not None:
                    exp["num_phys_vec_regs"] = v
                    break
    if exp.get("bits") in (1, 2):
        exp["model_id"] = "FR01" if exp["bits"] == 1 else "FR02"
    exp["_source"] = source
    return exp


EXPECT_KEYS = (
    "model_id", "bits", "fault_mask", "lane_width", "lane_offset",
    "semantic_role", "phys_reg", "run_id", "sample_run_id", "fault_type",
    "precision", "expect_fail_closed", "allow_multiple_overwrites",
    "require_allocated", "injection_mode", "reg_target_class", "rng_seed",
    "max_faults", "num_phys_vec_regs",
)


def _normalise_expect(raw, source):
    exp = {}
    if not isinstance(raw, dict):
        return exp
    for key in EXPECT_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if key in ("bits", "lane_width", "lane_offset", "phys_reg",
                   "rng_seed", "max_faults", "num_phys_vec_regs"):
            value = _int_text(value)
        elif key in ("fault_mask", "target_phys_idx"):
            value = _hexval(value) if isinstance(value, str) else _int_text(value)
        elif key in ("expect_fail_closed", "allow_multiple_overwrites",
                     "require_allocated"):
            if isinstance(value, str):
                value = value.strip().lower() in ("1", "true", "yes")
            else:
                value = bool(value)
        elif isinstance(value, str):
            value = value.strip()
        if value is None or value == "":
            continue
        exp[key] = value
    exp["_source"] = source
    return exp


def load_expectations(attempt, cli_expect):
    attempt = Path(attempt)
    cfg = read_config(attempt / "config.ini")
    layers = []
    cfg_exp = expectations_from_config(cfg) if cfg else {}
    if cfg_exp:
        cfg_exp.pop("_source", None)
        layers.append(("config.ini", cfg_exp))
    local = _read_json(attempt / "expect.json")
    if local is not None:
        layers.append(("expect.json", _normalise_expect(local, "expect.json")))
    if cli_expect:
        layers.append(("cli", _normalise_expect(cli_expect, "cli")))

    merged = {}
    sources = {}
    conflicts = []
    for source, layer in layers:
        for key, value in layer.items():
            if key.startswith("_"):
                continue
            if key in merged and merged[key] != value:
                # config.ini vs expect.json/cli is a hard conflict: the gate
                # must never silently pick one.
                if key == "target_phys_idx" and "phys_reg" in merged:
                    continue
                conflicts.append({
                    "field": key,
                    "values": [{"source": sources.get(key), "value": merged[key]},
                               {"source": source, "value": value}],
                })
                continue
            if key not in merged:
                merged[key] = value
                sources[key] = source
    return merged, sources, conflicts, cfg


# ---------------------------------------------------------------------------
# Pre-injection configuration validity (mirrors C++ selectionFromMask()).
#
# Only conditions the C++ really rejects are listed as *fail-closed
# expectations*.  Semantic role vs lane-width mistakes that C++ does NOT
# reject (e.g. FR01-a with a 32-bit lane) are surfaced as a normal gate FAIL
# on the injected event, never as an expected rejection.
# ---------------------------------------------------------------------------
FC_REASONS = {
    "invalid_lane_width": {"invalid_lane_width"},
    "lane_offset_out_of_range": {"lane_offset_out_of_range"},
    "bit_count_out_of_range": {"bit_count_out_of_range"},
    "mask_popcount_mismatch": {"mask_popcount_mismatch"},
    "mask_geometry_mismatch": {
        "bits_not_in_one_lane", "written_lane_mismatch",
        "bits_not_adjacent_in_lane", "bits_adjacent_or_out_of_lane",
        "mask_is_single_lane", "written_lane_not_in_mask",
        "mask_is_single_field", "bits_not_in_directed_lane",
        "directed_field_not_in_mask", "adjacent_needs_two_bits",
        "non_adjacent_needs_two_bits", "cross_lane_needs_two_bits",
        "cross_field_needs_two_bits", "duplicate_bit",
    },
}


def config_problems(exp):
    """Conditions that must fail closed BEFORE injection.

    Returns a list of dicts: {"kind", "detail", "acceptable_reasons"}.
    """
    problems = []
    bits = exp.get("bits")
    lw = exp.get("lane_width")
    lo = exp.get("lane_offset")
    mask = exp.get("fault_mask")
    role = _role_kind(exp.get("semantic_role"))

    def add(kind, detail):
        problems.append({
            "kind": kind,
            "detail": detail,
            "acceptable_reasons": FC_REASONS.get(kind, set()),
        })

    # A missing manifest field is evidence_missing, NOT proof that the
    # command was invalid: only fields that are present and inconsistent can
    # establish a fail-closed expectation.
    if bits is None or lw is None:
        return problems
    if bits <= 0 or bits > VEC_BITS:
        add("bit_count_out_of_range", "bitsToChange=%s outside 1..%d"
            % (bits, VEC_BITS))
    if lw not in LANE_WIDTHS:
        add("invalid_lane_width", "vecLaneWidth=%s not in %s"
            % (lw, list(LANE_WIDTHS)))
    elif lo is not None and (lo < -1 or lo >= VEC_BITS // lw):
        add("lane_offset_out_of_range",
            "vecLaneOffset=%s outside -1..%d for lane width %s"
            % (lo, VEC_BITS // lw - 1, lw))

    if mask is None or mask == 0:
        return problems  # random mask: only the event stream can be checked
    mask &= (1 << 64) - 1
    flats = _mask_bits(mask)
    got = len(flats)
    if bits is not None and got != bits:
        add("mask_popcount_mismatch",
            "faultMask popcount=%d but bitsToChange=%d" % (got, bits))
        return problems
    if lw not in LANE_WIDTHS:
        return problems

    geom = _geometry(flats, lw)
    role = role or ""
    if role.startswith("fr02"):
        if role == "fr02-c" and not geom["cross_lane"]:
            add("mask_geometry_mismatch",
                "FR02-c requires >=2 lanes, mask lanes=%s" % geom["lanes"])
        if role == "fr02-d" and not geom["cross_field"]:
            add("mask_geometry_mismatch",
                "FR02-d requires >=2 32-bit fields, mask fields=%s"
                % geom["fields"])
        if role == "fr02-a" and not geom["adjacent"]:
            add("mask_geometry_mismatch",
                "FR02-a requires two adjacent bits in one lane, flat bits=%s"
                % flats)
        if role == "fr02-b" and not (geom["same_lane"]
                                     and not geom["adjacent"]):
            add("mask_geometry_mismatch",
                "FR02-b requires same-lane non-adjacent bits, flat bits=%s"
                % flats)
        if role == "fr02-d" and lo is not None and lo >= 0:
            if lw >= 64:
                if any(_lane_of(f, lw) != lo for f in flats):
                    add("mask_geometry_mismatch",
                        "FR02-d directed 64-bit lane %d does not hold all bits"
                        % lo)
            else:
                want = (lo * lw) // 32
                if want not in geom["fields"]:
                    add("mask_geometry_mismatch",
                        "FR02-d directed field %d not in mask fields %s"
                        % (want, geom["fields"]))
    if lo is not None and lo >= 0:
        if role in ("fr02-a", "fr02-b") and geom["lanes"] != [lo]:
            add("mask_geometry_mismatch",
                "directed lane %d but bits live in lanes %s"
                % (lo, geom["lanes"]))
        if role == "fr02-c" and lo not in geom["lanes"]:
            add("mask_geometry_mismatch",
                "directed lane %d not represented in mask lanes %s"
                % (lo, geom["lanes"]))
        if role in ("", "fr01", "fr01-a", "fr01-b", "fr01-c"):
            if any(_lane_of(f, lw) != lo for f in flats):
                add("mask_geometry_mismatch",
                    "directed lane %d does not hold bits %s" % (lo, flats))
    return problems


def _acceptable_reasons(problems):
    acc = set()
    for p in problems:
        acc |= set(p.get("acceptable_reasons") or ())
    return acc


# ---------------------------------------------------------------------------
# fault_injections.log / stats.txt
# ---------------------------------------------------------------------------
def _log_kv(tail):
    out = {}
    for tok in str(tail).split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def parse_fault_log(path):
    log = {
        "exists": False,
        "installs": [],
        "overwrites": [],
        "fail_closed": [],
        "summaries": [],
        "read_trace": [],
    }
    if not path or not Path(path).exists():
        return log
    log["exists"] = True
    for line in _read_text(path).splitlines():
        m = INSTALL_RE.search(line)
        if m:
            log["installs"].append(_log_kv(m.group(1)))
            continue
        m = OVERWRITE_RE.search(line)
        if m:
            log["overwrites"].append(_log_kv(m.group(1)))
            continue
        m = FAILCLOSED_RE.search(line)
        if m:
            log["fail_closed"].append(_log_kv(m.group(1)))
            continue
        if line.startswith("ReadTracePoll:"):
            log["read_trace"].append(line.strip())
            continue
        if line.startswith("Cycle:"):
            m = SUMMARY_RE.search(line)
            if m:
                log["summaries"].append(m.groupdict())
    return log


def parse_stats(path):
    out = {}
    if not path or not Path(path).exists():
        return out
    for line in _read_text(path).splitlines():
        m = re.match(r"^(\S+)\s+([0-9.eE+\-]+)\s", line)
        if not m:
            continue
        key, text = m.group(1), m.group(2)
        try:
            out[key] = int(text)
        except ValueError:
            try:
                out[key] = float(text)
            except ValueError:
                pass
    return out


def _stat(stats, suffix):
    for key, value in stats.items():
        if key == suffix or key.endswith("." + suffix):
            return value
    return None


# ---------------------------------------------------------------------------
# Check collector
# ---------------------------------------------------------------------------
class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, status, detail, critical=True, source=None):
        item = {
            "check": name,
            "status": status,
            "detail": detail,
            "critical": bool(critical),
        }
        if source:
            item["fields_source"] = sorted(set(source))
        self.items.append(item)
        return status

    def passed(self, name, detail, critical=True, source=None):
        return self.add(name, STATUS_PASS, detail, critical, source)

    def failed(self, name, detail, critical=True, source=None):
        return self.add(name, STATUS_FAIL, detail, critical, source)

    def skipped(self, name, detail, critical=False, source=None):
        return self.add(name, STATUS_SKIP, detail, critical, source)

    def counts(self):
        out = {STATUS_PASS: 0, STATUS_FAIL: 0, STATUS_SKIP: 0}
        for item in self.items:
            out[item["status"]] += 1
        return out

    def overall(self):
        if any(i["status"] == STATUS_FAIL for i in self.items):
            return STATUS_FAIL
        if any(i["status"] == STATUS_SKIP and i["critical"]
               for i in self.items):
            return STATUS_SKIP
        return STATUS_PASS

    def failures(self):
        return [i["check"] for i in self.items if i["status"] == STATUS_FAIL]

    def critical_skips(self):
        return [i["check"] for i in self.items
                if i["status"] == STATUS_SKIP and i["critical"]]


# ---------------------------------------------------------------------------
# Attempt analysis
# ---------------------------------------------------------------------------
def _find_stream(attempt):
    for name in ("prop_evt.txt.gz", "prop_evt.txt"):
        p = Path(attempt) / name
        if p.exists():
            return p
    return None


def _evidence_entry(path):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return {"path": str(p), "exists": False}
    try:
        size = p.stat().st_size
    except OSError:
        size = None
    return {
        "path": str(p.resolve()),
        "exists": True,
        "size_bytes": size,
        "sha256": sha256_file(p),
    }


def _fail_closed_report(attempt, exp, sources, conflicts, strict, stream_path,
                        events, truncated, stream_reason, log, stats, cfg):
    checks = Checks()
    evidence = {
        "event_stream": _evidence_entry(stream_path),
        "fault_log": _evidence_entry(Path(attempt) / "fault_injections.log"),
        "config_ini": _evidence_entry(Path(attempt) / "config.ini"),
        "expect_json": _evidence_entry(Path(attempt) / "expect.json"),
        "stats": _evidence_entry(Path(attempt) / "stats.txt"),
    }
    problems = config_problems(exp)
    detail = "; ".join("%s: %s" % (p["kind"], p["detail"]) for p in problems)

    if conflicts:
        checks.failed("expectation_conflict", json.dumps(conflicts,
                                                         ensure_ascii=False))
    if stream_path is None:
        checks.skipped("evidence_stream", "no prop_evt stream found",
                       critical=False)
    elif truncated:
        checks.failed("stream_integrity",
                      "event stream truncated/unreadable: %s"
                      % (stream_reason or "unknown"))
    else:
        checks.passed("stream_integrity",
                      "%d event line(s) read" % len(events))

    roots = [e for e in events
             if _c(e, "kind") == "fault_applied"
             and _c(e, "model_id") in MODELS]
    if roots:
        checks.failed("no_fault_applied",
                      "expected fail-closed but %d transient root(s) exist"
                      % len(roots))
    else:
        checks.passed("no_fault_applied",
                      "no FR01/FR02 fault_applied event in the stream")

    if log["installs"]:
        checks.failed("no_injection_logged",
                      "%d VecTransientInstall line(s) despite fail-closed"
                      % len(log["installs"]))
    else:
        checks.passed("no_injection_logged", "fault log has no install line")

    fc = log["fail_closed"]
    if not fc:
        checks.failed("fail_closed_log",
                      "no VecFaultFailClosed line in fault_injections.log")
    else:
        acceptable = _acceptable_reasons(problems)
        reasons = [x.get("reason", "") for x in fc]
        matched = [r for r in reasons if r in acceptable]
        if acceptable and not matched:
            checks.failed(
                "fail_closed_log",
                "rejection reasons %s do not match the gate-derived "
                "condition(s) %s" % (reasons, sorted(acceptable)))
        elif not acceptable:
            checks.failed("fail_closed_log",
                          "rejection logged (%s) but the gate derived no "
                          "pre-injection inconsistency" % reasons)
        else:
            checks.passed("fail_closed_log",
                          "reason(s) %s; no injection, fault not consumed"
                          % matched, source=["fault_injections.log"])

    if not stats:
        checks.skipped("stats_zero_injection",
                       "stats.txt missing: cannot prove zero injection",
                       critical=True)
    else:
        nf = _stat(stats, "numFaultsInjected")
        nbf = _stat(stats, "numBitFlips")
        nperm = _stat(stats, "numPermanentFaults")
        nsz = _stat(stats, "numStuckAtZero")
        nso = _stat(stats, "numStuckAtOne")
        zeros = (nf == 0 and nbf == 0 and nperm == 0
                 and nsz == 0 and nso == 0)
        if zeros:
            checks.passed("stats_zero_injection",
                          "numFaultsInjected=0 numBitFlips=0 "
                          "numPermanentFaults=0 stuck=0",
                          source=["stats.txt"])
        else:
            checks.failed("stats_zero_injection",
                          "stats show an injection: faults=%s bitflips=%s "
                          "permanent=%s stuck0=%s stuck1=%s"
                          % (nf, nbf, nperm, nsz, nso),
                          source=["stats.txt"])

    siminsts = _stat(stats, "simInsts")
    simticks = _stat(stats, "simTicks")
    if stats and (siminsts is not None and siminsts > 0
                  and simticks is not None):
        checks.passed("run_boundary",
                      "stats.txt written: simInsts=%s simTicks=%s"
                      % (siminsts, simticks), source=["stats.txt"])
    else:
        checks.skipped("run_boundary",
                       "stats.txt lacks simInsts/simTicks; run end not "
                       "traceable", critical=True, source=["stats.txt"])

    status = checks.overall()
    certification = {
        "status": "CERTIFIED" if status == STATUS_PASS else (
            "FAILED" if status == STATUS_FAIL else "BLOCKED"),
        "verdict": "precondition_rejected",
        "basis": "injection refused before touching the PRF; no L0 root, "
                 "no stats injection, VecFaultFailClosed reason present",
        "missing": [],
    }
    return {
        "attempt": None,
        "status": status,
        "reason": ("pre-injection rejection verified: " + detail)
                  if status == STATUS_PASS else
                  "fail-closed gate did not verify: "
                  + "; ".join(checks.failures() or checks.critical_skips()),
        "model_id": exp.get("model_id"),
        "mode": "fail_closed",
        "run_id": exp.get("run_id"),
        "sample_run_id": exp.get("sample_run_id"),
        "expectations": exp,
        "expectation_sources": sources,
        "checks": checks.items,
        "check_counts": checks.counts(),
        "evidence": evidence,
        "identity": {},
        "lifecycle": {
            "closure": "fail_closed",
            "recorded_terminal": None,
            "certified_closure": status == STATUS_PASS,
            "events": {},
        },
        "masked_certification": {
            "certified": False,
            "verdict": "NOT_APPLICABLE",
            "reason": "no fault was injected (fail-closed precondition)",
            "final_hash_equality_alone_insufficient": True,
        },
        "certification": certification,
        "blockers": [],
    }


def analyze_attempt(attempt, cli_expect=None, rel_name=None):
    attempt = Path(attempt).resolve()
    exp, sources, conflicts, cfg = load_expectations(attempt, cli_expect)
    stream_path = _find_stream(attempt)
    log_path = attempt / "fault_injections.log"
    stats_path = attempt / "stats.txt"
    log = parse_fault_log(log_path)
    stats = parse_stats(stats_path)

    events, truncated, stream_reason = [], False, ""
    if stream_path is not None:
        events, truncated, stream_reason = P.read_stream(stream_path)

    # ------------------------------------------------------------------
    # Expectations decide the expected mode BEFORE looking at the root:
    # an inconsistent command must have failed closed; a consistent one
    # must have produced exactly one transient root.
    # ------------------------------------------------------------------
    cfg_problems = config_problems(exp)
    explicit_fc = bool(exp.get("expect_fail_closed"))
    # Without any manifest/config we cannot claim the command was invalid;
    # the event stream is then the only authority (and the manifest checks
    # below are reported as SKIP/evidence_missing).
    expected_fc = explicit_fc or (bool(exp) and bool(cfg_problems))
    # requireAllocated is only meaningful for phys mode.
    if exp.get("require_allocated") and \
            str(exp.get("injection_mode", "phys")) != "phys":
        conflicts = list(conflicts) + [{
            "field": "require_allocated",
            "values": [{"source": sources.get("require_allocated"),
                        "value": True},
                       {"source": "gate", "value": "phys mode only"}],
        }]

    if expected_fc:
        rep = _fail_closed_report(
            attempt, exp, sources, conflicts, True, stream_path, events,
            truncated, stream_reason, log, stats, cfg)
        rep["attempt"] = rel_name or str(attempt)
        return rep

    checks = Checks()
    evidence = {
        "event_stream": _evidence_entry(stream_path),
        "fault_log": _evidence_entry(log_path),
        "config_ini": _evidence_entry(attempt / "config.ini"),
        "expect_json": _evidence_entry(attempt / "expect.json"),
        "stats": _evidence_entry(stats_path),
    }

    if conflicts:
        checks.failed("expectation_conflict",
                      json.dumps(conflicts, ensure_ascii=False))
    if stream_path is None:
        checks.failed("evidence_stream", "no prop_evt.txt[.gz] found")
        events = []
    elif truncated:
        checks.failed("stream_integrity",
                      "event stream truncated/unreadable: %s"
                      % (stream_reason or "unknown"))
    else:
        checks.passed("stream_integrity",
                      "%d event line(s) read" % len(events))

    roots = [e for e in events
             if _c(e, "kind") == "fault_applied"
             and _c(e, "model_id") in MODELS]
    if not roots:
        if log["fail_closed"]:
            checks.failed(
                "fail_closed_not_expected",
                "VecFaultFailClosed present (%s) but the gate derived no "
                "pre-injection inconsistency: %s"
                % ([x.get("reason") for x in log["fail_closed"]],
                   "; ".join("%s: %s" % (p["kind"], p["detail"])
                            for p in cfg_problems) or "none"))
        else:
            checks.failed("root_count",
                          "no FR01/FR02 fault_applied root and no "
                          "VecFaultFailClosed evidence")
        rep = _blocked_report(attempt, rel_name, exp, sources, checks,
                              evidence, "no transient root")
        return rep
    if len(roots) != 1:
        checks.failed("root_count",
                      "%d transient roots; FR01/FR02 F0 requires exactly one "
                      "injection per run" % len(roots))
        rep = _blocked_report(attempt, rel_name, exp, sources, checks,
                              evidence, "multiple roots")
        return rep
    checks.passed("root_count", "exactly one fault_applied root")

    root = roots[0]
    fid = _c(root, "fault_id")
    if not fid:
        checks.failed("fault_id", "root has an empty fault_id")
        rep = _blocked_report(attempt, rel_name, exp, sources, checks,
                              evidence, "missing fault_id")
        return rep
    # CHAOSPropagation's per-fault exit flush emits a blank chain_end with the
    # same fault_id but model_id=""/phys_reg=""/terminal="" and corr=none. It
    # is NOT a transient lifecycle event: group strictly by fault_id AND a
    # real FR01/FR02 model id.
    fault_events = [e for e in events
                    if _c(e, "fault_id") == fid
                    and _c(e, "model_id") in MODELS]
    fault_events.sort(key=lambda e: (_i(e, "tick") if _i(e, "tick")
                                     is not None else -1,
                                     _i(e, "event_id")
                                     if _i(e, "event_id") is not None else -1))

    identity = _check_identity(checks, root, exp, sources, stream_path, events)
    _check_carrier(checks, root, fault_events, exp, sources)
    _check_run_identity(checks, root, fault_events, exp, sources)
    _check_config_conforms(checks, root, exp, sources, cfg)
    _check_log_crosscheck(checks, root, log, exp, sources)
    lc = _check_lifecycle(checks, root, fault_events, exp, sources, stats,
                          evidence)
    _check_no_permanent(checks, root, fault_events, log, stats, exp, sources)
    _check_boundary(checks, root, fault_events, lc, stats, exp, sources)

    status = checks.overall()
    closure = lc["closure"]
    containment = _containment_evidence(root, fault_events)
    certification = _certification(closure, lc, status, containment)
    masked = _masked_certification(closure, lc, status, containment)

    report = {
        "attempt": rel_name or str(attempt),
        "status": status,
        "reason": _reason_text(status, closure, lc, checks),
        "model_id": identity.get("model_id"),
        "mode": "transient",
        "run_id": _c(root, "run_id"),
        "sample_run_id": _c(root, "sample_run_id"),
        "fault_id": fid,
        "expectations": exp,
        "expectation_sources": sources,
        "checks": checks.items,
        "check_counts": checks.counts(),
        "evidence": evidence,
        "identity": identity,
        "lifecycle": lc,
        "containment": containment,
        "masked_certification": masked,
        "certification": certification,
        "blockers": _blockers(lc, masked, certification, containment),
    }
    return report


def _blocked_report(attempt, rel_name, exp, sources, checks, evidence, why):
    return {
        "attempt": rel_name or str(attempt),
        "status": checks.overall(),
        "reason": "%s: %s" % (why,
                              "; ".join(checks.failures()
                                        or checks.critical_skips())),
        "model_id": exp.get("model_id"),
        "mode": "blocked",
        "run_id": exp.get("run_id"),
        "sample_run_id": exp.get("sample_run_id"),
        "expectations": exp,
        "expectation_sources": sources,
        "checks": checks.items,
        "check_counts": checks.counts(),
        "evidence": evidence,
        "identity": {},
        "lifecycle": {"closure": "evidence_missing",
                      "certified_closure": False, "events": {}},
        "masked_certification": {
            "certified": False,
            "verdict": "BLOCKED",
            "reason": "no usable transient chain on disk",
            "final_hash_equality_alone_insufficient": True,
        },
        "certification": {
            "status": "BLOCKED",
            "verdict": "evidence_missing",
            "missing": ["transient L0 root"],
        },
        "blockers": ["transient L0 root"],
    }


# ---------------------------------------------------------------------------
# Identity / bit-level checks
# ---------------------------------------------------------------------------
def _check_identity(checks, root, exp, sources, stream_path, events):
    ident = {}
    model = _c(root, "model_id")
    ident["model_id"] = model
    ident["fault_id"] = _c(root, "fault_id")
    ident["event_id"] = _i(root, "event_id")
    ident["reg_class"] = _c(root, "reg_class")
    ident["phys_reg"] = _i(root, "phys_reg")
    ident["arch_reg"] = _i(root, "arch_reg")
    ident["reg_generation"] = _i(root, "reg_generation")
    ident["lane_width"] = _i(root, "lane_width")
    ident["lane_offset"] = _i(root, "lane_offset")
    ident["lane_mask"] = _hexval(_c(root, "lane_mask"), 64)
    ident["fault_mask"] = _hexval(_c(root, "fault_mask"), VEC_BITS)
    ident["bit_indices"] = _c(root, "bit_indices")
    ident["bit_in_lane"] = _i(root, "bit_in_lane")
    ident["precision"] = _c(root, "precision")
    ident["field"] = _c(root, "field")
    ident["submodel"] = _c(root, "submodel")
    ident["full_before"] = _hexval(_c(root, "full_before"), VEC_BITS)
    ident["full_after"] = _hexval(_c(root, "full_after"), VEC_BITS)
    ident["lane_before"] = _hexval(_c(root, "before"), 64)
    ident["lane_after"] = _hexval(_c(root, "after"), 64)
    ident["carrier_cell_allocated"] = None

    # -- model / bit count ------------------------------------------------
    bit_text = _c(root, "bit_indices")
    flats = []
    if bit_text:
        for tok in bit_text.split(","):
            tok = tok.strip()
            if tok:
                try:
                    flats.append(int(tok, 0))
                except ValueError:
                    flats = []
                    break
    ident["flats"] = flats
    count = len(flats)
    derived_model = {1: "FR01", 2: "FR02"}.get(count)
    model_problems = []
    if count not in (1, 2):
        model_problems.append("bit_indices=%r is not 1 or 2 bits" % bit_text)
    if model not in MODELS:
        model_problems.append("root model_id=%r" % model)
    if derived_model is not None and model != derived_model:
        model_problems.append("root model_id=%s but %d bit(s) -> %s"
                              % (model, count, derived_model))
    if exp.get("model_id") and model != exp["model_id"]:
        model_problems.append("expected model %s, root says %s"
                              % (exp["model_id"], model))
    if exp.get("bits") is not None and count != exp["bits"]:
        model_problems.append("expected %s bit(s), root has %d"
                              % (exp["bits"], count))
    if model_problems:
        checks.failed("model_and_bit_count", "; ".join(model_problems),
                      source=["prop_evt.txt", "config.ini/expect.json"])
    else:
        checks.passed("model_and_bit_count",
                      "%s with exactly %d bit(s) %s"
                      % (model, count, flats),
                      source=["prop_evt.txt"])

    # -- distinct / domain / order ---------------------------------------
    if not flats:
        checks.failed("bit_identity", "root has no parseable bit_indices")
    else:
        bad = [f for f in flats if f < 0 or f >= VEC_BITS]
        dup = len(set(flats)) != len(flats)
        ordered = flats == sorted(flats)
        if bad:
            checks.failed("bit_identity",
                          "bit(s) outside the 128-bit Vec domain: %s" % bad)
        elif dup:
            checks.failed("bit_identity",
                          "duplicate bit position(s) in bit_indices=%s"
                          % bit_text)
        elif not ordered:
            checks.failed("bit_identity",
                          "bit_indices not ascending: %s" % bit_text)
        else:
            checks.passed("bit_identity",
                          "distinct, in-domain, ascending bits %s" % flats)

    # -- fault mask -------------------------------------------------------
    mask = ident["fault_mask"]
    if mask is None:
        checks.failed("mask_identity", "root fault_mask is missing/invalid")
    else:
        mb = _mask_bits(mask)
        if len(mb) != count:
            checks.failed("mask_identity",
                          "fault_mask popcount=%d but bit_indices count=%d"
                          % (len(mb), count))
        elif mb != sorted(flats):
            checks.failed("mask_identity",
                          "fault_mask bits %s != bit_indices %s"
                          % (mb, sorted(flats)))
        else:
            checks.passed("mask_identity",
                          "fault_mask popcount=%d, exactly the selected bits"
                          % len(mb))
        cfg_mask = exp.get("fault_mask")
        if cfg_mask is not None and cfg_mask != 0:
            low = mask & ((1 << 64) - 1)
            if low != (cfg_mask & ((1 << 64) - 1)):
                checks.failed(
                    "mask_matches_command",
                    "root fault_mask low64=0x%x != manifest faultMask=0x%x"
                    % (low, cfg_mask))
            else:
                checks.passed("mask_matches_command",
                              "root fault_mask matches manifest faultMask "
                              "0x%x" % cfg_mask,
                              source=["prop_evt.txt", "config.ini"])
        else:
            checks.skipped("mask_matches_command",
                           "manifest faultMask is 0 (random mask); only the "
                           "event stream is authoritative",
                           critical=False)

    # -- lane / bit-in-lane identity --------------------------------------
    lw = ident["lane_width"]
    lo = ident["lane_offset"]
    lane_problems = []
    if lw not in LANE_WIDTHS:
        lane_problems.append("lane_width=%r not in %s"
                             % (lw, list(LANE_WIDTHS)))
    if exp.get("lane_width") is not None and lw != exp["lane_width"]:
        lane_problems.append("lane_width=%s but manifest says %s"
                             % (lw, exp["lane_width"]))
    if lo is None or lo < 0:
        lane_problems.append("lane_offset=%r is not a concrete lane" % lo)
    if flats and lw in LANE_WIDTHS:
        first_lane = _lane_of(min(flats), lw)
        first_bit = _bit_in_lane(min(flats), lw)
        if lo is not None and lo != first_lane:
            lane_problems.append("lane_offset=%s but lowest bit %d is in "
                                 "lane %d" % (lo, min(flats), first_lane))
        if ident["bit_in_lane"] is not None and \
                ident["bit_in_lane"] != first_bit:
            lane_problems.append("bit_in_lane=%s but lowest bit %d -> %d"
                                 % (ident["bit_in_lane"], min(flats),
                                    first_bit))
        # Every bit must fit inside the 128-bit architectural value under the
        # declared lane width (this is what makes lane/lane_width meaningful).
        if any(_lane_of(f, lw) >= VEC_BITS // lw for f in flats):
            lane_problems.append("bit outside the 128-bit lane domain")
    if lane_problems:
        checks.failed("lane_identity", "; ".join(lane_problems))
    else:
        checks.passed("lane_identity",
                      "lane_width=%s lane_offset=%s bit_in_lane=%s"
                      % (lw, lo, ident["bit_in_lane"]))

    # Directed lane (manifest) must agree with the real bits.
    want_lane = exp.get("lane_offset")
    if want_lane is not None and want_lane >= 0 and flats and lw in LANE_WIDTHS:
        lanes = sorted(set(_lane_of(f, lw) for f in flats))
        role = _role_kind(exp.get("semantic_role"))
        if role in ("fr02-c",):
            ok = want_lane in lanes
            detail = "directed lane %d present in lanes %s" % (want_lane, lanes)
        elif role == "fr02-d" and lw >= 64:
            ok = lanes == [want_lane]
            detail = "directed 64-bit lane %d holds all bits (%s)" \
                     % (want_lane, lanes)
        else:
            ok = lanes == [want_lane]
            detail = "all bits in directed lane %d (lanes=%s)" \
                     % (want_lane, lanes)
        if ok:
            checks.passed("directed_lane", detail,
                          source=["prop_evt.txt", "config.ini"])
        else:
            checks.failed("directed_lane", detail,
                          source=["prop_evt.txt", "config.ini"])
    elif want_lane == -1:
        checks.skipped("directed_lane",
                       "manifest lane is random (-1); only the event lane is "
                       "authoritative", critical=False,
                       source=["config.ini"])
    else:
        checks.skipped("directed_lane", "no directed lane in the manifest",
                       critical=False)

    # -- lane mask --------------------------------------------------------
    if flats and lw in LANE_WIDTHS and lo is not None:
        want = _lane_mask_for(flats, lw, lo)
        got = ident["lane_mask"]
        if got is None:
            checks.failed("lane_mask", "root lane_mask is missing")
        elif got != want:
            checks.failed("lane_mask",
                          "lane_mask=0x%x but bits %s in lane %d -> 0x%x"
                          % (got, flats, lo, want))
        else:
            checks.passed("lane_mask",
                          "lane_mask=0x%x is the relative mask of the "
                          "selected bits in lane %d" % (got, lo))

    # -- before/after + full_before/full_after ----------------------------
    lb, la = ident["lane_before"], ident["lane_after"]
    mask = ident["fault_mask"]
    if lb is None or la is None or ident["lane_mask"] is None:
        checks.failed("lane_value",
                      "root before/after/lane_mask missing or unparseable")
    else:
        exp_after = lb ^ ident["lane_mask"]
        if la != exp_after:
            checks.failed("lane_value",
                          "after=0x%x != before^lane_mask=0x%x"
                          % (la, exp_after))
        elif lb == la:
            checks.failed("lane_value",
                          "before==after (0x%x): no bit actually changed" % lb)
        else:
            checks.passed("lane_value",
                          "before=0x%x after=0x%x == before ^ lane_mask"
                          % (lb, la),
                          source=["prop_evt.txt"])

    fb, fa = ident["full_before"], ident["full_after"]
    if fb is None or fa is None or mask is None:
        checks.skipped("non_target_bits",
                       "full_before/full_after not emitted; non-target bits "
                       "cannot be cross-validated", critical=True,
                       source=["prop_evt.txt"])
    else:
        diff = (fb ^ fa) & MAX_MASK
        problems = []
        if diff != mask:
            problems.append(
                "full_before^full_after=0x%032x != fault_mask=0x%032x"
                % (diff, mask))
        if fb & mask:
            problems.append("selected bit(s) already set in full_before: "
                            "0x%032x" % (fb & mask))
        if lw in LANE_WIDTHS and lo is not None:
            if _lane_value(fb, lw, lo) != lb:
                problems.append("full_before lane %s=0x%x != before=0x%x"
                                % (lo, _lane_value(fb, lw, lo), lb))
            if _lane_value(fa, lw, lo) != la:
                problems.append("full_after lane %s=0x%x != after=0x%x"
                                % (lo, _lane_value(fa, lw, lo), la))
        if problems:
            checks.failed("non_target_bits", "; ".join(problems),
                          source=["prop_evt.txt"])
        else:
            checks.passed(
                "non_target_bits",
                "only the selected bit(s) differ: full_before^full_after == "
                "fault_mask (0x%032x); lane values agree with the 128-bit "
                "image" % mask, source=["prop_evt.txt"])

    # -- geometry / workbook submodel ------------------------------------
    if flats and lw in LANE_WIDTHS:
        geom = _geometry(flats, lw)
        ident["geometry"] = geom
        role = _role_kind(exp.get("semantic_role"))
        role_text = exp.get("semantic_role") or _c(root, "submodel")
        if not role:
            checks.skipped("role_geometry",
                           "no recognised semantic role; observed geometry "
                           "is %s" % geom.get("label"), critical=False)
        elif role.startswith("fr02"):
            problems = []
            if role == "fr02-c" and not geom["cross_lane"]:
                problems.append("FR02-c requires cross-lane, observed %s"
                                % geom["label"])
            if role == "fr02-d" and not geom["cross_field"]:
                problems.append("FR02-d requires cross-field, fields=%s"
                                % geom["fields"])
            if role == "fr02-a" and not geom["adjacent"]:
                problems.append("FR02-a requires adjacency, bits=%s" % flats)
            if role == "fr02-b" and not (geom["same_lane"]
                                         and not geom["adjacent"]):
                problems.append("FR02-b requires same-lane non-adjacent, "
                                "bits=%s" % flats)
            if role == "fr02-d" and exp.get("lane_offset") is not None \
                    and exp["lane_offset"] >= 0 and lw >= 64:
                if geom["lanes"] != [exp["lane_offset"]]:
                    problems.append("FR02-d directed lane %s, observed lanes "
                                    "%s" % (exp["lane_offset"],
                                            geom["lanes"]))
            if problems:
                checks.failed("role_geometry", "; ".join(problems),
                              source=["prop_evt.txt", "config.ini"])
            else:
                checks.passed("role_geometry",
                              "%s matches observed geometry %s (lanes=%s "
                              "fields=%s)"
                              % (role_text, geom.get("field_label")
                                 or geom.get("label"),
                                 geom["lanes"], geom["fields"]),
                              source=["prop_evt.txt", "config.ini"])
        else:
            # FR01 family: the workbook splits FP64/FP32/NEON lanes.
            problems = []
            if role == "fr01-a" and lw != 64:
                problems.append("FR01-a (FP64) requires lane_width=64, got %s"
                                % lw)
            if role == "fr01-b" and lw != 32:
                problems.append("FR01-b (FP32) requires lane_width=32, got %s"
                                % lw)
            if role in ("fr01-a", "fr01-b") and flats:
                bit = _bit_in_lane(flats[0], lw)
                if lw == 64:
                    fld = ("sign" if bit == 63 else
                           "exp" if 52 <= bit <= 62 else "mant")
                else:
                    fld = ("sign" if bit == 31 else
                           "exp" if 23 <= bit <= 30 else "mant")
                ident["candidate_fp_field"] = fld
            if problems:
                checks.failed("role_geometry", "; ".join(problems),
                              source=["prop_evt.txt", "config.ini"])
            else:
                checks.passed("role_geometry",
                              "%s lane width %s consistent with the workbook"
                              % (role_text or role, lw),
                              source=["prop_evt.txt", "config.ini"])

    # -- precision / field labels (not emitted by this C++ path) ----------
    precision = _c(root, "precision")
    if exp.get("precision"):
        if not precision:
            checks.skipped(
                "precision",
                "manifest precision=%s but the transient event carries no "
                "`precision` field (C++ does not emit it); cannot verify"
                % exp["precision"], critical=False,
                source=["config.ini/expect.json", "prop_evt.txt"])
        elif precision.lower() != str(exp["precision"]).lower():
            checks.failed("precision",
                          "manifest precision=%s, root precision=%s"
                          % (exp["precision"], precision))
        else:
            checks.passed("precision",
                          "root precision=%s matches the manifest" % precision)
    else:
        checks.skipped("precision",
                       "no precision in manifest; transient events also emit "
                       "precision= (empty)", critical=False)
    field = _c(root, "field")
    if field == "transient_bit_flip":
        checks.skipped(
            "field_semantics",
            "field=transient_bit_flip only; sign/exp/mant and FP32/FP64 "
            "labels are not emitted (candidate from bit position: %s)"
            % ident.get("candidate_fp_field", "n/a"), critical=False,
            source=["prop_evt.txt"])
    else:
        checks.skipped("field_semantics",
                       "field=%r does not identify the FP field" % field,
                       critical=False)

    ident["carrier_cell_allocated"] = None
    return ident


def _check_carrier(checks, root, fault_events, exp, sources):
    fid = _c(root, "fault_id")
    carriers = [e for e in fault_events if _c(e, "kind") == "carrier_state"]
    if len(carriers) != 1:
        checks.failed("carrier_state",
                      "%d carrier_state event(s) for fault %s (expected 1)"
                      % (len(carriers), fid))
        return
    c = carriers[0]
    problems = []
    ident = {
        "reg_class": "vec",
        "phys_reg": _i(root, "phys_reg"),
        "reg_generation": _i(root, "reg_generation"),
        "lane_width": _i(root, "lane_width"),
        "lane_offset": _i(root, "lane_offset"),
        "lane_mask": _hexval(_c(root, "lane_mask"), 64),
        "bit_indices": _c(root, "bit_indices"),
    }
    for key, value in ident.items():
        if _c(c, key) != _c(root, key):
            problems.append("%s: carrier=%r root=%r"
                            % (key, _c(c, key), _c(root, key)))
    if _i(c, "parent_event_id") != _i(root, "event_id"):
        problems.append("parent_event_id=%s != root event_id=%s"
                        % (_c(c, "parent_event_id"), _c(root, "event_id")))
    if _c(c, "install_event") != _c(root, "event_id"):
        problems.append("install_event=%s != root event_id=%s"
                        % (_c(c, "install_event"), _c(root, "event_id")))
    if _c(c, "before") != _c(root, "after"):
        problems.append("carrier before=%s != root after=%s"
                        % (_c(c, "before"), _c(root, "after")))
    if _c(c, "after") != _c(root, "after"):
        problems.append("carrier after=%s != root after=%s"
                        % (_c(c, "after"), _c(root, "after")))
    if exp.get("require_allocated") and _c(c, "cell_allocated") != "1":
        problems.append("requireAllocated=true but cell_allocated=%r"
                        % _c(c, "cell_allocated"))
    if problems:
        checks.failed("carrier_state", "; ".join(problems),
                      source=["prop_evt.txt"])
    else:
        checks.passed("carrier_state",
                      "L1 carrier holds the flipped value at generation %s"
                      % _c(root, "reg_generation"),
                      source=["prop_evt.txt"])


def _check_run_identity(checks, root, fault_events, exp, sources):
    rid = _c(root, "run_id")
    sid = _c(root, "sample_run_id")
    problems = []
    if not rid:
        problems.append("root run_id is empty")
    if not sid:
        problems.append("root sample_run_id is empty")
    if exp.get("run_id") and rid != exp["run_id"]:
        problems.append("root run_id=%s != manifest %s"
                        % (rid, exp["run_id"]))
    if exp.get("sample_run_id") and sid != exp["sample_run_id"]:
        problems.append("root sample_run_id=%s != manifest %s"
                        % (sid, exp["sample_run_id"]))
    for e in fault_events:
        if _c(e, "run_id") != rid or _c(e, "sample_run_id") != sid:
            problems.append("event %s carries run_id=%r sample_run_id=%r"
                            % (_c(e, "event_id"), _c(e, "run_id"),
                               _c(e, "sample_run_id")))
            break
    if problems:
        checks.failed("run_identity", "; ".join(problems),
                      source=["prop_evt.txt", "config.ini"])
    else:
        checks.passed("run_identity",
                      "run_id=%s sample_run_id=%s on every lifecycle event"
                      % (rid, sid), source=["prop_evt.txt", "config.ini"])


def _check_config_conforms(checks, root, exp, sources, cfg):
    problems = []
    if exp.get("fault_type") and exp["fault_type"] != "bit_flip":
        problems.append("faultType=%s is not bit_flip; a permanent path "
                        "cannot be judged by this transient gate"
                        % exp["fault_type"])
    if exp.get("injection_mode") and exp["injection_mode"] != "phys":
        problems.append("injectionMode=%s (FR01/FR02 evidence assumes phys)"
                        % exp["injection_mode"])
    if exp.get("reg_target_class") and \
            exp["reg_target_class"].lower() not in ("vector", "both"):
        problems.append("regTargetClass=%s cannot target VecRegClass"
                        % exp["reg_target_class"])
    if _c(root, "reg_class") != "vec":
        problems.append("root reg_class=%r != vec" % _c(root, "reg_class"))

    # Physical cell identity vs the command: only a pinned index is
    # comparable. -1 means the simulator chose; the log/event chain must then
    # be internally consistent instead.
    phys = _i(root, "phys_reg")
    target = exp.get("phys_reg")
    if target is None:
        target = exp.get("target_phys_idx")
    if phys is None:
        problems.append("root phys_reg is missing")
    else:
        nregs = exp.get("num_phys_vec_regs")
        if nregs is not None and not (0 <= phys < nregs):
            problems.append("phys_reg=%s outside numPhysVecRegs=%s"
                            % (phys, nregs))
        if target is not None and target >= 0 and phys != target:
            problems.append("phys_reg=%s != pinned target %s"
                            % (phys, target))
    if exp.get("lane_width") is not None and \
            _i(root, "lane_width") != exp["lane_width"]:
        problems.append("root lane_width=%s != manifest %s"
                        % (_c(root, "lane_width"), exp["lane_width"]))
    if exp.get("lane_offset") is not None and exp["lane_offset"] >= 0 and \
            _i(root, "lane_offset") != exp["lane_offset"]:
        problems.append("root lane_offset=%s != directed manifest lane %s"
                        % (_c(root, "lane_offset"), exp["lane_offset"]))
    if exp.get("max_faults") is not None and exp["max_faults"] not in (0, 1):
        problems.append("maxFaults=%s is not an F0 one-shot command"
                        % exp["max_faults"])
    if problems:
        checks.failed("config_conforms", "; ".join(problems),
                      source=["prop_evt.txt", "config.ini/expect.json"])
    else:
        done = "phys_reg=%s" % phys
        if target is not None and target >= 0:
            done += " matches pinned target %s" % target
        checks.passed("config_conforms",
                      "vecRegClass/phys mode/bit_flip/lane parameters agree "
                      "with the command (%s)" % done,
                      source=["prop_evt.txt", "config.ini/expect.json"])


def _check_log_crosscheck(checks, root, log, exp, sources):
    if not log["exists"]:
        checks.skipped("fault_log_crosscheck",
                       "fault_injections.log absent; no command-log "
                       "cross-check", critical=False)
        return
    problems = []
    if len(log["installs"]) != 1:
        problems.append("%d VecTransientInstall line(s)" % len(log["installs"]))
    else:
        line = log["installs"][0]
        checks_map = [
            ("phys", "phys_reg"), ("gen", "reg_generation"),
            ("bits", "bit_indices"), ("lane", "lane_offset"),
            ("lane_width", "lane_width"),
        ]
        for log_key, root_key in checks_map:
            if log_key in line and _c(root, root_key) != str(line[log_key]):
                problems.append("log %s=%s != root %s=%s"
                                % (log_key, line[log_key], root_key,
                                   _c(root, root_key)))
        if "model" in line and _c(root, "model_id") != line["model"]:
            problems.append("log model=%s != root model_id=%s"
                            % (line["model"], _c(root, "model_id")))
    if log["fail_closed"]:
        problems.append("both VecTransientInstall and VecFaultFailClosed "
                        "present")
    if len(log["summaries"]) != 1:
        problems.append("%d injection summary line(s)"
                        % len(log["summaries"]))
    else:
        s = log["summaries"][0]
        if s.get("mode") != "phys":
            problems.append("log Mode=%s" % s.get("mode"))
        if s.get("cls") != "vec":
            problems.append("log RegClass=%s" % s.get("cls"))
        if s.get("ftype") != "bit_flip":
            problems.append("log FaultType=%s" % s.get("ftype"))
        if _c(root, "phys_reg") and s.get("phys") != _c(root, "phys_reg"):
            problems.append("log PhysReg[%s] != root phys_reg=%s"
                            % (s.get("phys"), _c(root, "phys_reg")))
        if _c(root, "arch_reg") and "ArchReg[" in s.get("state", ""):
            m = re.search(r"ArchReg\[(\d+)\]", s.get("state", ""))
            if m and m.group(1) != _c(root, "arch_reg"):
                problems.append("log ArchReg[%s] != root arch_reg=%s"
                                % (m.group(1), _c(root, "arch_reg")))
        role = exp.get("semantic_role") or ""
        if role and role not in s.get("state", ""):
            # semanticRole is logged after the PhysReg state text; search the
            # raw log line through the stored summary is not enough, so only
            # flag when a role is visible elsewhere and differs.
            pass
    if problems:
        checks.failed("fault_log_crosscheck", "; ".join(problems),
                      source=["fault_injections.log", "prop_evt.txt"])
    else:
        checks.passed("fault_log_crosscheck",
                      "install log/summary identity agrees with the L0 root",
                      source=["fault_injections.log", "prop_evt.txt"])


# ---------------------------------------------------------------------------
# Lifecycle checks
# ---------------------------------------------------------------------------
def _check_lifecycle(checks, root, fault_events, exp, sources, stats,
                     evidence):
    fid = _c(root, "fault_id")
    target = _c(root, "phys_reg")
    install_gen = _i(root, "reg_generation")
    install_event = _i(root, "event_id")
    lw = _i(root, "lane_width")
    lo = _i(root, "lane_offset")
    root_after = _hexval(_c(root, "after"), 64)

    by_kind = {}
    ids = {}
    for e in fault_events:
        by_kind.setdefault(_c(e, "kind"), []).append(e)
        eid = _i(e, "event_id")
        if eid is not None:
            ids[eid] = e
    reads = by_kind.get("operand_read", [])
    commits = by_kind.get("commit", [])
    squashes = by_kind.get("squash", [])
    overwrites = by_kind.get("overwrite", [])
    post_reads = by_kind.get("post_overwrite_read", [])
    post_writes = by_kind.get("write_after_overwrite", [])
    chain_ends = by_kind.get("chain_end", [])
    gen_events = []
    for kind in ("generation_change", "cell_free", "cell_realloc", "free",
                 "realloc", "alloc", "cell_reuse"):
        gen_events.extend(by_kind.get(kind, []))
    stuck_events = []
    for kind in STUCK_KINDS:
        stuck_events.extend(by_kind.get(kind, []))

    counts = {
        "operand_read": len(reads),
        "commit": len(commits),
        "squash": len(squashes),
        "overwrite": len(overwrites),
        "post_overwrite_read": len(post_reads),
        "write_after_overwrite": len(post_writes),
        "chain_end": len(chain_ends),
        "generation": len(gen_events),
        "stuck": len(stuck_events),
    }

    # -- event integrity --------------------------------------------------
    problems = []
    for e in fault_events:
        kind = _c(e, "kind")
        if kind in ("fault_applied",):
            continue
        if _c(e, "reg_class") not in ("", "vec"):
            problems.append("%s reg_class=%r" % (kind, _c(e, "reg_class")))
        if kind in ("operand_read", "commit", "squash", "overwrite",
                    "chain_end") and _c(e, "phys_reg") != target:
            problems.append("%s phys_reg=%s != root %s"
                            % (kind, _c(e, "phys_reg"), target))
        parent = _i(e, "parent_event_id")
        if parent is not None and parent not in ids:
            problems.append("%s parent_event_id=%s not in this fault"
                            % (kind, parent))
        if kind == "commit":
            if _c(e, "detection_layer") != "L5":
                problems.append("commit detection_layer=%r"
                                % _c(e, "detection_layer"))
            if _c(e, "outcome") != "errant_commit":
                problems.append("commit outcome=%r" % _c(e, "outcome"))
            if _c(e, "contained") == "1":
                problems.append("commit claimed contained=1")
        if kind == "squash":
            if _c(e, "detection_layer"):
                problems.append("squash claims detection_layer=%r"
                                % _c(e, "detection_layer"))
            if _c(e, "outcome") != "squashed" or _c(e, "squashed") != "1":
                problems.append("squash outcome/squashed flag inconsistent")
        if kind == "overwrite":
            if _c(e, "detection_layer") != "L1":
                problems.append("overwrite detection_layer=%r"
                                % _c(e, "detection_layer"))
            if _c(e, "contained") != "1":
                problems.append("overwrite contained=%r"
                                % _c(e, "contained"))
            if _c(e, "containment_layer") != "L1":
                problems.append("overwrite containment_layer=%r"
                                % _c(e, "containment_layer"))
            if _c(e, "containment_reason") != "phys_cell_rewritten":
                problems.append("overwrite containment_reason=%r"
                                % _c(e, "containment_reason"))
            if _c(e, "producer_seq") and \
                    _c(e, "producer_seq") != _c(e, "dyn_inst_seq"):
                problems.append("overwrite producer_seq != dyn_inst_seq")
            gen = _i(e, "reg_generation")
            if gen is not None and install_gen is not None and \
                    gen < install_gen:
                problems.append("overwrite generation %s < install %s"
                                % (gen, install_gen))
        if kind == "chain_end":
            if _c(e, "detection_layer"):
                problems.append("chain_end claims detection_layer=%r "
                                "(lifecycle marker, not a layer)"
                                % _c(e, "detection_layer"))
    # Consumer identity: a recorded read must show the flipped lane value and
    # the install generation.
    read_by_seq = {}
    for e in reads:
        seq = _c(e, "consumer_seq")
        if not seq:
            problems.append("operand_read without consumer_seq")
            continue
        if _c(e, "consumer_seq") != _c(e, "dyn_inst_seq"):
            problems.append("operand_read consumer_seq != dyn_inst_seq")
        gen = _i(e, "reg_generation")
        if gen is not None and install_gen is not None and gen != install_gen:
            problems.append("operand_read gen=%s != install gen=%s"
                            % (gen, install_gen))
        observed = _hexval(_c(e, "before"), 64)
        if observed is not None and root_after is not None and \
                observed != root_after:
            problems.append("operand_read lane=0x%x != injected lane=0x%x"
                            % (observed, root_after))
        if _c(e, "before") != _c(e, "after"):
            problems.append("operand_read before != after (not an observation)")
        read_by_seq[seq] = e
    # Terminal consumers must point at their exact L2 read event.
    for kind, groups in (("commit", commits), ("squash", squashes)):
        for e in groups:
            seq = _c(e, "consumer_seq")
            rd = read_by_seq.get(seq)
            if rd is None:
                problems.append("%s consumer_seq=%s has no operand_read"
                                % (kind, seq))
                continue
            if _c(e, "parent_event_id") != _c(rd, "event_id"):
                problems.append("%s parent=%s != read event=%s"
                                % (kind, _c(e, "parent_event_id"),
                                   _c(rd, "event_id")))
            if _i(e, "reg_generation") != _i(rd, "reg_generation"):
                problems.append("%s gen=%s != read gen=%s"
                                % (kind, _c(e, "reg_generation"),
                                   _c(rd, "reg_generation")))
            if _hexval(_c(e, "before"), 64) != \
                    _hexval(_c(rd, "before"), 64):
                problems.append("%s value != read value" % kind)

    if problems:
        checks.failed("lifecycle_event_integrity", "; ".join(problems),
                      source=["prop_evt.txt"])
    else:
        checks.passed("lifecycle_event_integrity",
                      "all lifecycle events share cell=%s generation=%s; "
                      "commit/squash/overwrite fields are layer-correct"
                      % (target, install_gen), source=["prop_evt.txt"])

    # -- consecutive writes / permanent-stuck proof -----------------------
    allow_multi = bool(exp.get("allow_multiple_overwrites"))
    if len(overwrites) > 1 and not allow_multi:
        checks.failed("write_sequence",
                      "%d overwrite events; the current emitter observes "
                      "only the first real write, so a multi-write claim is "
                      "not supported by this evidence" % len(overwrites),
                      source=["prop_evt.txt"])
    if stuck_events:
        checks.failed("consecutive_writes_not_stuck",
                      "transient chain contains permanent-cell event(s): %s"
                      % [_c(e, "kind") for e in stuck_events],
                      source=["prop_evt.txt"])
    elif post_writes:
        ce = chain_ends[-1] if chain_ends else {}
        wt = _i(ce, "post_overwrite_writes_total")
        we = _i(ce, "post_overwrite_writes_emitted")
        wa = _i(ce, "post_overwrite_writes_affected")
        bad = []
        if None in (wt, we, wa):
            bad.append("post-overwrite write counters missing")
        elif wt != we:
            bad.append("post-overwrite writes not fully observed (%s/%s)"
                       % (we, wt))
        elif wa != 0:
            bad.append("%s post-overwrite write(s) re-flipped the target"
                       % wa)
        for e in post_writes:
            if _c(e, "target_bits_flipped") != "0":
                bad.append("post-overwrite write at sn=%s still saw a "
                           "flipped target bit" % _c(e, "dyn_inst_seq"))
        if bad:
            checks.failed("consecutive_writes_not_stuck", "; ".join(bad),
                          source=["prop_evt.txt"])
        else:
            checks.passed(
                "consecutive_writes_not_stuck",
                "%d post-overwrite real write(s) observed, none re-applied "
                "the transient (affected=0, all observed)" % len(post_writes),
                source=["prop_evt.txt"])
    elif len(overwrites) < 2:
        checks.skipped(
            "consecutive_writes_not_stuck",
            "only %d overwrite event(s) and no post-overwrite write "
            "observation; 'consecutive writes never re-stick' is not "
            "provable from this stream" % len(overwrites), critical=False,
            source=["prop_evt.txt"])
    else:
        bad = []
        for i in range(1, len(overwrites)):
            prev = overwrites[i - 1]
            cur = overwrites[i]
            if _c(cur, "before") != _c(prev, "after"):
                bad.append("write %d before=%s != previous after=%s "
                           "(defect re-applied between real writes)"
                           % (i, _c(cur, "before"), _c(prev, "after")))
        if bad:
            checks.failed("consecutive_writes_not_stuck", "; ".join(bad),
                          source=["prop_evt.txt"])
        else:
            checks.passed("consecutive_writes_not_stuck",
                          "%d consecutive real writes, no re-application: "
                          "each before equals the previous written value"
                          % len(overwrites), source=["prop_evt.txt"])

    # -- derived closure --------------------------------------------------
    if commits:
        closure = "committed"
    elif overwrites:
        closure = "overwritten"
    elif squashes:
        closure = "squashed"
    elif gen_events:
        closure = "free_realloc"
    elif reads:
        closure = "exposed_unconsumed"
    else:
        closure = "not_consumed"

    # -- overwrite phase: before any consumer, or after reads but before any
    #    commit?  Both are contained-by-write closures, but they are different
    #    evidence and must not be conflated.
    overwrite_phase = None
    if overwrites:
        wtick = _i(overwrites[0], "tick")
        late = [r for r in reads
                if _i(r, "tick") is not None and wtick is not None
                and _i(r, "tick") > wtick]
        if late:
            overwrite_phase = "post_overwrite_read"
            checks.failed(
                "overwrite_phase",
                "%d operand_read event(s) after the overwrite tick %s; the "
                "current C++ observer suppresses post-overwrite reads, so "
                "this stream is not from the known emitter"
                % (len(late), wtick), source=["prop_evt.txt"])
        elif reads:
            overwrite_phase = "after_consumer_reads_no_commit"
            checks.passed(
                "overwrite_phase",
                "overwrite tick %s follows %d consumer read(s) and no commit; "
                "the fault was exposed but contained by a later real write"
                % (wtick, len(reads)), source=["prop_evt.txt"])
        else:
            overwrite_phase = "before_any_consumer_read"
            checks.passed(
                "overwrite_phase",
                "overwrite tick %s happened before any consumer read"
                % wtick, source=["prop_evt.txt"])
    else:
        checks.skipped("overwrite_phase",
                       "no overwrite event; phase is not applicable",
                       critical=False, source=["prop_evt.txt"])

    if gen_events:
        checks.passed("free_realloc_evidence",
                      "generation/free events for the transient fault: %s"
                      % [_c(e, "kind") for e in gen_events],
                      source=["prop_evt.txt"])
    else:
        checks.skipped("free_realloc_evidence",
                       "no transient free/realloc/generation_change event is "
                       "emitted; free/realloc closure cannot be observed",
                       critical=False, source=["prop_evt.txt"])

    # -- chain_end terminal honesty ---------------------------------------
    recorded_terminal = None
    if len(chain_ends) == 0:
        checks.failed("terminal_honesty",
                      "no chain_end for fault %s: lifecycle is not closed" % fid)
    elif len(chain_ends) > 1:
        checks.failed("terminal_honesty",
                      "%d chain_end events for fault %s" % (len(chain_ends), fid))
    else:
        ce = chain_ends[0]
        recorded_terminal = _c(ce, "terminal")
        problems = []
        if recorded_terminal != closure:
            problems.append("chain_end terminal=%r but the events derive %r"
                            % (recorded_terminal, closure))
        # `TERMINALS` is the semantic vocabulary this gate can certify.
        # `EMITTED_TERMINALS` is what the CURRENT finalizeVecTransient()
        # emits; "squashed"/"free_realloc" are valid semantics that C++ does
        # not emit yet, so they are accepted here and the emitter gap is
        # reported separately in the documentation/blockers.
        if recorded_terminal not in TERMINALS:
            problems.append("terminal=%r is outside the semantic vocabulary %s"
                            % (recorded_terminal, list(TERMINALS)))
        if _c(ce, "phys_reg") != target:
            problems.append("chain_end phys_reg=%s != %s"
                            % (_c(ce, "phys_reg"), target))
        if _i(ce, "reg_generation") != install_gen:
            problems.append("chain_end reg_generation=%s != install %s"
                            % (_c(ce, "reg_generation"), install_gen))
        if _i(ce, "install_event") != install_event:
            problems.append("chain_end install_event=%s != root event %s"
                            % (_c(ce, "install_event"), install_event))
        for key in ("lane_width", "lane_offset", "lane_mask", "bit_indices"):
            if _c(ce, key) != _c(root, key):
                problems.append("chain_end %s=%r != root %r"
                                % (key, _c(ce, key), _c(root, key)))
        want_contained = "1" if closure == "overwritten" else "0"
        if _c(ce, "contained") != want_contained:
            problems.append("chain_end contained=%r, closure %s requires %s"
                            % (_c(ce, "contained"), closure, want_contained))
        counters = {
            "commit_events": len(commits),
            "squash_events": len(squashes),
            "read_exposures_total": len(reads),
            "write_exposures_total": 1 + len(overwrites),
        }
        for key, want in counters.items():
            got = _i(ce, key)
            if got is None:
                problems.append("chain_end %s missing" % key)
            elif got != want:
                problems.append("chain_end %s=%s != observed %s"
                                % (key, got, want))
        pending = len(set(_c(e, "consumer_seq") for e in reads))
        got = _i(ce, "consumers_recorded")
        if got is not None and got != pending:
            problems.append("chain_end consumers_recorded=%s != distinct "
                            "read consumers %s" % (got, pending))
        if commits:
            first_commit_sn = _i(commits[0], "consumer_seq")
            if _i(ce, "first_impact_sn") != first_commit_sn:
                problems.append("chain_end first_impact_sn=%s != first "
                                "commit seq %s"
                                % (_c(ce, "first_impact_sn"),
                                   first_commit_sn))
            if _i(ce, "l5_witness_event") != _i(commits[0], "event_id"):
                problems.append("chain_end l5_witness_event=%s != commit "
                                "event %s"
                                % (_c(ce, "l5_witness_event"),
                                   _c(commits[0], "event_id")))
        if overwrites:
            if _i(ce, "affected_sn") != _i(overwrites[-1], "dyn_inst_seq"):
                problems.append("chain_end affected_sn=%s != last write sn %s"
                                % (_c(ce, "affected_sn"),
                                   _c(overwrites[-1], "dyn_inst_seq")))
        # chain_end must be the last event of this fault.
        ce_tick = _i(ce, "tick")
        later = [e for e in fault_events
                 if _i(e, "tick") is not None and ce_tick is not None
                 and _i(e, "tick") > ce_tick]
        if later:
            problems.append("%d event(s) after chain_end tick" % len(later))
        if problems:
            checks.failed("terminal_honesty", "; ".join(problems),
                          source=["prop_evt.txt"])
        else:
            checks.passed("terminal_honesty",
                          "chain_end terminal=%s is exactly the event-derived "
                          "closure; counters match the stream"
                          % recorded_terminal, source=["prop_evt.txt"])

    events_summary = {
        "overwrite_phase": overwrite_phase,
        "first_read_tick": _i(reads[0], "tick") if reads else None,
        "overwrite_tick": _i(overwrites[0], "tick") if overwrites else None,
        "operand_read_sns": sorted(set(_c(e, "consumer_seq") for e in reads)),
        "commit_sns": sorted(set(_c(e, "consumer_seq") for e in commits)),
        "squash_sns": sorted(set(_c(e, "consumer_seq") for e in squashes)),
        "overwrite_sns": [_c(e, "dyn_inst_seq") for e in overwrites],
        "install_generation": install_gen,
        "overwrite_generation": [_c(e, "reg_generation") for e in overwrites],
        "counts": counts,
    }
    return {
        "closure": closure,
        "recorded_terminal": recorded_terminal,
        "certified_closure": checks.overall() == STATUS_PASS,
        "events": events_summary,
        "chain_end_tick": _i(chain_ends[0], "tick") if chain_ends else None,
    }


def _check_no_permanent(checks, root, fault_events, log, stats, exp, sources):
    problems = []
    kinds = [_c(e, "kind") for e in fault_events]
    bad = [k for k in kinds if k in STUCK_KINDS]
    if bad:
        problems.append("permanent-cell event(s) in a transient chain: %s"
                        % bad)
    if _c(root, "field") != "transient_bit_flip":
        problems.append("root field=%r != transient_bit_flip"
                        % _c(root, "field"))
    if exp.get("fault_type") and exp["fault_type"] != "bit_flip":
        problems.append("faultType=%s" % exp["fault_type"])
    if problems:
        checks.failed("no_permanent_arm", "; ".join(problems),
                      source=["prop_evt.txt", "stats.txt"])
    else:
        checks.passed("no_permanent_arm",
                      "transient path armed nothing: no fault_installed/"
                      "stuck_reapplied/phys_write event and field="
                      "transient_bit_flip", source=["prop_evt.txt"])
    # The permanent counters are a separate, stats-only witness. Missing
    # stats is evidence_missing (SKIP), never a fabricated zero.
    if not stats:
        checks.skipped("permanent_counters",
                       "stats.txt missing: numPermanentFaults/stuck counters "
                       "unverifiable", critical=False, source=["stats.txt"])
    else:
        nperm = _stat(stats, "numPermanentFaults")
        nsz = _stat(stats, "numStuckAtZero")
        nso = _stat(stats, "numStuckAtOne")
        bad = []
        if nperm not in (None, 0):
            bad.append("numPermanentFaults=%s" % nperm)
        if nsz not in (None, 0):
            bad.append("numStuckAtZero=%s" % nsz)
        if nso not in (None, 0):
            bad.append("numStuckAtOne=%s" % nso)
        if bad:
            checks.failed("permanent_counters", "; ".join(bad),
                          source=["stats.txt"])
        else:
            checks.passed("permanent_counters",
                          "numPermanentFaults=0 stuckAtZero=0 stuckAtOne=0",
                          source=["stats.txt"])


def _check_boundary(checks, root, fault_events, lc, stats, exp, sources):
    if not stats:
        checks.skipped("run_boundary",
                       "stats.txt missing: run end cannot be anchored",
                       critical=True)
        return
    simticks = _stat(stats, "simTicks")
    siminsts = _stat(stats, "simInsts")
    problems = []
    if simticks is None or siminsts is None or siminsts <= 0:
        problems.append("stats.txt lacks a completed-run simTicks/simInsts")
    ce_tick = lc.get("chain_end_tick")
    if ce_tick is not None and simticks is not None and ce_tick > simticks:
        problems.append("chain_end tick %s > simTicks %s"
                        % (ce_tick, simticks))
    nf = _stat(stats, "numFaultsInjected")
    nbf = _stat(stats, "numBitFlips")
    maxf = exp.get("max_faults")
    if nf is None or nbf is None:
        problems.append("stats.txt lacks numFaultsInjected/numBitFlips")
    else:
        want = 1 if maxf in (None, 0, 1) else None
        if want is not None and nf != want:
            problems.append("numFaultsInjected=%s (F0 one-shot expects %s)"
                            % (nf, want))
        if want is not None and nbf != want:
            problems.append("numBitFlips=%s (expects %s)" % (nbf, want))
    if problems:
        checks.failed("run_boundary", "; ".join(problems),
                      source=["stats.txt", "prop_evt.txt"])
    else:
        checks.passed("run_boundary",
                      "chain_end tick %s <= simTicks %s; stats confirm one "
                      "bit-flip injection and a completed run"
                      % (ce_tick, simticks),
                      source=["stats.txt", "prop_evt.txt"])


# ---------------------------------------------------------------------------
# Certification blocks
# ---------------------------------------------------------------------------
def _hex128(text):
    text = str(text or "").strip()
    if text.lower().startswith("0x"):
        text = text[2:]
    if not text:
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


def _containment_evidence(root, events):
    """Prove (or refuse to prove) that a real overwrite removed the defect.

    Requires the post-overwrite emitter: the overwrite event must carry the
    128-bit flipped value and mask, and chain_end must carry observed
    post-overwrite read/write totals.  Old streams without those fields are
    reported `evidence_missing`, never assumed contained.
    """
    by_kind = {}
    for e in events:
        by_kind.setdefault(_c(e, "kind"), []).append(e)
    overwrites = by_kind.get("overwrite", [])
    post_reads = by_kind.get("post_overwrite_read", [])
    post_writes = by_kind.get("write_after_overwrite", [])
    chain_ends = by_kind.get("chain_end", [])
    if not overwrites:
        # Free/realloc terminal: the installed generation no longer exists.
        gen = []
        for kind in ("generation_change", "cell_free", "cell_realloc",
                     "free", "realloc", "cell_reuse"):
            gen.extend(by_kind.get(kind, []))
        if not gen:
            return None
        change = gen[0]
        install_gen = _i(root, "reg_generation")
        old = _i(change, "generation_old")
        new = _i(change, "generation_new")
        missing = []
        if old is None or new is None:
            missing.append("generation change old/new missing")
        elif install_gen is not None and old != install_gen:
            missing.append("generation change old=%s != install=%s"
                           % (old, install_gen))
        elif new == old:
            missing.append("generation change did not change the generation")
        change_tick = _i(change, "tick")
        late_reads = [e for e in by_kind.get("operand_read", [])
                      if install_gen is not None
                      and _i(e, "reg_generation") == install_gen
                      and (change_tick is None
                           or (_i(e, "tick") or 0) > change_tick)]
        if late_reads:
            missing.append("%d read(s) of the installed generation after "
                           "reallocation" % len(late_reads))
        ce = chain_ends[-1] if chain_ends else {}
        if _i(ce, "commit_events") not in (0, None):
            missing.append("a consumer committed before the cell was "
                           "reallocated")
        return {
            "certified": not missing,
            "kind": "free_realloc",
            "generation_old": old,
            "generation_new": new,
            "missing": missing,
        }
    ow = overwrites[0]
    ce = chain_ends[-1] if chain_ends else {}
    missing = []
    full_before = _hex128(_c(ow, "full_before"))
    full_after = _hex128(_c(ow, "full_after"))
    mask = _hex128(_c(ow, "fault_mask"))
    restored = _c(ow, "target_bits_restored") == "1"
    if not restored and None not in (full_before, full_after, mask):
        restored = ((full_before ^ full_after) & mask) == mask
    install_gen = _i(root, "reg_generation")
    ow_gen = _i(ow, "reg_generation")
    if install_gen is not None and ow_gen is not None and \
            ow_gen != install_gen:
        missing.append("overwrite generation %s != install generation %s"
                       % (ow_gen, install_gen))
    if full_before is None or mask is None:
        missing.append("overwrite full_before/fault_mask")
    elif not restored:
        missing.append("target bits not restored by the overwrite")
    if _c(ce, "post_overwrite_reads_total") == "":
        missing.append("post-overwrite read observation counters")
    else:
        rt = _i(ce, "post_overwrite_reads_total")
        re_ = _i(ce, "post_overwrite_reads_emitted")
        ra = _i(ce, "post_overwrite_affected_reads")
        if None in (rt, re_, ra):
            missing.append("post-overwrite read counters malformed")
        elif rt != re_:
            missing.append("post-overwrite reads not fully observed "
                           "(%s/%s)" % (re_, rt))
        elif ra != 0:
            missing.append("%s post-overwrite affected read(s)" % ra)
        elif any(_c(e, "same_generation") == "1"
                 and _c(e, "target_bits_flipped") != "0"
                 for e in post_reads):
            missing.append("a post-overwrite read still saw a flipped target "
                           "bit on the installed generation")
    if _c(ce, "post_overwrite_writes_total") == "":
        missing.append("post-overwrite write observation counters")
    else:
        wt = _i(ce, "post_overwrite_writes_total")
        we = _i(ce, "post_overwrite_writes_emitted")
        wa = _i(ce, "post_overwrite_writes_affected")
        if None in (wt, we, wa):
            missing.append("post-overwrite write counters malformed")
        elif wt != we:
            missing.append("post-overwrite writes not fully observed "
                           "(%s/%s)" % (we, wt))
        elif wa != 0:
            missing.append("%s post-overwrite write(s) re-flipped the target"
                           % wa)
        elif any(_c(e, "target_bits_flipped") != "0" for e in post_writes):
            missing.append("a later real write still saw a flipped target "
                           "bit")
    gen_changes = _i(ce, "generation_changes")
    # A generation change AFTER a same-generation overwrite is harmless: the
    # old cell (already cleaned) is simply freed. It does not invalidate the
    # overwrite's containment evidence.
    return {
        "certified": not missing,
        "kind": "overwrite",
        "restored": bool(restored),
        "post_overwrite_reads_total": _i(
            ce, "post_overwrite_reads_total"),
        "post_overwrite_reads_emitted": _i(
            ce, "post_overwrite_reads_emitted"),
        "post_overwrite_affected_reads": _i(
            ce, "post_overwrite_affected_reads"),
        "post_overwrite_writes_total": _i(
            ce, "post_overwrite_writes_total"),
        "post_overwrite_writes_emitted": _i(
            ce, "post_overwrite_writes_emitted"),
        "post_overwrite_writes_affected": _i(
            ce, "post_overwrite_writes_affected"),
        "generation_changes": gen_changes,
        "missing": missing,
    }


def _certification(closure, lc, status, containment=None):
    if status == STATUS_FAIL:
        return {
            "status": "FAILED",
            "verdict": "evidence_inconsistent",
            "missing": [],
        }
    if closure == "committed":
        return {
            "status": "CERTIFIED",
            "verdict": "l5_commit_witnessed",
            "basis": "a real operand_read of the flipped cell is the direct "
                     "parent of a commit event at detection_layer=L5, same "
                     "generation and value",
            "missing": ["oracle_diff/golden comparison (SDC vs benign)"],
        }
    if closure == "overwritten":
        c = containment or {}
        if c.get("certified"):
            return {
                "status": "CERTIFIED",
                "verdict": "contained_by_real_overwrite",
                "basis": "the overwrite restored every injected target bit "
                         "(full_before/fault_mask vs full_after) and every "
                         "observed post-overwrite read/write saw no flipped "
                         "target bit, with all observations accounted for",
                "missing": ["oracle_diff/golden comparison (SDC vs benign)"],
            }
        return {
            "status": "BLOCKED",
            "verdict": "l1_containment_event_only",
            "basis": "a real write to the target cell was observed "
                     "(overwrite, containment L1, phys_cell_rewritten) with "
                     "no consumer commit",
            "missing": (c.get("missing") or [
                "post-overwrite read/write visibility",
                "target-bit restoration by the overwrite"]) +
                ["oracle_diff/golden comparison"],
        }
    if closure == "squashed":
        return {
            "status": "BLOCKED",
            "verdict": "squash_witnessed_but_defect_may_still_be_live",
            "basis": "the only consumer(s) squashed; squash is not a commit "
                     "and does not clear the physical cell",
            "missing": ["an overwrite/free event after the squash",
                        "squashed terminal in the current emitter"],
        }
    if closure == "free_realloc":
        c = containment or {}
        if c.get("certified"):
            return {
                "status": "CERTIFIED",
                "verdict": "contained_by_free_realloc",
                "basis": "the installed generation was freed/reallocated "
                         "(generation_change old=%s new=%s); the defective "
                         "cell no longer exists and no later read of that "
                         "generation or commit was observed"
                         % (c.get("generation_old"),
                            c.get("generation_new")),
                "missing": ["oracle_diff/golden comparison (SDC vs benign)"],
            }
        return {
            "status": "BLOCKED",
            "verdict": "free_realloc_witnessed",
            "basis": "generation/free event(s) for the transient cell",
            "missing": (c.get("missing") or [
                "installed-generation free/realloc evidence"]) +
                ["oracle_diff/golden comparison"],
        }
    if closure == "exposed_unconsumed":
        return {
            "status": "BLOCKED",
            "verdict": "unknown_live_at_run_end",
            "basis": "consumer read(s) exist but no commit, squash, overwrite "
                     "or free event closes the fault",
            "missing": ["commit/squash/overwrite/free evidence",
                        "oracle_diff/golden comparison"],
        }
    return {
        "status": "BLOCKED",
        "verdict": "unknown_no_consumer",
        "basis": "no consumer read and no real write were observed before "
                 "run end",
        "missing": ["a consumer read", "an overwrite/free event",
                    "oracle_diff/golden comparison"],
    }


def _masked_certification(closure, lc, status, containment=None):
    base = {
        "certified": False,
        "final_hash_equality_alone_insufficient": True,
    }
    if status == STATUS_FAIL:
        base.update({
            "verdict": "BLOCKED",
            "reason": "evidence is inconsistent; no terminal claim can be "
                      "certified",
            "missing": ["consistent identity/lifecycle evidence"],
        })
        return base
    if closure == "committed":
        base.update({
            "verdict": "NOT_MASKED",
            "reason": "a consumer reached architectural commit; this is an "
                      "L5-exposed fault, not masked",
            "missing": ["oracle_diff/golden comparison to split SDC vs "
                        "benign"],
        })
        return base
    if closure == "overwritten":
        c = containment or {}
        present = ["L1 overwrite with containment_reason="
                   "phys_cell_rewritten",
                   "chain_end boundary after the overwrite"]
        if c.get("certified"):
            present += [
                "target bits restored",
                "post-overwrite reads fully observed (%s/%s, affected=%s)"
                % (c.get("post_overwrite_reads_emitted"),
                   c.get("post_overwrite_reads_total"),
                   c.get("post_overwrite_affected_reads")),
                "post-overwrite writes fully observed (%s/%s, affected=%s)"
                % (c.get("post_overwrite_writes_emitted"),
                   c.get("post_overwrite_writes_total"),
                   c.get("post_overwrite_writes_affected")),
            ]
            base.update({
                "certified": True,
                "verdict": "CONTAINED_BY_OVERWRITE",
                "reason": "the specified generation's defect is gone (target "
                          "bits restored) and no later affected read/write "
                          "was observed; the chain_end boundary is traceable. "
                          "This is containment, not an SDC/benign claim.",
                "present": present,
                "missing": ["oracle_diff/golden comparison (SDC vs benign)"],
            })
            return base
        base.update({
            "verdict": "BLOCKED",
            "reason": "the L1 overwrite event shows a real write, but Masked "
                      "requires the specified generation's defect to be gone "
                      "AND no later affected read/side effect AND a traceable "
                      "boundary. The stream does not provide the full "
                      "post-overwrite observation set.",
            "present": present,
            "missing": (c.get("missing") or []) +
                       ["oracle_diff/golden comparison"],
        })
        return base
    if closure == "free_realloc":
        c = containment or {}
        if c.get("certified"):
            base.update({
                "certified": True,
                "verdict": "CONTAINED_BY_FREE_REALLOC",
                "reason": "the installed generation was freed/reallocated; "
                          "the defective cell is gone, no later read of that "
                          "generation and no commit was observed. This is "
                          "containment, not an SDC/benign claim.",
                "present": [
                    "generation_change old=%s new=%s"
                    % (c.get("generation_old"), c.get("generation_new")),
                    "chain_end boundary after the reallocation",
                ],
                "missing": ["oracle_diff/golden comparison (SDC vs benign)"],
            })
            return base
        base.update({
            "verdict": "BLOCKED",
            "reason": "a generation/free event exists, but it does not yet "
                      "prove the installed generation is gone and unaffected.",
            "missing": (c.get("missing") or []) +
                       ["oracle_diff/golden comparison"],
        })
        return base
    if closure == "fail_closed":
        base.update({"verdict": "NOT_APPLICABLE",
                     "reason": "no fault injected", "missing": []})
        return base
    base.update({
        "verdict": "BLOCKED",
        "reason": "no terminal containment evidence; the fault may still be "
                  "live in the physical cell at run end. A matching final "
                  "hash does not prove Masked.",
        "missing": ["overwrite/free/commit/squash terminal",
                    "oracle_diff/golden comparison"],
    })
    return base


def _blockers(lc, masked, certification, containment=None):
    out = []
    if lc.get("closure") in ("exposed_unconsumed", "not_consumed"):
        out.append("fault state at run end is unknown: no commit, squash, "
                   "overwrite or free event")
    if lc.get("closure") == "squashed":
        out.append("defect may still be live after squash; no post-squash "
                   "overwrite/free evidence")
    if lc.get("closure") == "overwritten" and not (
            containment or {}).get("certified"):
        out.append("Masked cannot be certified: the stream lacks target-bit "
                   "restoration and/or full post-overwrite read/write "
                   "visibility")
    for item in masked.get("missing", []):
        if item not in out and "oracle" not in item:
            out.append(item)
    return out


def _reason_text(status, closure, lc, checks):
    if status == STATUS_FAIL:
        return "FAIL: " + "; ".join(checks.failures())
    if status == STATUS_SKIP:
        return "SKIP: required evidence missing: " + \
               "; ".join(checks.critical_skips())
    return ("PASS: lifecycle closed as %s (recorded terminal=%s); "
            "certification may still be BLOCKED"
            % (closure, lc.get("recorded_terminal")))


# ---------------------------------------------------------------------------
# Directory discovery / top-level analysis
# ---------------------------------------------------------------------------
def _is_attempt_dir(path):
    path = Path(path)
    if (path / "prop_evt.txt.gz").exists() or \
            (path / "prop_evt.txt").exists():
        return True
    return (path / "fault_injections.log").exists() and \
        (path / "config.ini").exists()


def discover_attempts(root):
    root = Path(root).resolve()
    if root.is_file():
        return [root.parent] if _is_attempt_dir(root.parent) else []
    if _is_attempt_dir(root):
        return [root]
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Never descend into a directory that is itself an attempt: its
        # m5out subfiles are not separate attempts.
        if dirpath != str(root) and _is_attempt_dir(dirpath):
            found.append(Path(dirpath).resolve())
            dirnames[:] = []
            continue
        dirnames.sort()
    found.sort()
    return found


def analyze_path(paths, cli_expect=None):
    roots = [Path(p).resolve() for p in paths]
    attempts = []
    for root in roots:
        attempts.extend(discover_attempts(root))
    # de-duplicate, drop attempts nested under another attempt
    uniq = []
    seen = set()
    for a in sorted(set(attempts)):
        if a in seen:
            continue
        if any(a != b and b in a.parents for b in attempts):
            continue
        uniq.append(a)
        seen.add(a)
    reports = []
    base = roots[0] if len(roots) == 1 else Path(os.path.commonpath(
        [str(r) for r in roots]))
    for a in uniq:
        try:
            rel = str(a.relative_to(base)) if a != base else "."
        except ValueError:
            rel = str(a)
        reports.append(analyze_attempt(a, cli_expect=cli_expect,
                                       rel_name=rel))
    summary = {
        "attempts_total": len(reports),
        STATUS_PASS: sum(1 for r in reports if r["status"] == STATUS_PASS),
        STATUS_FAIL: sum(1 for r in reports if r["status"] == STATUS_FAIL),
        STATUS_SKIP: sum(1 for r in reports if r["status"] == STATUS_SKIP),
        "certification": {
            "CERTIFIED": sum(1 for r in reports
                             if r["certification"]["status"] == "CERTIFIED"),
            "BLOCKED": sum(1 for r in reports
                           if r["certification"]["status"] == "BLOCKED"),
            "FAILED": sum(1 for r in reports
                          if r["certification"]["status"] == "FAILED"),
        },
        "run_ids": sorted(set(r.get("run_id") for r in reports
                              if r.get("run_id"))),
        "blockers": sorted(set(b for r in reports for b in r.get("blockers", []))),
    }
    return {
        "tool": TOOL,
        "version": TOOL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(roots[0]) if len(roots) == 1 else [str(r) for r in roots],
        "attempts": reports,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Read-only FR01/FR02 transient Vec bit-flip lifecycle "
                    "gate.")
    ap.add_argument("paths", nargs="+",
                    help="attempt directory or gate directory (read-only)")
    ap.add_argument("--json-out", default=None,
                    help="write the JSON report here (default: stdout)")
    ap.add_argument("--expect", default=None,
                    help="JSON expectations applied to every attempt")
    ap.add_argument("--quiet", action="store_true",
                    help="with --json-out, print only a one-line summary")
    args = ap.parse_args(argv)

    cli_expect = _read_json(args.expect) if args.expect else None
    if args.expect and cli_expect is None:
        print("fsu_fr01_fr02_gate: cannot read --expect %s" % args.expect,
              file=sys.stderr)
        return 2

    report = analyze_path(args.paths, cli_expect=cli_expect)
    if report["summary"]["attempts_total"] == 0:
        print("fsu_fr01_fr02_gate: no attempt directory found under %s"
              % ", ".join(args.paths), file=sys.stderr)
        return 2

    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        s = report["summary"]
        print("FR01/FR02 gate: %d attempt(s) PASS=%d FAIL=%d SKIP=%d "
              "certified=%d blocked=%d failed=%d -> %s"
              % (s["attempts_total"], s[STATUS_PASS], s[STATUS_FAIL],
                 s[STATUS_SKIP], s["certification"]["CERTIFIED"],
                 s["certification"]["BLOCKED"],
                 s["certification"]["FAILED"], out))
    elif not args.quiet:
        print(text)

    s = report["summary"]
    if s[STATUS_FAIL]:
        return 1
    if s[STATUS_SKIP]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
