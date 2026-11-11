#!/usr/bin/env python3
"""MMU Phase-3 formal-experiment preflight / dry-run.

Authoritative inputs (read-only):
  * gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx  (the design package ships
    this name; the task brief's "gem5-fi-MMU-Final-Experiment-Plan.xlsx" does
    not exist -- see FOR-MISMATCH-01 in the report)
  * MMU_Sample_Matrix.csv (40 rows, Seed = NEEDS_AUTHORITATIVE_EXCEL)
  * MMU_Final_Experiment_Config.json (contexts/ROIs)

What this tool does
-------------------
1. Cross-validates the 40 SampleRunIDs and every (ModelID, WorkloadID,
   ContextID) triple against the authoritative worksheets 03/05/06/07/10.
2. Checks each sample against the REAL tree:
     hook      - greps the actual C++ for mmuFaultModelIs("M0x") /
                 mmuFaultActivate("M0x"); design docs alone are never trusted.
     workload  - binary + rcS + checkpoint + disk template exist (and the
                 binary is executable).
     context   - R01-R05 is defined for the model and the sample carries a
                 non-empty dynamic context; W9/W10 explicit ASID/VA identities
                 are cross-checked against the workload definition.
     config    - ROI/VA/target-event/eligible-ordinal/mode are resolvable in
                 the real run-command template, and the model-specific CLI
                 flags exist in configs/se/arm_chaos_fs.py.
     trace     - the formal validator (mmu_formal_validate.py) knows the model.
     oracle    - the model oracle + expected terminal + workload oracle exist.
     seed      - the Seed cell is a VALID value under its SeedPolicy.  The
                 researcher-approved literal N/A_DETERMINISTIC is valid iff
                 SeedPolicy=DETERMINISTIC; it is never parsed as an int and
                 never passed to gem5.  Numeric seeds under DETERMINISTIC (or
                 the literal under a random policy) are BLOCKED_SEED_POLICY.
                 This tool never generates, hashes, timestamps or defaults a
                 seed.
      runtime   - Gate 3: a sample is READY only with real pilot/control/
                 trace evidence.  The runtime precedence is:
                   no pilot evidence / NOT_RUN         -> BLOCKED_TRACE
                   propagation PARTIAL                 -> BLOCKED_TRACE
                   terminal TRACE_INCOMPLETE           -> BLOCKED_TRACE
                   activation NO_ELIGIBLE_EVENT or
                     NOT_ACTIVATED                     -> BLOCKED_HOOK
                   propagation NOT_RUN/NOT_OBSERVED    -> BLOCKED_TRACE
                   OracleResult NOT_OBSERVED or terminal not admissible
                                                        -> BLOCKED_ORACLE
                   independent control oracle missing  -> BLOCKED_ORACLE
                   ACTIVATED + admissible terminal + complete trace +
                     independent control oracle         -> READY
                 (A NO_ELIGIBLE_EVENT activation is reported as BLOCKED_HOOK;
                  no sample currently has a knowably-wrong target event, which
                  would be BLOCKED_CONTEXT.)
     provenance- a formal sample with a sample_manifest.json whose
                 gem5/source SHA256 disagrees with the frozen formal config
                 is BLOCKED_BINARY / BLOCKED_SOURCE.  While the config still
                 says PENDING_MAIN_BUILD the comparison is reported as
                 PENDING, never as a pass.
     output    - runs/<SampleRunID>/ (and the Excel OutputDir) do not already
                 hold results.
3. Emits the PRIMARY status plus an `all_blockers` column.

Input resolution: an explicit --excel/--csv path wins; otherwise the frozen
researcher authority under phase3/freeze/authority/ is used; otherwise the
read-only design package.  If the frozen directory exists but a frozen file is
missing, resolution fails instead of silently falling back.

Status vocabulary (exactly):
    READY
    BLOCKED_MISSING_SEED
    BLOCKED_SEED_POLICY
    BLOCKED_HOOK
    BLOCKED_WORKLOAD
    BLOCKED_CONTEXT
    BLOCKED_TRACE
    BLOCKED_ORACLE
    BLOCKED_CONFIG
    BLOCKED_BINARY
    BLOCKED_SOURCE

Precedence (documented, implemented in STATUS_PRECEDENCE):
    HOOK > WORKLOAD > CONTEXT > CONFIG > TRACE > ORACLE > SEED
A seed-gate failure plus another blocker reports the other blocker as PRIMARY
and still lists the seed blocker in all_blockers.  A seed failure never
suppresses any other check.

--dry-run is the default and the only mode: this tool never launches gem5.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter, OrderedDict, defaultdict

try:
    import openpyxl
except ImportError:  # pragma: no cover - environment check
    openpyxl = None

# ---------------------------------------------------------------------------
# Authoritative inputs
# ---------------------------------------------------------------------------

DESIGN_DIR = "/home/sdc/mmu_phase1_work/design/MMU_Final_Design_Package"
REQUESTED_XLSX = os.path.join(
    DESIGN_DIR, "gem5-fi-MMU-Final-Experiment-Plan.xlsx")
# The package actually ships the "Paper" name.  Both are accepted; the tools
# record which one was used so the mismatch is never hidden.
AUTHORITATIVE_XLSX = os.path.join(
    DESIGN_DIR, "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")
AUTHORITATIVE_CSV = os.path.join(DESIGN_DIR, "MMU_Sample_Matrix.csv")
AUTHORITATIVE_CONFIG_JSON = os.path.join(
    DESIGN_DIR, "MMU_Final_Experiment_Config.json")

# Researcher-approved frozen authority (2026-11-11).  These copies are the
# default input; the design package above remains an explicit CLI override.
FROZEN_AUTHORITY_SUBDIR = os.path.join("phase3", "freeze", "authority")
FROZEN_XLSX_NAME = "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"
FROZEN_CSV_NAME = "MMU_40_Sample_Matrix.csv"
FROZEN_CONFIG_JSON_NAME = "MMU_Formal_Config.json"
FROZEN_CONFIG_YAML_NAME = "MMU_Formal_Config.yaml"

# Researcher decision: every Seed is this literal text, never a number.
SEED_LITERAL_DETERMINISTIC = "N/A_DETERMINISTIC"
SEED_POLICY_DETERMINISTIC = "DETERMINISTIC"
SEED_SOURCE_RESEARCHER_APPROVED = "RESEARCHER_APPROVED"

CONTEXT_IDS = ["R01", "R02", "R03", "R04", "R05"]

# Workload-defined context identities.  These are facts of the frozen
# workloads (same tables as tools/mmu_trace_validate_v3.py).
W9_CONTEXT_ASID = {220: "R01", 224: "R02", 228: "R03", 232: "R04", 236: "R05"}
W10_CONTEXT_VA = {
    0x4001000000: "R01", 0x4001100000: "R02", 0x4001200000: "R03",
    0x4001300000: "R04", 0x4001400000: "R05",
}

# Model -> workload fixed by worksheets 03/05/06/07.
MODEL_WORKLOAD = {
    "M01": "W9", "M02": "W10", "M03": "W11", "M04": "W12",
    "M05": "W13", "M06": "W10", "M07": "W14", "M08": "W10",
}

# Precedence is the order of this list (highest first).  READY is absence.
STATUS_PRECEDENCE = [
    # Build provenance is checked first: a formal sample whose recorded
    # binary/source hash disagrees with the frozen config is not the same
    # experiment at all.
    "BLOCKED_BINARY",
    "BLOCKED_SOURCE",
    "BLOCKED_HOOK",
    "BLOCKED_WORKLOAD",
    "BLOCKED_CONTEXT",
    "BLOCKED_CONFIG",
    "BLOCKED_MISSING_DECOY_MAPPING",
    "BLOCKED_TRACE",
    "BLOCKED_ORACLE",
    # The researcher must freeze SampleRunIDs before a formal run may start.
    "BLOCKED_SAMPLE_ID_NOT_FROZEN",
    "BLOCKED_MISSING_SEED",
    # Seed present but inconsistent with the declared policy (e.g. a numeric
    # seed under DETERMINISTIC, or N/A_DETERMINISTIC under a random policy).
    "BLOCKED_SEED_POLICY",
]
STATUS_VOCABULARY = ["READY"] + STATUS_PRECEDENCE
SEED_PLACEHOLDERS = {
    "", "NEEDS_AUTHORITATIVE_EXCEL", "N/A", "NA", "NONE", "TBD", "PENDING",
    "MISSING",
}
SEED_RE = re.compile(r"^(?:0[xX][0-9a-fA-F]+|\d+)$")

# Models the formal validator is written to understand.
VALIDATOR_MODELS = {"M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"}

MODE_CHOICES = {"Read", "Write", "Execute", "Atomic"}

# Internal workload variants.  The authoritative Excel WorkloadID stays W10;
# only the guest binary/rcS and the access mode change.  These are the two
# formal samples whose target is a store, not the W10 read contexts.
W10S_VARIANTS = {
    ("M06", "R02"): {
        "variant": "W10S-COLD-STORE",
        "workload": "W10S",
        "target_va": 0x4001100000,
        "mode": "Write",
        "roi": (0x4001100000, 0x4001700000),
        "rcs": "configs/fs/generated/mmu_w10s_run_M06_R02.rcS",
        "instruction": "STRB / cold write walk",
    },
    ("M08", "R05"): {
        "variant": "W10S-WARM-STORE",
        "workload": "W10S",
        "target_va": 0x4001400000,
        "mode": "Write",
        "roi": (0x4001400000, 0x4001700000),
        "rcs": "configs/fs/generated/mmu_w10s_run_M08_R05.rcS",
        "instruction": "STRB / warm DTLB hit",
    },
}

# Authoritative control runs used as independent no-fault oracles.  A run may
# hold all five contexts (one --all script) or only R01; the lookup function
# verifies the context line really exists before accepting it.
CONTROL_ORACLE_RUNS = {
    ("M01", "W9"): "runs/w9_trace_on_final",
    ("M02", "W10"): "runs/TEST-ENV-CTRL-W10",
    ("M03", "W11"): "runs/TEST-P3-W11-CTRL",
    ("M04", "W12"): "runs/TEST-P3-W12-CTRL",
    ("M05", "W13"): "runs/TEST-P3-W13-CTRL",
    ("M06", "W10"): "runs/TEST-M06-P3-CTRL-R01",
    ("M07", "W14"): "runs/TEST-M07-P3B-CTRL-R01",
    ("M08", "W10"): "runs/TEST-M08-P3-CTRL-R01",
}

# The W12 per-context scoped controls on the FINAL binary are the source of
# the decoy PFN.  A single `--all` control has a different guest allocation
# history; the fail-closed M04 check proved the old PFNs do not transfer to
# scoped runs.  The map is data-driven (JSON or directory), never hardcoded.
W12_CONTROL_DEFAULT = "phase3/formal/w12_decoy_map.json"

# Per-context controls take precedence over the model/workload default.
CONTROL_ORACLE_CONTEXT_RUNS = {
    ("M04", "R01"): "runs/TEST-CTRL-W12-R01",
    ("M04", "R02"): "runs/TEST-CTRL-W12-R02",
    ("M04", "R03"): "runs/TEST-CTRL-W12-R03",
    ("M04", "R04"): "runs/TEST-CTRL-W12-R04",
    ("M04", "R05"): "runs/TEST-CTRL-W12-R05",
    ("M05", "R01"): "runs/TEST-CTRL-W13-CLOSURE",
    ("M05", "R02"): "runs/TEST-CTRL-W13-CLOSURE",
    ("M05", "R03"): "runs/TEST-CTRL-W13-CLOSURE",
    ("M05", "R04"): "runs/TEST-CTRL-W13-CLOSURE",
    ("M05", "R05"): "runs/TEST-CTRL-W13-CLOSURE",
    ("M06", "R02"): "runs/TEST-CTRL-W10S-COLD",
    ("M08", "R05"): "runs/TEST-CTRL-W10S-WARM",
}

EVIDENCE_INDEX_DEFAULT = "phase3/formal/evidence_index.json"

# Expected per-model target parameters (verified from the built workloads and
# the Phase-3 model semantics).  These are the values the formal runner must
# pass; the legacy generic run-script default (n=12 for every model) is not
# sufficient for M05 (2 MiB walk-cache pages, n=21).
MODEL_TARGET_PARAMS = {
    "M01": {"target_n": 12},
    "M02": {"target_n": 12},
    "M03": {"target_n": 12,
            "target_va": "data 0x4004000000 (R01-R04), code 0x4005000000 (R05)"},
    "M04": {"target_n": 12,
            "target_instance": "dtb (R01-R04), itb (R05)",
            "decoy_pfn": "W12 control run (auto until pinned)"},
    "M05": {"target_n": 21, "target_walk_level": 2,
            "target_instance": "l2_shared",
            "fault_persistence": "entry_lifetime"},
    "M06": {"target_n": 12, "target_walk_level": 3},
    "M07": {"target_n": 12},
    "M08": {"target_n": 12,
            "target_mode": "Read (R01-R04), Write (R05)"},
}


def model_params_detail(model, context):
    params = dict(MODEL_TARGET_PARAMS.get(model, {}))
    if model == "M04":
        params["target_instance"] = "itb" if context == "R05" else "dtb"
    if model == "M08":
        params["target_mode"] = "Write" if context == "R05" else "Read"
    return params

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _norm_key(key):
    if key is None:
        return ""
    return str(key).replace("﻿", "").strip()


def _s(value):
    return "" if value is None else str(value).strip()


def _parse_int(value):
    """Parse a decimal/0x integer, returning None for symbolic values."""
    text = _s(value)
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def _row_dicts(rows):
    if not rows:
        return []
    header = [_norm_key(c) for c in rows[0]]
    out = []
    for raw in rows[1:]:
        rec = OrderedDict()
        for idx, key in enumerate(header):
            rec[key] = raw[idx] if idx < len(raw) else None
        out.append(rec)
    return out


def _rel(repo_root, path):
    try:
        return os.path.relpath(path, repo_root)
    except ValueError:
        return path


def _read_text(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read()
    except (OSError, ValueError):
        return ""


def context_allowed(text, cid):
    """Accept both an explicit list and the worksheet's range form R01-R05."""
    for token in re.split(r"[,;\s]+", _s(text)):
        if not token:
            continue
        m = re.match(r"^(R\d+)-(R\d+)$", token)
        if m:
            lo = int(m.group(1)[1:])
            hi = int(m.group(2)[1:])
            if lo <= int(cid[1:]) <= hi:
                return True
        elif token == cid:
            return True
    return False


# ---------------------------------------------------------------------------
# Authoritative Excel / CSV loading
# ---------------------------------------------------------------------------


class AuthoritativeError(RuntimeError):
    pass


def frozen_authority_paths(repo_root=None):
    """Absolute paths of the researcher-frozen authority copies."""
    root = os.path.abspath(repo_root or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    base = os.path.join(root, FROZEN_AUTHORITY_SUBDIR)
    return {
        "dir": base,
        "xlsx": os.path.join(base, FROZEN_XLSX_NAME),
        "csv": os.path.join(base, FROZEN_CSV_NAME),
        "config_json": os.path.join(base, FROZEN_CONFIG_JSON_NAME),
        "config_yaml": os.path.join(base, FROZEN_CONFIG_YAML_NAME),
    }


def authority_label(path, repo_root=None):
    """Classify an input path without guessing: FROZEN_AUTHORITY vs design."""
    if not path:
        return "<none>"
    frozen = frozen_authority_paths(repo_root)
    full = os.path.abspath(path)
    if full == os.path.abspath(frozen["xlsx"]) or \
            full == os.path.abspath(frozen["csv"]) or \
            full == os.path.abspath(frozen["config_json"]) or \
            full == os.path.abspath(frozen["config_yaml"]):
        return "FROZEN_AUTHORITY"
    if full == os.path.abspath(AUTHORITATIVE_XLSX) or \
            full == os.path.abspath(REQUESTED_XLSX) or \
            full == os.path.abspath(AUTHORITATIVE_CSV):
        return "DESIGN_PACKAGE_ORIGINAL"
    return "EXPLICIT_OVERRIDE"


def resolve_excel(path=None, repo_root=None):
    """Resolve the authoritative workbook.

    Precedence: explicit CLI path > frozen authority copy > design package.
    If the frozen authority directory exists but its workbook is missing,
    this raises instead of silently falling back to the original package.
    """
    if path:
        if os.path.isfile(path):
            return path
        raise AuthoritativeError("explicit --excel not found: %s" % path)
    frozen = frozen_authority_paths(repo_root)
    if os.path.isdir(frozen["dir"]):
        if os.path.isfile(frozen["xlsx"]):
            return frozen["xlsx"]
        raise AuthoritativeError(
            "frozen authority directory exists but %s is missing; refusing "
            "a silent fallback to the design package" % frozen["xlsx"])
    for candidate in (REQUESTED_XLSX, AUTHORITATIVE_XLSX):
        if os.path.isfile(candidate):
            return candidate
    raise AuthoritativeError(
        "authoritative Excel not found (frozen %s; requested %s; shipped %s)"
        % (frozen["xlsx"], REQUESTED_XLSX, AUTHORITATIVE_XLSX))


def resolve_csv(path=None, repo_root=None):
    """Resolve MMU_Sample_Matrix.csv with the same precedence as the Excel."""
    if path:
        if os.path.isfile(path):
            return path
        raise AuthoritativeError("explicit --csv not found: %s" % path)
    frozen = frozen_authority_paths(repo_root)
    if os.path.isdir(frozen["dir"]):
        if os.path.isfile(frozen["csv"]):
            return frozen["csv"]
        raise AuthoritativeError(
            "frozen authority directory exists but %s is missing; refusing "
            "a silent fallback to the design package" % frozen["csv"])
    if os.path.isfile(AUTHORITATIVE_CSV):
        return AUTHORITATIVE_CSV
    return None


def load_pages(excel_path):
    if openpyxl is None:
        raise AuthoritativeError("openpyxl is required to read the Excel")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    pages = {}
    for name in wb.sheetnames:
        ws = wb[name]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        pages[name] = _row_dicts(rows)
    return pages


def load_samples(excel_path, csv_path=None):
    """Return (samples, issues).  Excel sheet 07 is authoritative; the CSV is
    cross-checked row-by-row and a mismatch is an issue, never silently
    ignored."""
    pages = load_pages(excel_path)
    sheet = pages.get("07_Sample_Matrix")
    if not sheet:
        raise AuthoritativeError("worksheet 07_Sample_Matrix missing/empty")
    samples = []
    for rec in sheet:
        sample = {k: _s(v) for k, v in rec.items()}
        if not sample.get("SampleRunID"):
            continue
        samples.append(sample)

    issues = []
    if len(samples) != 40:
        issues.append("EXCEL_SAMPLE_COUNT=%d (expected 40)" % len(samples))

    ids = [s["SampleRunID"] for s in samples]
    dup = [k for k, n in Counter(ids).items() if n > 1]
    if dup:
        issues.append("duplicate SampleRunID: %s" % ",".join(sorted(dup)))

    triples = [(s.get("ModelID"), s.get("WorkloadID"), s.get("ContextID"))
               for s in samples]
    if len(set(triples)) != len(triples):
        issues.append("duplicate ModelID/WorkloadID/ContextID triples")

    # CSV cross-check (the CSV is a derived mirror; every ID/triple must agree).
    if csv_path and os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as fh:
            csv_rows = list(csv.DictReader(fh))
        csv_rows = [{(k or "").replace("﻿", ""): _s(v)
                     for k, v in r.items()} for r in csv_rows]
        if len(csv_rows) != len(samples):
            issues.append("CSV_SAMPLE_COUNT=%d (Excel=%d)" %
                          (len(csv_rows), len(samples)))
        by_id = {r["SampleRunID"]: r for r in csv_rows}
        for s in samples:
            r = by_id.get(s["SampleRunID"])
            if r is None:
                issues.append("CSV missing %s" % s["SampleRunID"])
                continue
            for field in ("ModelID", "WorkloadID", "ContextID"):
                if r.get(field, "") != s.get(field, ""):
                    issues.append(
                        "CSV/Excel %s mismatch on %s: %s vs %s" %
                        (s["SampleRunID"], field, r.get(field, ""),
                         s.get(field, "")))
            if _s(r.get("Seed", "")) != _s(s.get("Seed", "")):
                issues.append(
                    "CSV/Excel Seed mismatch on %s: %r vs %r (Excel is "
                    "authoritative)" % (s["SampleRunID"], r.get("Seed", ""),
                                        s.get("Seed", "")))
            for field in ("SeedPolicy", "SeedSource", "SampleFreezeStatus"):
                if field in r and field in s and \
                        _s(r.get(field)) != _s(s.get(field)):
                    issues.append(
                        "CSV/Excel %s mismatch on %s: %r vs %r" %
                        (field, s["SampleRunID"], r.get(field),
                         s.get(field)))

    # Worksheet 03/05/06/07 triple validation.
    model_info = {}
    for rec in pages.get("03_Fault_Model_Summary", []):
        mid = _s(rec.get("ModelID"))
        if mid:
            model_info[mid] = {k: _s(v) for k, v in rec.items()}
    model_workload_06 = defaultdict(set)
    workload_info = {}
    for rec in pages.get("06_Workload_Matrix", []):
        wid = _s(rec.get("WorkloadID"))
        if not wid:
            continue
        workload_info[wid] = {k: _s(v) for k, v in rec.items()}
        for mid in _s(rec.get("Models")).replace(",", ";").split(";"):
            mid = mid.strip()
            if mid:
                model_workload_06[mid].add(wid)
    injection_cfg = {}
    for rec in pages.get("05_Injection_Configuration", []):
        mid = _s(rec.get("ModelID"))
        if mid:
            injection_cfg[mid] = {k: _s(v) for k, v in rec.items()}
    oracle_info = {}
    for rec in pages.get("10_Terminal_Oracle", []):
        key = _s(rec.get("TerminalStateOrModelOracle"))
        if key:
            oracle_info[key] = {k: _s(v) for k, v in rec.items()}

    for s in samples:
        mid, wid, cid = (s.get("ModelID"), s.get("WorkloadID"),
                         s.get("ContextID"))
        if mid not in MODEL_WORKLOAD:
            issues.append("%s: unknown ModelID %s" % (s["SampleRunID"], mid))
        else:
            expected_wl = MODEL_WORKLOAD[mid]
            if wid != expected_wl:
                issues.append(
                    "%s: WorkloadID %s != authoritative %s" %
                    (s["SampleRunID"], wid, expected_wl))
            ws03_wl = model_info.get(mid, {}).get("WorkloadID", "")
            if ws03_wl and ws03_wl != wid:
                issues.append(
                    "%s: worksheet 03 WorkloadID %s != sample %s" %
                    (s["SampleRunID"], ws03_wl, wid))
            ws05_wl = injection_cfg.get(mid, {}).get("WorkloadID", "")
            if ws05_wl and ws05_wl != wid:
                issues.append(
                    "%s: worksheet 05 WorkloadID %s != sample %s" %
                    (s["SampleRunID"], ws05_wl, wid))
            if model_workload_06.get(mid) and \
                    wid not in model_workload_06[mid]:
                issues.append(
                    "%s: worksheet 06 does not list %s under model %s" %
                    (s["SampleRunID"], wid, mid))
        if cid not in CONTEXT_IDS:
            issues.append("%s: ContextID %s not in R01-R05" %
                          (s["SampleRunID"], cid))
        ws03_ctx = model_info.get(mid, {}).get("Contexts", "")
        if ws03_ctx and not context_allowed(ws03_ctx, cid):
            issues.append(
                "%s: worksheet 03 contexts '%s' do not include %s" %
                (s["SampleRunID"], ws03_ctx, cid))
        if not s.get("DynamicContext"):
            issues.append("%s: empty DynamicContext" % s["SampleRunID"])
        if not s.get("TargetEvent"):
            issues.append("%s: empty TargetEvent" % s["SampleRunID"])
        if not s.get("EventOrdinal"):
            issues.append("%s: empty EventOrdinal" % s["SampleRunID"])
        if not s.get("ExpectedTerminalStates"):
            issues.append("%s: empty ExpectedTerminalStates" %
                          s["SampleRunID"])

    ctx = {
        "pages": pages,
        "model_info": model_info,
        "injection_cfg": injection_cfg,
        "workload_info": workload_info,
        "oracle_info": oracle_info,
        "issues": issues,
    }
    return samples, ctx


# ---------------------------------------------------------------------------
# Source hook scan (engineering truth, not design docs)
# ---------------------------------------------------------------------------


def scan_hooks(repo_root, model_ids):
    """Grep the actual C++ for real hook sites.

    A model counts as hooked when a call site names it explicitly:
        mmuFaultModelIs("<Mxx>")  or  mmuFaultActivate("<Mxx>"
    A generic summary branch (`mmu_fault_model == "Mxx"`) is NOT a hook; it
    only prints a summary.  Accessor names (mmuM06...) are recorded as
    supporting evidence but do not by themselves prove a hook site.
    """
    src_root = os.path.join(repo_root, "CHAOS", "gem5", "src")
    files = []
    for dirpath, _dirnames, filenames in os.walk(src_root):
        for name in filenames:
            if name.endswith((".cc", ".hh", ".py")):
                files.append(os.path.join(dirpath, name))
    blobs = {path: _read_text(path) for path in files}

    result = {}
    for mid in model_ids:
        site_re = re.compile(
            r"(mmuFaultModelIs|mmuFaultActivate)\s*\(\s*\"%s\"" %
            re.escape(mid))
        accessor_re = re.compile(r"\bmmu%s[A-Za-z0-9_]*" % re.escape(mid))
        sites = []
        supporting = []
        for path, text in blobs.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                if site_re.search(line):
                    sites.append({
                        "file": _rel(repo_root, path), "line": lineno,
                        "text": line.strip()[:200],
                    })
                elif accessor_re.search(line):
                    supporting.append({
                        "file": _rel(repo_root, path), "line": lineno,
                        "text": line.strip()[:200],
                    })
        result[mid] = {
            "hook_present": bool(sites),
            "sites": sites,
            "supporting": supporting[:20],
        }
    return result


# ---------------------------------------------------------------------------
# Workload / config discovery (live tree, including W11-W14 while they land)
# ---------------------------------------------------------------------------


def _parse_run_script(repo_root):
    """Parse workload defaults out of the real phase3/phase2.2 run scripts.

    Returns {workload: {ckpt, rcs, va_lo, va_hi, script}}.
    """
    candidates = [
        os.path.join(repo_root, "phase3", "run_scripts", "run_mmu_case.sh"),
        os.path.join(repo_root, "phase2_2", "run_scripts", "run_p22_case.sh"),
    ]
    out = {}
    for script in candidates:
        text = _read_text(script)
        if not text:
            continue
        # case blocks:  W11|W12|W13|W14) ... ;;
        for m in re.finditer(r"^\s*([A-Z0-9|]+)\)\s*\n(.*?);;",
                             text, re.M | re.S):
            keys = [k.strip() for k in m.group(1).split("|")]
            body = m.group(2)
            ckpt = re.search(r"CKPT=\"?\$WS/([^\"\s]+)\"?", body)
            rcs = re.search(r"RCS=\"?\$WS/([^\"\s]+)\"?", body)
            va_lo = re.search(r"VA_LO=(0x[0-9a-fA-F]+)", body)
            va_hi = re.search(r"VA_HI=(0x[0-9a-fA-F]+)", body)
            for key in keys:
                if not re.match(r"^W\d+[A-Z]?$", key):
                    continue
                rcs_path = rcs.group(1) if rcs else ""
                if rcs_path:
                    rcs_path = rcs_path.replace("${WL,,}", key.lower())
                out.setdefault(key, {}).update({
                    "ckpt": ckpt.group(1) if ckpt else "",
                    "rcs": rcs_path,
                    "va_lo": int(va_lo.group(1), 0) if va_lo else None,
                    "va_hi": int(va_hi.group(1), 0) if va_hi else None,
                    "script": _rel(repo_root, script),
                })
    return out


def _read_workload_vas(repo_root, workload):
    """Extract target VA definitions from the live workload source.

    W11: data target + R05 code target; W12/W13: one target VA.  Returns a
    dict of {macro_name: int}.  Unknown workloads return {}.
    """
    candidates = []
    for wid_dir in ("workloads/mmu/%s", "workloads/mmu_rev/%s",
                    "phase3/workloads/%s"):
        d = os.path.join(repo_root, wid_dir % workload)
        if os.path.isdir(d):
            for name in os.listdir(d):
                if name.endswith(".c"):
                    candidates.append(os.path.join(d, name))
    vas = {}
    for path in candidates:
        text = _read_text(path)
        for m in re.finditer(
                r"#define\s+%s_[A-Z0-9_]*(VA|PAGE|BASE)[A-Z0-9_]*\s+"
                r"(0x[0-9a-fA-F]+|\d+)UL?" % re.escape(workload), text):
            vas[m.group(0).split()[1]] = int(m.group(2), 0)
    return vas


def discover_workload(repo_root, workload, run_script_defaults):
    """Resolve binary/rcS/checkpoint/disk/ROI for one workload."""
    lw = workload.lower()
    # The live `workloads/mmu/<W>/mmu_<w>` build is authoritative.  The
    # historical `workloads/mmu_rev/` copies are FALLBACKS only: hashing a
    # stale copy while the rcS executes the live/embedded binary would record
    # a false workload provenance (observed for W9/W10: mmu_rev hashes
    # ec5256…/4a3367… vs the live 4f3ddb…/20d9f2…).
    # W9 is special: the authoritative ASID table (220/224/228/232/236) and
    # every historical M01 run come from the canonical mmu_rev W9 build.  The
    # live workloads/mmu/W9 rebuild assigns ASIDs 234/238/242/246/250, so
    # preferring it makes an M01 target ASID unreachable.  Keep mmu_rev W9
    # first; every other workload uses the live build first.
    if workload == "W9":
        ordered = (
            "workloads/mmu_rev/%s/Binary/mmu_%s" % (workload, lw),
            "workloads/mmu_rev/%s/mmu_%s" % (workload, lw),
            "workloads/mmu/%s/Binary/mmu_%s" % (workload, lw),
            "workloads/mmu/%s/mmu_%s" % (workload, lw),
            "workloads/mmu_rev/%s/install/%s/mmu_%s" %
            (workload, workload, lw),
            "phase3/workloads/%s/mmu_%s" % (workload, lw),
            "phase3/workloads/mmu_%s" % lw,
        )
    else:
        ordered = (
            "workloads/mmu/%s/Binary/mmu_%s" % (workload, lw),
            "workloads/mmu/%s/mmu_%s" % (workload, lw),
            "workloads/mmu_rev/%s/Binary/mmu_%s" % (workload, lw),
            "workloads/mmu_rev/%s/mmu_%s" % (workload, lw),
            "workloads/mmu_rev/%s/install/%s/mmu_%s" %
            (workload, workload, lw),
            "phase3/workloads/%s/mmu_%s" % (workload, lw),
            "phase3/workloads/mmu_%s" % lw,
        )
    binary_candidates = [os.path.join(repo_root, p) for p in ordered]
    binary = next((p for p in binary_candidates if os.path.isfile(p)), None)

    defaults = run_script_defaults.get(workload, {})
    rcs_candidates = []
    if defaults.get("rcs"):
        rcs_candidates.append(os.path.join(repo_root, defaults["rcs"]))
    rcs_candidates += [
        os.path.join(repo_root, "configs", "fs",
                     "mmu_%s_run.rcS" % workload.lower()),
        os.path.join(repo_root, "configs", "fs",
                     "mmu_%s.rcS" % workload.lower()),
    ]
    rcs = next((p for p in rcs_candidates if os.path.isfile(p)), None)

    ckpt = None
    if defaults.get("ckpt"):
        candidate = os.path.join(repo_root, defaults["ckpt"])
        if os.path.isdir(candidate):
            ckpt = candidate
    disk = os.path.join(repo_root, "runs", "disks", "mmu_template.img")
    if not os.path.isfile(disk):
        disk = None

    va_lo = defaults.get("va_lo")
    va_hi = defaults.get("va_hi")
    vas = _read_workload_vas(repo_root, workload)
    golden_prefix = "%s_RESULT" % workload
    rcs_text = _read_text(rcs) if rcs else ""
    # Can a single formal context be selected?  W9 uses a shell loop
    # (--ctx $c), W10 uses --ctx all, W11-W14 use --all, W10S is a
    # context-specialised cold-write variant.
    context_scopable = bool(
        workload in ("W9", "W10S") or
        "--ctx all" in rcs_text or "--all" in rcs_text or
        "--ctx $c" in rcs_text or
        ("--ctx" in rcs_text and "R01" in rcs_text))
    context_scope_method = (
        "W9 shell loop -> per-context rcS" if workload == "W9" else
        "context-specialised workload" if workload == "W10S" else
        "--ctx all -> --ctx CID" if "--ctx all" in rcs_text else
        "--all -> --ctx CID" if "--all" in rcs_text else
        "unknown")

    return {
        "workload": workload,
        "binary": binary,
        "binary_executable": bool(binary and os.access(binary, os.X_OK)),
        "rcs": rcs,
        "ckpt": ckpt,
        "disk": disk,
        "roi_lo": va_lo,
        "roi_hi": va_hi,
        "workload_vas": vas,
        "golden_prefix": golden_prefix,
        "rcs_text": rcs_text,
        "context_scopable": context_scopable,
        "context_scope_method": context_scope_method,
        "run_script": defaults.get("script", ""),
        # A workload is "ready" only when the command can actually start.
        "ready": bool(binary and os.access(binary, os.X_OK) and rcs and
                      ckpt and disk and va_lo is not None and
                      va_hi is not None),
        "missing": [
            name for name, val in (
                ("binary", binary and os.access(binary, os.X_OK)),
                ("rcS", rcs), ("checkpoint", ckpt), ("disk", disk),
                ("ROI", va_lo is not None and va_hi is not None),
            ) if not val
        ],
    }


def resolve_target_va(sample, wl):
    """Resolve the sample's target VA from authoritative data + workload fact."""
    raw = _s(sample.get("TargetVA"))
    numeric = _parse_int(raw)
    if numeric is not None:
        return numeric, "excel"
    wid = sample.get("WorkloadID")
    cid = sample.get("ContextID")
    vas = wl.get("workload_vas", {})
    if wid == "W9":
        return 0x4000000000, "W9 workload fixed remapped VA"
    if wid == "W10":
        return W10_CONTEXT_VA.get(cid), "W10 context VA"
    # W11: R05 uses the code VA; other contexts use the data VA.
    if wid == "W11":
        if cid == "R05" and "W11_CODE_VA" in vas:
            return vas["W11_CODE_VA"], "W11_CODE_VA"
        if "W11_DATA_VA" in vas:
            return vas["W11_DATA_VA"], "W11_DATA_VA"
    if wid == "W14":
        # Exact mapping from workloads/mmu/W14/mmu_w14.c (ctx -> mapping).
        macro = {
            "R01": "W14_RO_VA", "R02": "W14_RO_VA",
            "R03": "W14_NONE_VA", "R04": "W14_XN_VA",
            "R05": "W14_NONE_CODE_VA",
        }.get(cid)
        if macro and macro in vas:
            return vas[macro], macro
    for macro, value in vas.items():
        if "TARGET_VA" in macro or "TARGET_BASE" in macro:
            return value, macro
    return None, "unresolved (symbolic %r)" % raw


# ---------------------------------------------------------------------------
# Per-check evaluation
# ---------------------------------------------------------------------------


def check_seed(sample):
    """Classify the authoritative Seed cell against its declared policy.

    The researcher-approved deterministic marker `N/A_DETERMINISTIC` is a
    VALID seed value when (and only when) SeedPolicy=DETERMINISTIC.  It is a
    literal marker: it is never parsed as an integer and never passed to gem5.
    A numeric seed under DETERMINISTIC, or the literal marker under a
    random/unspecified policy, is an inconsistency (BLOCKED_SEED_POLICY).
    """
    raw = _s(sample.get("Seed"))
    policy_raw = _s(sample.get("SeedPolicy"))
    policy = policy_raw.upper()
    source_raw = _s(sample.get("SeedSource"))
    source = source_raw or "<unset>"
    base = {
        "seed_raw": raw if raw else "<empty>",
        "seed_policy": policy_raw or "<unset>",
        "seed_source": source,
        "seed_source_raw": source_raw,
        "seed_literal_deterministic":
            raw == SEED_LITERAL_DETERMINISTIC,
        "seed_used_by_gem5": False,
    }
    if raw == SEED_LITERAL_DETERMINISTIC:
        if policy == SEED_POLICY_DETERMINISTIC:
            base.update({
                "seed_present": True,
                "seed_valid": True,
                "status": "VALID_DETERMINISTIC",
                "detail": ("valid deterministic marker %r "
                           "(SeedPolicy=%s, SeedSource=%s; not passed to "
                           "gem5)" % (raw, policy_raw, source)),
            })
            return base
        base.update({
            "seed_present": True,
            "seed_valid": False,
            "status": "POLICY_INCONSISTENT",
            "detail": ("%r requires SeedPolicy=%s, found %r" %
                       (raw, SEED_POLICY_DETERMINISTIC,
                        policy_raw or "<unset>")),
        })
        return base
    if bool(SEED_RE.match(raw)):
        base.update({
            "seed_present": True,
            "seed_valid": False,
            "status": "POLICY_INCONSISTENT",
            "detail": ("numeric seed %r is inconsistent with the deterministic "
                       "policy (and this runner never passes a numeric seed to "
                       "gem5)" % raw),
        })
        return base
    base.update({
        "seed_present": False,
        "seed_valid": False,
        "status": "MISSING",
        "detail": "missing/placeholder in authoritative workbook (%s)" %
                  (raw or "<empty>"),
    })
    return base


def sample_id_frozen(sample):
    """True only for a researcher-frozen SampleRunID status.

    The frozen authority marks every row FROZEN.  Unfrozen/proposed values are
    still refused for formal runs; this function never mutates or defaults
    the value.
    """
    raw = _s(sample.get("SampleIDStatus"))
    up = raw.upper()
    frozen = ("FROZEN" in up and "NOT_FROZEN" not in up and
              up not in ("", "PROPOSED", "PROPOSED_NOT_FROZEN"))
    return frozen, raw or "<empty>"


def check_sample_id(sample):
    frozen, raw = sample_id_frozen(sample)
    return {
        "frozen": frozen,
        "status_raw": raw,
        "detail": ("frozen (%s)" % raw if frozen else
                   "SampleIDStatus=%s; researcher must freeze SampleRunID" %
                   raw),
    }


PENDING_BUILD = "PENDING_MAIN_BUILD"


def terminal_admissible(sample, terminal_state):
    """Observed terminal must be one of the sample's expected terminals."""
    raw = _s(terminal_state)
    if not raw:
        return False, "terminal state is empty"
    expected = []
    for part in re.split(r"[,;]", _s(sample.get("ExpectedTerminalStates"))):
        part = re.sub(r"\s*\(.*?\)", "", part.strip().upper()).strip()
        part = part.rstrip(".")
        if part:
            expected.append(part)
    up = raw.upper().rstrip(".")
    if up in expected:
        return True, "%s is an expected terminal" % up
    return False, ("terminal %r is not in the sample's expected terminal set "
                   "%s" % (up, expected))


def runtime_evidence_check(sample, ev, control):
    """Gate 3: runtime evidence decides READY, not file existence.

    Returns (status_or_None, detail).  Status is one of the existing
    BLOCKED_TRACE / BLOCKED_HOOK / BLOCKED_ORACLE vocabulary and follows the
    precedence documented in the module docstring.
    """
    ev = ev or {}
    pilot = _s(ev.get("runtime_pilot") or "NOT_RUN").upper()
    activation = _s(ev.get("fault_activation") or "NOT_RUN").upper()
    propagation = _s(ev.get("propagation") or "NOT_RUN").upper()
    trace = _s(ev.get("trace_completeness") or "NOT_RUN").upper()
    terminal = _s(ev.get("terminal_state"))
    oracle = _s(ev.get("oracle_result") or "NOT_OBSERVED").upper()

    if pilot != "PASS":
        return ("BLOCKED_TRACE",
                "no pilot runtime evidence (RuntimePilotEvidenceStatus=%s)"
                % pilot)
    if terminal.upper() == "TRACE_INCOMPLETE":
        return ("BLOCKED_TRACE",
                "terminal TRACE_INCOMPLETE: the trace stream is incomplete")
    # Trace completeness is the gate; PropagationStatus is the model's
    # architectural reach (PARTIAL is the CORRECT value for a legitimate
    # SQUASHED / DETECTED_CONTAINED / masked terminal and must not block).
    if trace in ("", "NOT_RUN", "NOT_OBSERVED", "PARTIAL", "INCOMPLETE"):
        return ("BLOCKED_TRACE",
                "TraceCompleteness=%s (real causal chain required)" %
                (trace or "<empty>"))
    if activation in ("NO_ELIGIBLE_EVENT", "NOT_ACTIVATED", "NOT_RUN"):
        # No current sample has a knowably-wrong target event; such a case
        # would be BLOCKED_CONTEXT instead (recorded in the detail).
        return ("BLOCKED_HOOK",
                "fault activation=%s: the target event was never reached "
                "(no knowably-wrong target, so not BLOCKED_CONTEXT)"
                % activation)
    if propagation in ("", "NOT_RUN", "NOT_OBSERVED"):
        return ("BLOCKED_TRACE",
                "propagation evidence=%s (trace missing)" %
                (propagation or "<empty>"))
    if oracle in ("", "NOT_OBSERVED"):
        return ("BLOCKED_ORACLE", "OracleResult=%s" % (oracle or "<empty>"))
    admissible, why = terminal_admissible(sample, terminal)
    if not admissible:
        return ("BLOCKED_ORACLE", why)
    if not (control or {}).get("present"):
        return ("BLOCKED_ORACLE",
                "independent control oracle missing: %s" %
                (control or {}).get("detail", "not resolved"))
    return (None,
            "ACTIVATED + admissible terminal + complete trace + independent "
            "control oracle")


def load_formal_config(repo_root):
    """Load the frozen formal config used for build-provenance comparison."""
    frozen = frozen_authority_paths(repo_root)
    path = frozen["config_json"]
    if not os.path.isfile(path):
        return {"path": None, "data": {}, "detail": "frozen formal config "
                "missing: %s" % path}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return {"path": path, "data": {}, "detail": "unreadable: %s" % exc}
    return {"path": path, "data": data, "detail": "loaded"}


def check_build_provenance(sample, repo_root, formal_config,
                           pilot_run_id=None):
    """Compare a run manifest's binary/source hashes with the frozen config.

    The gate is active whenever the frozen config carries a real hash.  While
    it says PENDING_MAIN_BUILD the result is recorded as PENDING, never PASS.
    """
    cfg = (formal_config or {}).get("data") or {}
    exp_bin = _s(cfg.get("gem5_sha256"))
    exp_src = cfg.get("source_sha256") or {}
    if not isinstance(exp_src, dict):
        exp_src = {}
    exp_bin_real = bool(exp_bin) and exp_bin != PENDING_BUILD
    exp_src_real = {k: _s(v) for k, v in exp_src.items()
                    if _s(v) and _s(v) != PENDING_BUILD}
    # The formal SampleRunID has not been launched before READY; the
    # provenance evidence is the REAL pilot run recorded in the evidence
    # index.  Looking only under the formal ID made every row NO_MANIFEST.
    run_id = _s(pilot_run_id) or _s(sample.get("SampleRunID"))
    manifest_path = os.path.join(
        repo_root, "runs", run_id, "sample_manifest.json")
    present = os.path.isfile(manifest_path)
    manifest = {}
    parse_detail = ""
    if present:
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, ValueError) as exc:
            present = False
            parse_detail = "manifest unreadable: %s" % exc
    got_bin = _s(manifest.get("gem5_sha256"))
    got_src = manifest.get("source_sha256") or {}
    if not isinstance(got_src, dict):
        got_src = {}

    result = {
        "manifest": manifest_path,
        "manifest_present": present,
        "expected_gem5_sha256": exp_bin or "<unset>",
        "manifest_gem5_sha256": got_bin or "<unset>",
        "binary_status": "PENDING",
        "source_status": "PENDING",
        "blocker": None,
        "detail": parse_detail,
    }
    if not exp_bin and not exp_src:
        result["detail"] = ("frozen formal config has no gem5_sha256/"
                            "source_sha256 fields; provenance gate PENDING")
        return result
    if not exp_bin_real and not exp_src_real:
        result["detail"] = ("frozen config hashes are %s; comparison not yet "
                            "possible" % PENDING_BUILD)
        return result
    if not present:
        result["binary_status"] = "NO_MANIFEST"
        result["source_status"] = "NO_MANIFEST"
        # Without a pilot manifest there is no binary/source provenance at
        # all; this must block the row rather than be silently ignored.
        result["blocker"] = "BLOCKED_BINARY"
        result["detail"] = ("no pilot sample_manifest.json under runs/%s; "
                            "binary/source hashes not recorded (%s)" %
                            (run_id, parse_detail or "file absent"))
        return result

    problems = []
    if exp_bin_real:
        if got_bin == exp_bin:
            result["binary_status"] = "PASS"
        else:
            result["binary_status"] = "MISMATCH"
            problems.append("BLOCKED_BINARY")
            result["detail"] = ("manifest gem5_sha256=%s != frozen %s" %
                                (got_bin or "<missing>", exp_bin))
    else:
        result["binary_status"] = "PENDING"

    if exp_src_real:
        mismatched = [path for path, want in exp_src_real.items()
                      if _s(got_src.get(path)) != want]
        if mismatched:
            result["source_status"] = "MISMATCH"
            problems.append("BLOCKED_SOURCE")
            result["detail"] = ("source hash mismatch for %s" %
                                ",".join(sorted(mismatched)))
        else:
            result["source_status"] = "PASS"
    else:
        result["source_status"] = "PENDING"

    if not problems:
        result["detail"] = "manifest binary/source hashes match frozen config"
    result["blocker"] = problems[0] if problems else None
    return result


def w10s_variant(model, context):
    return W10S_VARIANTS.get((model, context))


def check_access_mode(sample, repo_root=None):
    """The sample's AccessMode must match the real guest instruction.

    This is what stops a sample marked Write from silently running an LDR.
    For the W10/W10S arm the check reads the actual source: W10S must contain
    the real store (`target[0] = STORE_MARKER`), W10 must not.
    """
    model = sample.get("ModelID", "")
    ctx = sample.get("ContextID", "")
    mode = _s(sample.get("AccessMode"))
    var = w10s_variant(model, ctx)
    if var:
        ok = mode == var["mode"]
        src_note = ""
        if repo_root:
            src = os.path.join(repo_root, "workloads", "mmu", "W10S",
                               "mmu_w10s.c")
            text = _read_text(src)
            has_store = "target[0] = STORE_MARKER" in text
            src_note = ("source store=%s" % has_store)
            if not has_store:
                ok = False
        return ok, ("%s (%s); %s" % (var["instruction"], mode, src_note)
                    if ok else
                    "sample AccessMode=%r but variant %s runs %s; %s" %
                    (mode, var["variant"], var["instruction"], src_note))
    if mode and mode not in MODE_CHOICES:
        return False, "unknown AccessMode %r" % mode
    # A plain W10 sample is a read context; its source must not contain the
    # W10S store marker.
    if repo_root and mode in ("Read", "Atomic", "Execute"):
        w10 = _read_text(os.path.join(repo_root, "workloads", "mmu", "W10",
                                      "mmu_w10.c"))
        if "STORE_MARKER" in w10:
            return False, "plain W10 unexpectedly carries a store marker"
    return True, "AccessMode=%s" % (mode or "<unspecified>")


def _parse_w12_line(line):
    if "W12_RESULT" not in line:
        return None
    kv = {}
    for tok in line.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
    ctx = kv.get("ctx")
    if not ctx:
        return None
    try:
        return ctx, {
            "target_pfn": int(kv.get("target_pfn", "0"), 0),
            "decoy_pfn": int(kv.get("decoy_pfn", "0"), 0),
            "target_va": int(kv.get("target_va", "0"), 0),
            "source_run": kv.get("run_id", ""),
            "line": line,
        }
    except ValueError:
        return None


def load_w12_decoy_map(repo_root, path=None):
    """Load the per-context decoy PFN map from real scoped W12 controls.

    Accepted inputs (in order):
      1. a JSON map produced by tools/mmu_collect_w12_decoy.py;
      2. a directory of `runs/TEST-CTRL-W12-R0x` control runs;
      3. a single golden_output.txt (legacy `--all` control).
    Nothing is hardcoded; absent entries make the runner block.
    """
    rel = path or os.environ.get("MMU_W12_CONTROL_GOLDEN") or \
        W12_CONTROL_DEFAULT
    full = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
    out = {"path": full, "present": False, "contexts": {},
           "sha256": None, "sources": []}
    if os.path.isdir(full):
        for name in sorted(os.listdir(full)):
            run = os.path.join(full, name)
            if not os.path.isdir(run):
                continue
            # Only per-context scoped controls count.  An `--all` control has
            # a different allocation history and must never supply the map.
            if not re.search(r"W12.*R0[1-5]$", name):
                continue
            gold = None
            for cand in (os.path.join(run, "Run_Log", "golden_output.txt"),
                         os.path.join(run, "Run_Log",
                                      "observed_output.txt"),
                         os.path.join(run, "board.terminal")):
                if os.path.isfile(cand):
                    gold = cand
                    break
            if not gold:
                continue
            out["sources"].append({"run": name, "golden": gold,
                                   "sha256": _sha256_file(gold)})
            for line in _read_text(gold).splitlines():
                parsed = _parse_w12_line(line)
                if parsed:
                    ctx, rec = parsed
                    rec["source_run"] = name
                    rec["source_sha256"] = _sha256_file(gold)
                    out["contexts"][ctx] = rec
        out["present"] = bool(out["contexts"])
        return out
    if not os.path.isfile(full):
        return out
    out["present"] = True
    out["sha256"] = _sha256_file(full)
    if full.endswith(".json"):
        try:
            data = json.loads(_read_text(full))
        except ValueError:
            return out
        for ctx, rec in (data.get("contexts") or {}).items():
            out["contexts"][ctx] = dict(rec)
        out["sources"] = data.get("sources", [])
        return out
    for line in _read_text(full).splitlines():
        parsed = _parse_w12_line(line)
        if parsed:
            ctx, rec = parsed
            out["contexts"][ctx] = rec
    return out


def check_decoy_mapping(sample, decoy_map):
    """M04 must receive an explicit, verified decoy PFN for its context."""
    if sample.get("ModelID") != "M04":
        return True, "not M04"
    ctx = sample.get("ContextID", "")
    rec = decoy_map.get("contexts", {}).get(ctx)
    if not rec or not rec.get("decoy_pfn"):
        return False, ("no decoy PFN for %s in %s" %
                       (ctx, decoy_map.get("path")))
    if rec["decoy_pfn"] == rec.get("target_pfn"):
        return False, ("decoy PFN equals target PFN for %s" % ctx)
    return True, ("0x%x (target 0x%x) from %s sha256=%s" %
                  (rec["decoy_pfn"], rec.get("target_pfn", 0),
                   decoy_map["path"],
                   (decoy_map.get("sha256") or "")[:16]))


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_evidence_index(repo_root, path=None):
    rel = path or os.environ.get("MMU_EVIDENCE_INDEX") or \
        EVIDENCE_INDEX_DEFAULT
    full = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
    if not os.path.isfile(full):
        return {"path": full, "present": False, "contexts": {}}
    try:
        with open(full, "r") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return {"path": full, "present": False,
                "error": "unreadable: %s" % exc, "contexts": {}}
    data["path"] = full
    data["present"] = True
    return data


def evidence_for(index, model, context):
    """Runtime evidence for a model/context (TEST-ID runs feed formal rows)."""
    key = "%s/%s" % (model, context)
    rec = (index.get("contexts") or {}).get(key)
    if not rec:
        return {}
    return rec


def control_oracle_for(repo_root, model, workload, context):
    """Locate the independent no-fault control line for this context."""
    rel = CONTROL_ORACLE_CONTEXT_RUNS.get((model, context)) or \
        CONTROL_ORACLE_RUNS.get((model, workload))
    if not rel:
        return {"present": False, "detail": "no control-run mapping"}
    run = os.path.join(repo_root, rel)
    gold = os.path.join(run, "Run_Log", "golden_output.txt")
    if not os.path.isfile(gold):
        # Older/alternate layout: the per-run directory holds the terminal.
        gold = os.path.join(run, "Run_Log", "observed_output.txt")
    if not os.path.isfile(gold):
        gold = os.path.join(run, "board.terminal")
    if not os.path.isfile(gold):
        return {"present": False,
                "detail": "control run missing golden: %s" % _rel(repo_root, run)}
    prefix = "%s_RESULT" % workload
    prefixes = [prefix]
    if workload == "W10":
        # The two store variants keep Excel WorkloadID=W10 but print
        # W10S_RESULT.
        prefixes.append("W10S_RESULT")

    def find_line(path):
        text = _read_text(path)
        hit = next((ln for ln in text.splitlines()
                    if any(p in ln for p in prefixes) and
                    ("ctx=%s" % context) in ln), "")
        if not hit and workload == "W10":
            # A W10S variant control is single-variant and has no ctx= field.
            hit = next((ln for ln in text.splitlines()
                        if "W10S_RESULT" in ln), "")
        return hit

    line = find_line(gold)
    if not line:
        # run_mmu_case's golden grep predates W10S; the guest terminal is the
        # authoritative no-fault observation for those controls.
        for cand in (os.path.join(run, "Run_Log", "board.terminal"),
                     os.path.join(run, "run", "board.terminal")):
            if os.path.isfile(cand):
                line = find_line(cand)
                if line:
                    gold = cand
                    break
    if not line:
        return {"present": False,
                "detail": "%s has no %s line for %s" %
                          (_rel(repo_root, gold), prefix, context)}
    return {"present": True, "path": gold, "line": line,
            "sha256": _sha256_file(gold),
            "detail": "%s sha256=%s" % (_rel(repo_root, gold),
                                        _sha256_file(gold)[:16])}


def check_hook(model, hooks):
    info = hooks.get(model, {})
    if info.get("hook_present"):
        sites = "; ".join("%s:%s" % (s["file"], s["line"])
                          for s in info["sites"][:4])
        return True, "hook site(s): %s" % sites
    return False, ("no mmuFaultModelIs(\"%s\") / mmuFaultActivate(\"%s\") "
                   "call site in CHAOS/gem5/src" % (model, model))


def _config_flags(model):
    common = ["--mmu_fault_model", "--mmu_fault_enable",
              "--mmu_target_va", "--mmu_target_n", "--mmu_eligible_event_index"]
    if model == "M01":
        return common + ["--mmu_m01_va", "--mmu_m01_asid", "--mmu_m01_vmid",
                         "--mmu_m01_regime", "--mmu_m01_security_state",
                         "--mmu_m01_n"]
    if model == "M02":
        return common + ["--mmu_m02_va", "--mmu_m02_old_pfn",
                         "--mmu_m02_xor_mask", "--mmu_m02_dram_lo",
                         "--mmu_m02_dram_hi"]
    if model == "M03":
        return common + ["--mmu_m03_candidate_asid"]
    if model == "M04":
        return common + ["--mmu_m04_decoy_pfn", "--mmu_target_instance"]
    if model == "M05":
        return common + ["--mmu_m05_decoy_table_base",
                         "--mmu_target_walk_level", "--mmu_target_instance",
                         "--mmu_fault_persistence"]
    if model == "M06":
        return common + ["--mmu_target_walk_level"]
    if model == "M07":
        return common + ["--mmu_fault_persistence"]
    if model == "M08":
        return common + ["--mmu_m08_pa_xor_mask"]
    return common


def check_config(sample, model, wl, repo_root, config_text):
    problems = []
    detail = []
    # ROI resolution.
    if wl.get("roi_lo") is None or wl.get("roi_hi") is None:
        problems.append("ROI unknown (no run-command template)")
    # Target VA resolution + ROI containment.
    target_va, basis = resolve_target_va(sample, wl)
    if target_va is None:
        problems.append("target VA %s" % basis)
    elif wl.get("roi_lo") is not None and wl.get("roi_hi") is not None:
        if not (wl["roi_lo"] <= target_va < wl["roi_hi"]):
            problems.append(
                "target VA 0x%x outside ROI [0x%x,0x%x)" %
                (target_va, wl["roi_lo"], wl["roi_hi"]))
        else:
            detail.append("target VA 0x%x in ROI (%s)" % (target_va, basis))
    else:
        detail.append("target VA 0x%x (%s)" % (target_va, basis))
    # Target event / ordinal / mode.
    if not sample.get("TargetEvent"):
        problems.append("target event missing")
    ordinal = _s(sample.get("EventOrdinal"))
    if not ordinal:
        problems.append("eligible-event ordinal missing")
    else:
        m = re.search(r"(\d+)(?:st|nd|rd|th)?", ordinal)
        if not m or int(m.group(1)) < 1:
            problems.append("eligible-event ordinal %r not parseable" % ordinal)
        else:
            detail.append("eligible index %s" % m.group(1))
    mode = _s(sample.get("AccessMode"))
    if mode not in MODE_CHOICES:
        problems.append("access mode %r not in %s" %
                        (mode, sorted(MODE_CHOICES)))
    # Expected model target parameters (verified workload facts).
    params = model_params_detail(model, sample.get("ContextID"))
    detail.append("model params: " + ", ".join(
        "%s=%s" % (k, v) for k, v in sorted(params.items())))
    if model == "M05" and params.get("target_n") == 21:
        # M05 targets the L2 partial walk cache: 2 MiB (n=21) pages.
        detail.append("M05 requires 2 MiB (n=21) partial pages")
    # Model accepted + model-specific flags present in the real config.
    if "--mmu_fault_model" not in config_text:
        problems.append("config family has no --mmu_fault_model")
    if model not in config_text:
        problems.append("config family does not name model %s" % model)
    for flag in _config_flags(model):
        if flag not in config_text:
            problems.append("config flag missing: %s" % flag)
    return (not problems), "; ".join(problems) if problems else "; ".join(detail)


def check_context(sample, model, wl, model_info):
    problems = []
    cid = sample.get("ContextID")
    if cid not in CONTEXT_IDS:
        problems.append("ContextID %s not defined (R01-R05)" % cid)
    if not sample.get("DynamicContext"):
        problems.append("dynamic context empty")
    allowed = model_info.get(model, {}).get("Contexts", "")
    if allowed and not context_allowed(allowed, cid):
        problems.append("model %s contexts %r exclude %s" %
                        (model, allowed, cid))
    wid = sample.get("WorkloadID")
    if wid == "W9":
        mapped = [k for k, v in W9_CONTEXT_ASID.items() if v == cid]
        if not mapped:
            problems.append("W9 has no ASID identity for %s" % cid)
        asid_text = _s(sample.get("ASID_VMContext"))
        expected = "ASID %s" % chr(ord("A") + int(cid[1:]) - 1)
        if asid_text and asid_text != expected:
            problems.append("W9 %s ASID symbol %r != %r" %
                            (cid, asid_text, expected))
    elif wid == "W10":
        mapped = [k for k, v in W10_CONTEXT_VA.items() if v == cid]
        if not mapped:
            problems.append("W10 has no VA identity for %s" % cid)
        else:
            target = _parse_int(sample.get("TargetVA"))
            if target is not None and target != mapped[0]:
                problems.append(
                    "sample TargetVA 0x%x != W10 %s VA 0x%x" %
                    (target, cid, mapped[0]))
    else:
        # W11-W14 contexts are defined by the workload's --ctx switch; a
        # workload without a runnable rcS is a WORKLOAD blocker, not a
        # CONTEXT blocker.
        rcs = wl.get("rcs")
        if rcs:
            text = _read_text(rcs)
            if cid not in text and "--ctx all" not in text and \
                    "--all" not in text:
                problems.append("workload rcS neither names %s nor --all"
                                % cid)
    if wl.get("ready") and not wl.get("context_scopable"):
        problems.append("workload rcS cannot isolate one context "
                        "(no --ctx/--all pattern)")
    problems = [p for p in problems if p]
    detail = ("context %s defined (%s)" %
              (cid, sample.get("DynamicContext")))
    if wl.get("context_scopable"):
        detail += "; isolation: %s" % wl.get("context_scope_method")
    return (not problems), ("; ".join(problems) if problems else detail)


def check_oracle(sample, model, oracle_info, wl, workload_info):
    problems = []
    key = "%s_ORACLE" % model
    oracle = oracle_info.get(key)
    if not oracle:
        problems.append("worksheet 10 missing %s" % key)
    else:
        if not oracle.get("Definition"):
            problems.append("%s definition empty" % key)
        if not oracle.get("Rule"):
            problems.append("%s rule empty" % key)
    if not sample.get("ExpectedTerminalStates"):
        problems.append("sample expected terminal states empty")
    wl_oracle = workload_info.get(sample.get("WorkloadID"), {}).get(
        "Oracle", "")
    if not wl_oracle or wl_oracle.upper() in {"N/A", "NA", "NONE"}:
        problems.append("workload oracle undefined")
    # A concrete golden line is required once the workload is runnable.
    if wl.get("ready") and not wl.get("golden_prefix"):
        problems.append("golden output line format undefined")
    return (not problems), ("; ".join(problems) if problems else
                            "%s oracle + expected terminal + %s golden line" %
                            (key, wl.get("golden_prefix")))


def check_output_conflict(sample, repo_root):
    candidates = []
    sid = sample.get("SampleRunID")
    if sid:
        candidates.append(os.path.join(repo_root, "runs", sid))
    outdir = _s(sample.get("OutputDir"))
    if outdir:
        # ${OUTPUT_ROOT}/RunID/SubTaskID/Context/
        rel = outdir.replace("${OUTPUT_ROOT}", "runs").replace("$OUTPUT_ROOT",
                                                               "runs")
        rel = rel.lstrip("/")
        candidates.append(os.path.join(repo_root, rel))
    for path in candidates:
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if not f.startswith(".")]
            if files:
                return True, "existing results: %s" % _rel(repo_root, path)
        elif os.path.isfile(path):
            return True, "existing path: %s" % _rel(repo_root, path)
    status = _s(sample.get("ExecutionStatus"))
    if status and status.upper() not in {"NOT_STARTED", "PROPOSED"}:
        return True, "Excel ExecutionStatus=%s" % status
    return False, "no output path conflict"


def evaluate_sample(sample, ctx, repo_root, hooks, workloads,
                    config_text, run_script_defaults):
    model = sample.get("ModelID", "")
    context = sample.get("ContextID", "")
    workload = sample.get("WorkloadID", "")
    variant = w10s_variant(model, context)
    run_workload = variant["workload"] if variant else workload
    wl = workloads.get(run_workload, {})
    model_info = ctx["model_info"]
    oracle_info = ctx["oracle_info"]
    workload_info = ctx["workload_info"]
    evidence_index = load_evidence_index(repo_root)
    decoy_map = load_w12_decoy_map(repo_root)

    hook_ok, hook_detail = check_hook(model, hooks)
    workload_ok = bool(wl.get("ready"))
    if variant:
        workload_ok = workload_ok and os.path.isfile(
            os.path.join(repo_root, variant["rcs"]))
    workload_detail = ("ready: %s%s" % (
        _rel(repo_root, wl["binary"]) if wl.get("binary") else "<binary>",
        ("; variant %s rcS=%s" % (variant["variant"], variant["rcs"]))
        if variant else "") if workload_ok else
        "missing: %s" % ",".join(wl.get("missing") or ["workload entry"]))
    # The variant's own ROI/target overrides the Excel W10 read context.
    wl_check = wl
    if variant:
        wl_check = dict(wl)
        wl_check["roi_lo"], wl_check["roi_hi"] = variant["roi"]
    context_ok, context_detail = check_context(
        sample, model, wl_check, model_info)
    config_ok, config_detail = check_config(
        sample, model, wl_check, repo_root, config_text)
    output_conflict, output_detail = check_output_conflict(sample, repo_root)
    if output_conflict:
        config_ok = False
        config_detail = ("%s; %s" % (config_detail, output_detail)
                         if config_detail else output_detail)
    # Static definition vs runtime evidence are separate facts.
    context_definition_ok = bool(context_ok)
    sample_id = check_sample_id(sample)
    access_ok, access_detail = check_access_mode(sample, repo_root)
    decoy_ok, decoy_detail = check_decoy_mapping(sample, decoy_map)
    if not decoy_ok:
        config_ok = False
        config_detail = ("%s; %s" % (config_detail, decoy_detail)
                         if config_detail else decoy_detail)
    # Trace support is a fact about the file on disk, not a constant claim.
    validator_path = os.path.join(repo_root, "tools",
                                  "mmu_formal_validate.py")
    trace_ok = bool(model in VALIDATOR_MODELS and
                    os.path.isfile(validator_path) and
                    ('"%s"' % model) in _read_text(validator_path))
    trace_detail = ("%s present with a %s profile" %
                    (_rel(repo_root, validator_path), model)
                    if trace_ok else
                    "validator file/profile missing for %s" % model)
    oracle_ok, oracle_detail = check_oracle(
        sample, model, oracle_info, wl, workload_info)
    control = control_oracle_for(repo_root, model, workload, context)
    if not control["present"]:
        oracle_ok = False
        oracle_detail = ("%s; %s" % (oracle_detail, control["detail"])
                         if oracle_detail else control["detail"])
    seed = check_seed(sample)
    ev = evidence_for(evidence_index, model, context)
    ev_status = lambda key: (ev.get(key) or "NOT_RUN")
    runtime_status, runtime_detail = runtime_evidence_check(sample, ev, control)
    provenance = check_build_provenance(
        sample, repo_root, ctx.get("formal_config") or {},
        pilot_run_id=ev.get("run_id"))

    blockers = []
    if provenance["blocker"]:
        blockers.append(provenance["blocker"])
    if runtime_status:
        blockers.append(runtime_status)
    if not hook_ok:
        blockers.append("BLOCKED_HOOK")
    if not workload_ok:
        blockers.append("BLOCKED_WORKLOAD")
    if not context_ok:
        blockers.append("BLOCKED_CONTEXT")
    if not config_ok:
        blockers.append("BLOCKED_CONFIG")
    if not decoy_ok:
        blockers.append("BLOCKED_MISSING_DECOY_MAPPING")
    if not access_ok:
        blockers.append("BLOCKED_CONFIG")
    if not trace_ok:
        blockers.append("BLOCKED_TRACE")
    if not oracle_ok:
        blockers.append("BLOCKED_ORACLE")
    if not sample_id["frozen"]:
        blockers.append("BLOCKED_SAMPLE_ID_NOT_FROZEN")
    if seed["status"] == "MISSING":
        blockers.append("BLOCKED_MISSING_SEED")
    elif seed["status"] == "POLICY_INCONSISTENT":
        blockers.append("BLOCKED_SEED_POLICY")
    # Keep the authoritative precedence no matter how the list is built.
    blockers = [s for s in STATUS_PRECEDENCE if s in blockers]
    primary = blockers[0] if blockers else "READY"

    row = OrderedDict()
    row["SampleRunID"] = sample.get("SampleRunID", "")
    row["RunID"] = sample.get("RunID", "")
    row["ModelID"] = model
    row["WorkloadID"] = workload
    row["WorkloadVariant"] = variant["variant"] if variant else workload
    row["RunWorkload"] = run_workload
    row["ContextID"] = context
    row["DynamicContext"] = sample.get("DynamicContext", "")
    row["TargetEvent"] = sample.get("TargetEvent", "")
    row["AccessMode"] = _s(sample.get("AccessMode"))
    row["AccessModeStatus"] = "PASS" if access_ok else "BLOCKED"
    row["AccessModeDetail"] = access_detail
    row["DecoyPFN"] = (hex(decoy_map.get("contexts", {})
                          .get(context, {}).get("decoy_pfn", 0))
                       if model == "M04" else "")
    row["DecoyStatus"] = "PASS" if decoy_ok else "BLOCKED"
    row["DecoyDetail"] = decoy_detail
    row["Seed"] = seed["seed_raw"]
    row["SeedPresent"] = "YES" if seed["seed_valid"] else "NO"
    row["SeedPolicy"] = seed["seed_policy"]
    row["SeedSource"] = seed["seed_source"]
    row["SeedLiteralDeterministic"] = "YES" if \
        seed["seed_literal_deterministic"] else "NO"
    row["SeedUsedByGem5"] = "NO"
    row["SampleIDStatus"] = sample_id["status_raw"]
    row["SampleIDFrozen"] = "YES" if sample_id["frozen"] else "NO"
    row["SampleFreezeStatus"] = sample.get("SampleFreezeStatus", "")
    row["HookStatus"] = "PASS" if hook_ok else "BLOCKED"
    row["WorkloadStatus"] = "PASS" if workload_ok else "BLOCKED"
    row["ContextStatus"] = "PASS" if context_ok else "BLOCKED"
    row["ContextDefinitionStatus"] = "PASS" if context_definition_ok \
        else "BLOCKED"
    row["ConfigStatus"] = "PASS" if config_ok else "BLOCKED"
    row["TraceStatus"] = "PASS" if trace_ok else "BLOCKED"
    row["OracleStatus"] = "PASS" if oracle_ok else "BLOCKED"
    row["ControlOracleStatus"] = "PASS" if control["present"] else "MISSING"
    row["ControlOraclePath"] = control.get("path", "")
    row["ControlOracleSHA256"] = control.get("sha256", "")
    row["ControlOracleLine"] = control.get("line", "")
    row["ObservedOutputPath"] = ev.get("observed_output", "")
    row["RuntimeEvidenceStatus"] = runtime_status or "PASS"
    row["RuntimeGateDetail"] = runtime_detail
    row["BinaryProvenanceStatus"] = provenance["binary_status"]
    row["SourceProvenanceStatus"] = provenance["source_status"]
    row["BinarySHA256Manifest"] = provenance["manifest_gem5_sha256"]
    row["ProvenanceManifest"] = provenance["manifest"]
    row["ProvenanceDetail"] = provenance["detail"]
    row["RuntimePilotEvidenceStatus"] = ev_status("runtime_pilot")
    row["FaultActivationEvidenceStatus"] = ev_status("fault_activation")
    row["FaultConsumptionEvidenceStatus"] = ev_status("fault_consumption")
    row["PropagationEvidenceStatus"] = ev_status("propagation")
    row["TerminalOracleStatus"] = ev_status("terminal_oracle")
    row["TerminalState"] = ev.get("terminal_state", "")
    row["OracleResult"] = ev.get("oracle_result", "")
    row["RuntimeEvidenceDetail"] = (
        "index=%s" % _rel(repo_root, evidence_index["path"])
        if evidence_index.get("present") else
        "no runtime evidence index (%s)" % _rel(repo_root,
                                                evidence_index["path"]))
    row["SeedStatus"] = "PASS" if seed["seed_valid"] else "BLOCKED"
    row["OutputConflict"] = "YES" if output_conflict else "NO"
    row["PrimaryStatus"] = primary
    row["AllBlockers"] = ";".join(blockers) if blockers else "READY"
    row["HookDetail"] = hook_detail
    row["WorkloadDetail"] = workload_detail
    row["ContextDetail"] = context_detail
    row["ConfigDetail"] = config_detail
    row["TraceDetail"] = trace_detail
    row["OracleDetail"] = oracle_detail
    row["SampleIDDetail"] = sample_id["detail"]
    row["SeedDetail"] = seed["detail"]
    return row


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def write_reports(rows, ctx, outdir, excel_path, csv_path, repo_root,
                  run_script_defaults, workloads, hooks, global_issues):
    os.makedirs(outdir, exist_ok=True)
    csv_path_out = os.path.join(outdir, "MMU_40_Sample_DryRun.csv")
    md_path = os.path.join(outdir, "MMU_40_Sample_DryRun.md")
    seed_path = os.path.join(outdir, "Missing_Seed_Report.md")

    fieldnames = list(rows[0].keys())
    with open(csv_path_out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    primary_counts = Counter(r["PrimaryStatus"] for r in rows)
    model_counts = defaultdict(Counter)
    for r in rows:
        model_counts[r["ModelID"]][r["PrimaryStatus"]] += 1
    blocker_counts = Counter()
    for r in rows:
        for b in r["AllBlockers"].split(";"):
            if b and b != "READY":
                blocker_counts[b] += 1
    runtime_counts = Counter(r["RuntimeEvidenceStatus"] for r in rows)
    binary_prov_counts = Counter(r["BinaryProvenanceStatus"] for r in rows)
    source_prov_counts = Counter(r["SourceProvenanceStatus"] for r in rows)

    hook_lines = []
    for mid in sorted(hooks):
        info = hooks[mid]
        if info["hook_present"]:
            sites = ", ".join("%s:%s" % (s["file"], s["line"])
                              for s in info["sites"][:3])
            hook_lines.append("| %s | PRESENT | %s |" %
                              (mid, sites.replace("|", "/")))
        else:
            hook_lines.append("| %s | ABSENT | no explicit hook call site |"
                              % mid)

    wl_lines = []
    for wid in sorted(workloads):
        wl = workloads[wid]
        wl_lines.append(
            "| %s | %s | %s | %s | %s | %s | %s |" % (
                wid,
                "yes" if wl.get("binary") else "no",
                "yes" if wl.get("rcs") else "no",
                "yes" if wl.get("ckpt") else "no",
                ("0x%x..0x%x" % (wl["roi_lo"], wl["roi_hi"])
                 if wl.get("roi_lo") is not None else "unknown"),
                "READY" if wl.get("ready") else
                "missing " + ",".join(wl.get("missing") or []),
                wl.get("context_scope_method", "")))

    lines = []
    lines.append("# MMU 40-Sample Formal Dry-Run\n")
    lines.append("Generated by `tools/mmu_formal_preflight.py --dry-run`; "
                 "gem5 was not launched.\n")
    lines.append("- Authoritative Excel: `%s`" %
                 (excel_path or "<missing>"))
    lines.append("- Authority source: **%s**" %
                 (ctx.get("excel_source") or "<unknown>"))
    if ctx.get("excel_source") == "FROZEN_AUTHORITY":
        lines.append("- The researcher-frozen authority copy is the default "
                     "input (2026-11-11 decision).")
    elif excel_path and os.path.basename(excel_path) != \
            os.path.basename(REQUESTED_XLSX):
        lines.append("- **FOR-MISMATCH-01**: the requested filename "
                     "`%s` does not exist; the design package ships `%s`. "
                     "The shipped file is used and recorded here."
                     % (os.path.basename(REQUESTED_XLSX),
                        os.path.basename(excel_path)))
    lines.append("- Sample CSV cross-checked: `%s` (%s)" %
                 (csv_path or "<none>", ctx.get("csv_source") or "<unknown>"))
    lines.append("- Samples: **%d** (expected 40)" % len(rows))
    lines.append("- Seed: literal `%s`, SeedPolicy=%s, SeedSource=%s. "
                 "No numeric seed was generated, hashed, timestamped, "
                 "coerced or passed to gem5.\n" %
                 (SEED_LITERAL_DETERMINISTIC, SEED_POLICY_DETERMINISTIC,
                  SEED_SOURCE_RESEARCHER_APPROVED))

    lines.append("## Primary status tally\n")
    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    for status in STATUS_VOCABULARY:
        lines.append("| %s | %d |" % (status, primary_counts.get(status, 0)))
    lines.append("")
    lines.append("Precedence: **BINARY > SOURCE > HOOK > WORKLOAD > CONTEXT "
                 "> CONFIG > DECOY > TRACE > ORACLE > SAMPLE_ID_NOT_FROZEN > "
                 "SEED** (SEED = MISSING or POLICY; a seed-gate failure never "
                 "suppresses another blocker).\n")
    lines.append("Runtime Gate-3 mapping: no pilot evidence / PARTIAL / "
                 "TRACE_INCOMPLETE / missing trace -> BLOCKED_TRACE; "
                 "NO_ELIGIBLE_EVENT or NOT_ACTIVATED -> BLOCKED_HOOK (a "
                 "knowably-wrong target would be BLOCKED_CONTEXT); "
                 "NOT_OBSERVED or inadmissible terminal or missing control "
                 "oracle -> BLOCKED_ORACLE; only ACTIVATED + admissible "
                 "terminal + complete trace + independent control => READY.\n")
    lines.append("Static checks never stand in for runtime evidence.  "
                 "`ContextDefinitionStatus` describes the authoritative "
                 "definition; `RuntimePilotEvidenceStatus`, "
                 "`FaultActivationEvidenceStatus`, "
                 "`FaultConsumptionEvidenceStatus`, "
                 "`PropagationEvidenceStatus` and `TerminalOracleStatus` are "
                 "`NOT_RUN`/`NOT_OBSERVED` until a real pilot/validator "
                 "artefact exists.\n")

    lines.append("## Per-model primary status\n")
    lines.append("| Model | Samples | " +
                 " | ".join(STATUS_VOCABULARY) + " |")
    lines.append("|---|---:|" + "---:|" * len(STATUS_VOCABULARY))
    for model in sorted(model_counts):
        c = model_counts[model]
        lines.append("| %s | %d | %s |" % (
            model, sum(c.values()),
            " | ".join(str(c.get(s, 0)) for s in STATUS_VOCABULARY)))
    lines.append("")

    lines.append("## All-blocker tally (a sample may have several)\n")
    lines.append("| Blocker | Samples |")
    lines.append("|---|---:|")
    for status in STATUS_PRECEDENCE:
        lines.append("| %s | %d |" % (status, blocker_counts.get(status, 0)))
    lines.append("")

    lines.append("## Hook evidence from the live C++ source\n")
    lines.append("| Model | Hook | Evidence |")
    lines.append("|---|---|---|")
    lines.extend(hook_lines)
    lines.append("")

    lines.append("## Workload assets discovered in the live tree\n")
    lines.append("| Workload | binary | rcS | checkpoint | ROI | state | "
                 "context isolation |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.extend(wl_lines)
    lines.append("")
    if run_script_defaults:
        scripts = sorted({d.get("script", "") for d in
                          run_script_defaults.values() if d.get("script")})
        lines.append("ROI/checkpoint/rcS defaults parsed from: %s\n" %
                     ", ".join("`%s`" % s for s in scripts))

    lines.append("## Per-sample dry-run\n")
    header = ("| SampleRunID | Model | Workload | Variant | Context | Hook "
              "| Workload | ContextDef | Config | AccessMode | Decoy | Trace "
              "| Oracle | ControlOracle | SampleID | Seed | Runtime | "
              "Activation | Consumption | Propagation | TerminalOracle "
              "| Primary | All blockers |")
    lines.append(header)
    lines.append("|---" * len(header.strip("|").split("|")) + "|")
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | "
                     "%s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s "
                     "| **%s** | %s |" % (
                         r["SampleRunID"], r["ModelID"], r["WorkloadID"],
                         r["WorkloadVariant"], r["ContextID"],
                         r["HookStatus"], r["WorkloadStatus"],
                         r["ContextDefinitionStatus"], r["ConfigStatus"],
                         r["AccessModeStatus"],
                         ("%s %s" % (r["DecoyStatus"], r["DecoyPFN"]))
                         if r["ModelID"] == "M04" else "-",
                         r["TraceStatus"], r["OracleStatus"],
                         r["ControlOracleStatus"],
                         "FROZEN" if r["SampleIDFrozen"] == "YES" else "NOT_FROZEN",
                         "%s (%s)" % (r["SeedStatus"], r["Seed"]),
                         r["RuntimePilotEvidenceStatus"],
                         r["FaultActivationEvidenceStatus"],
                         r["FaultConsumptionEvidenceStatus"],
                         r["PropagationEvidenceStatus"],
                         r["TerminalOracleStatus"],
                         r["PrimaryStatus"], r["AllBlockers"]))
    lines.append("")

    lines.append("## Evidence details for non-PASS checks\n")
    for r in rows:
        if r["PrimaryStatus"] == "READY":
            continue
        parts = []
        if r["HookStatus"] != "PASS":
            parts.append("hook: " + r["HookDetail"])
        if r["WorkloadStatus"] != "PASS":
            parts.append("workload: " + r["WorkloadDetail"])
        if r["ContextStatus"] != "PASS":
            parts.append("context: " + r["ContextDetail"])
        if r["ConfigStatus"] != "PASS":
            parts.append("config: " + r["ConfigDetail"])
        if r["OracleStatus"] != "PASS":
            parts.append("oracle: " + r["OracleDetail"])
        if r["SeedStatus"] != "PASS":
            parts.append("seed: " + r["SeedDetail"])
        if r["RuntimeEvidenceStatus"] != "PASS":
            parts.append("runtime: %s (%s)" %
                         (r["RuntimeEvidenceStatus"],
                          r["RuntimeGateDetail"]))
        if r["BinaryProvenanceStatus"] in ("MISMATCH", "NO_MANIFEST") or \
                r["SourceProvenanceStatus"] in ("MISMATCH", "NO_MANIFEST"):
            parts.append("provenance: binary=%s source=%s (%s)" %
                         (r["BinaryProvenanceStatus"],
                          r["SourceProvenanceStatus"],
                          r["ProvenanceDetail"]))
        lines.append("- **%s**: %s" % (r["SampleRunID"],
                                       "; ".join(parts) if parts else "-"))
    lines.append("")

    lines.append("## Authoritative cross-check issues\n")
    if ctx["issues"] or global_issues:
        for issue in ctx["issues"] + global_issues:
            lines.append("- %s" % issue)
    else:
        lines.append("- none: 40 unique samples and all triples match "
                     "worksheets 03/05/06/07 and the CSV mirror.")
    lines.append("")

    with open(md_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    # Missing-seed report: one row per sample, all other checks tallied.
    seed_lines = []
    seed_lines.append("# Seed Gate Report\n")
    seed_lines.append(
        "Policy: the seed is taken **only** from the authoritative workbook "
        "(`07_Sample_Matrix.Seed` + `SeedPolicy`). The researcher-approved "
        "literal `%s` is valid when and only when SeedPolicy=%s; it is never "
        "parsed as an integer and never passed to gem5. A numeric seed under "
        "the deterministic policy (or the literal under a random policy) is "
        "`BLOCKED_SEED_POLICY`; a blank/placeholder cell is "
        "`BLOCKED_MISSING_SEED`.\n" %
        (SEED_LITERAL_DETERMINISTIC, SEED_POLICY_DETERMINISTIC))
    missing = [r for r in rows if r["SeedStatus"] != "PASS"]
    seed_lines.append("- Samples failing the seed gate: **%d / %d**" %
                      (len(missing), len(rows)))
    distinct = sorted({r["Seed"] for r in rows})
    if len(distinct) == 1:
        seed_lines.append("- Every authoritative seed cell currently reads: "
                          "`%s`" % distinct[0])
    else:
        seed_lines.append("- Distinct seed cells: %s" % distinct)
    seed_lines.append("")
    seed_lines.append("| SampleRunID | Model | Workload | Context | Seed cell "
                      "| Hook | Workload | Context | Config | Trace | Oracle "
                      "| Output | PRIMARY | Other blockers |")
    seed_lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        others = [b for b in r["AllBlockers"].split(";")
                  if b and b not in ("BLOCKED_MISSING_SEED", "READY")]
        seed_lines.append("| %s | %s | %s | %s | `%s` | %s | %s | %s | %s | "
                          "%s | %s | %s | **%s** | %s |" % (
                              r["SampleRunID"], r["ModelID"],
                              r["WorkloadID"], r["ContextID"], r["Seed"],
                              r["HookStatus"], r["WorkloadStatus"],
                              r["ContextStatus"], r["ConfigStatus"],
                              r["TraceStatus"], r["OracleStatus"],
                              "CONFLICT" if r["OutputConflict"] == "YES"
                              else "ok", r["PrimaryStatus"],
                              ";".join(others) if others else "-"))
    seed_lines.append("")
    seed_lines.append("## Consequence\n")
    if not missing:
        seed_lines.append(
            "The frozen seed gate is **satisfied for all %d samples**: every "
            "Seed is the literal `%s` with SeedPolicy=%s. Formal execution "
            "still requires the remaining runtime-evidence blockers below to "
            "be closed first.\n" %
            (len(rows), SEED_LITERAL_DETERMINISTIC,
             SEED_POLICY_DETERMINISTIC))
    else:
        seed_lines.append(
            "The seed gate is not satisfied; the rows above must be fixed "
            "before a formal run. Other blockers remain independent.\n")
    with open(seed_path, "w") as fh:
        fh.write("\n".join(seed_lines) + "\n")

    return {
        "csv": csv_path_out,
        "md": md_path,
        "seed_md": seed_path,
        "primary_counts": dict(primary_counts),
        "blocker_counts": dict(blocker_counts),
        "runtime_counts": dict(runtime_counts),
        "binary_provenance_counts": dict(binary_prov_counts),
        "source_provenance_counts": dict(source_prov_counts),
        "missing_seed_count": len(missing),
        "seed_gate_fail_count": len(missing),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_environment(repo_root, excel_path=None, csv_path=None):
    excel = resolve_excel(excel_path, repo_root)
    csv_path_resolved = resolve_csv(csv_path, repo_root)
    samples, ctx = load_samples(excel, csv_path_resolved)
    # Record, never guess, which authority copy was used.  The frozen
    # researcher copies are preferred; an explicit CLI path overrides them.
    ctx["excel"] = excel
    ctx["csv"] = csv_path_resolved
    ctx["excel_source"] = authority_label(excel, repo_root)
    ctx["csv_source"] = authority_label(csv_path_resolved, repo_root)
    ctx["frozen_authority"] = frozen_authority_paths(repo_root)
    ctx["formal_config"] = load_formal_config(repo_root)
    hooks = scan_hooks(repo_root, sorted(MODEL_WORKLOAD))
    run_script_defaults = _parse_run_script(repo_root)
    workloads = {}
    # W10S is not one of the 40 formal samples; it is discovered because the
    # Phase-3 pilots use it for the M06 EL0-write cold-walk / M08 write arm.
    workload_ids = sorted({s["WorkloadID"] for s in samples} | {"W10S"})
    for wid in workload_ids:
        workloads[wid] = discover_workload(repo_root, wid,
                                           run_script_defaults)
    config_text = _read_text(os.path.join(
        repo_root, "configs", "se", "arm_chaos_fs.py"))
    return excel, samples, ctx, hooks, workloads, run_script_defaults, \
        config_text


def self_check(repo_root, excel_path=None, csv_path=None):
    """Verify every tool/asset the formal tools need, with paths + SHA256.

    Multi-GB images are recorded by absolute path and hash, never copied.
    """
    assets = []
    files = [
        ("tool", "tools/mmu_formal_preflight.py"),
        ("tool", "tools/mmu_formal_runner.py"),
        ("tool", "tools/mmu_formal_validate.py"),
        ("tool", "tools/mmu_trace_validate_v3.py"),
        ("tool", "tools/mmu_trace_validate_v4.py"),
        ("config", "configs/se/arm_chaos_fs.py"),
        ("config", "configs/fs/lsu_b0_fs.py"),
        ("kernel", "gem5-fs/vmlinux"),
        ("bootloader", "gem5-fs/boot.arm64"),
        ("disk_template", "runs/disks/mmu_template.img"),
        ("gem5_binary", "CHAOS/gem5/build/ARM/gem5.opt"),
        ("sample_csv", AUTHORITATIVE_CSV),
        ("experiment_config",
         os.path.join(DESIGN_DIR, "MMU_Final_Experiment_Config.json")),
        ("experiment_config_yaml",
         os.path.join(DESIGN_DIR, "MMU_Final_Experiment_Config.yaml")),
    ]
    frozen = frozen_authority_paths(repo_root)
    files += [
        ("frozen_authority_xlsx", frozen["xlsx"]),
        ("frozen_authority_csv", frozen["csv"]),
        ("frozen_formal_config_json", frozen["config_json"]),
        ("frozen_formal_config_yaml", frozen["config_yaml"]),
    ]
    for kind, rel in files:
        full = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
        rec = {"kind": kind, "path": full, "exists": os.path.exists(full)}
        if rec["exists"] and os.path.isfile(full):
            rec["sha256"] = _sha256_file(full)
            rec["bytes"] = os.path.getsize(full)
        assets.append(rec)
    excel = excel_path
    if excel is None:
        try:
            excel = resolve_excel(None, repo_root)
        except AuthoritativeError:
            excel = None
    assets.append({"kind": "authoritative_excel", "path": excel,
                   "source": authority_label(excel, repo_root),
                   "exists": bool(excel and os.path.isfile(excel)),
                   **({"sha256": _sha256_file(excel)}
                      if excel and os.path.isfile(excel) else {})})
    checkpoints = sorted(
        os.path.join(repo_root, "runs", d) for d in ("mmu_boot5", "mmu_boot7")
        if os.path.isdir(os.path.join(repo_root, "runs", d)))
    for ck in checkpoints:
        assets.append({"kind": "checkpoint_dir", "path": ck, "exists": True})
    missing = [a["path"] for a in assets if not a["exists"]]
    return {"repo_root": repo_root, "assets": assets, "missing": missing,
            "ok": not missing}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="MMU formal 40-sample preflight / dry-run (never runs "
                    "gem5)")
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--excel", default=None,
                    help="explicit authoritative Excel override "
                         "(default: frozen authority copy, then design "
                         "package)")
    ap.add_argument("--csv", default=None,
                    help="explicit MMU_Sample_Matrix.csv override "
                         "(default: frozen authority copy, then design "
                         "package)")
    ap.add_argument("--outdir", default=None,
                    help="default: <repo>/phase3/formal")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="the only supported mode; never launches gem5")
    ap.add_argument("--summary-json", default=None,
                    help="optional JSON summary path")
    ap.add_argument("--self-check", action="store_true",
                    help="verify tool/asset dependencies (paths + SHA256) "
                         "and exit")
    args = ap.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    outdir = args.outdir or os.path.join(repo_root, "phase3", "formal")

    if args.self_check:
        result = self_check(repo_root, args.excel, args.csv)
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0 if result["ok"] else 5

    try:
        excel, samples, ctx, hooks, workloads, run_script_defaults, \
            config_text = build_environment(repo_root, args.excel, args.csv)
    except AuthoritativeError as exc:
        print("PREFLIGHT ERROR: %s" % exc, file=sys.stderr)
        return 2

    rows = [evaluate_sample(s, ctx, repo_root, hooks, workloads,
                            config_text, run_script_defaults)
            for s in samples]
    global_issues = []
    if len(rows) != 40:
        global_issues.append("sample count is %d, expected 40" % len(rows))

    csv_resolved = ctx.get("csv")
    summary = write_reports(rows, ctx, outdir, excel, csv_resolved, repo_root,
                            run_script_defaults, workloads, hooks,
                            global_issues)
    summary.update({
        "excel": excel,
        "csv_input": csv_resolved,
        "excel_source": ctx.get("excel_source"),
        "csv_source": ctx.get("csv_source"),
        "seed_policy": SEED_POLICY_DETERMINISTIC,
        "seed_literal": SEED_LITERAL_DETERMINISTIC,
        "seed_source": SEED_SOURCE_RESEARCHER_APPROVED,
        "repo_root": repo_root,
        "sample_count": len(rows),
        "hooks": hooks,
        "workloads": workloads,
        "triple_issues": ctx["issues"] + global_issues,
    })
    if args.summary_json:
        with open(args.summary_json, "w") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True, default=str)

    print(json.dumps({
        "samples": len(rows),
        "authority": {
            "excel": summary["excel"],
            "excel_source": summary["excel_source"],
            "csv": summary["csv_input"],
            "csv_source": summary["csv_source"],
        },
        "seed_policy": summary["seed_policy"],
        "seed_literal": summary["seed_literal"],
        "seed_source": summary["seed_source"],
        "primary_counts": summary["primary_counts"],
        "all_blocker_counts": summary["blocker_counts"],
        "runtime_counts": summary["runtime_counts"],
        "binary_provenance_counts": summary["binary_provenance_counts"],
        "source_provenance_counts": summary["source_provenance_counts"],
        "missing_seed_count": summary["missing_seed_count"],
        "seed_gate_fail_count": summary["seed_gate_fail_count"],
        "outs": {k: summary[k] for k in ("csv", "md", "seed_md")},
        "triple_issues": summary["triple_issues"],
    }, indent=2, sort_keys=True))
    return 0 if len(rows) == 40 else 2


if __name__ == "__main__":
    sys.exit(main())
