#!/usr/bin/env python3
"""LSU v3.3.3 formal campaign collector (campaign-root isolated).

Every formal evidence value is read from ``--runs <CampaignRoot>``.  The design
matrix / ROI mapping provide **identity only** (SampleRunID, model, context,
seed, workload, ROI and the injection identity); they never supply a run
outcome.  Nothing under a historical audit tree is read, and a value that cannot
be derived from the campaign root is reported as ``UNKNOWN`` / ``n/a`` -- never
defaulted to ``0`` or ``PASS``.

Design rules (see ``audit_launch_fix_v333/README_INTERFACES.md``):

* a missing run dir / ``campaign.json`` / ``summary.json``, an identity or SHA
  disagreement, a timeout or a missing required output is a non-PASS status;
* ``EvidenceKind=FORMAL`` only for a run directory under ``--runs`` whose
  ``campaign.json`` matches ``--campaign-id`` and whose identity matches the
  design;
* control runs are graded by ``lsu_v333_control_proof.classify_control_run``;
  A03/SP05/RP01 fault runs also carry
  ``lsu_v333_qualified.qualified_evidence`` and that status is never upgraded.

CLI::

    python3 tools/lsu_v333_launch.py --runs <CampaignRoot> \\
        --campaign-id <id> \\
        --design-matrix <60_SAMPLE_MATRIX.csv> \\
        --design-mapping <LSU_60Context_ROI_Percentile_Mapping.csv> \\
        --out <dir> [--manifest-only]

``main(argv) -> int`` returns 0 only when every scheduled task is FORMAL and
evidence-complete (success statuses below), else 1.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import lsu_run_state  # noqa: E402
from lsu_v333_control_proof import classify_control_run  # noqa: E402
from lsu_v333_qualified import QUALIFIED_MODELS, qualified_evidence  # noqa: E402

DEFAULT_BINARY_SHA = (
    "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd")
DEFAULT_CONFIG_SHA = (
    "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225")

FORMAL = "FORMAL"
NON_FORMAL = "NON_FORMAL"
UNKNOWN = "UNKNOWN"
NOT_AVAILABLE = "n/a"

# Task outcomes that count as evidence-complete for the launch gate.
# A fault run may legitimately terminate ORACLE_FAIL (the injected fault was
# expected to change the checksum); a control run may not -- it must reproduce
# the golden checksum, so only COMPLETED is a control success.
FAULT_SUCCESS_STATUSES = frozenset(
    {"COMPLETED", "ORACLE_FAIL", "QUALIFIED", "TRACE_INCOMPLETE"})
CONTROL_SUCCESS_STATUSES = frozenset({"COMPLETED"})
# Backwards-compatible alias; role-aware gates use the two sets above.
SUCCESS_STATUSES = FAULT_SUCCESS_STATUSES
WATCHDOG_TERMINALS = frozenset({"HANG_WATCHDOG"})
MEASURED_TERMINALS = frozenset(
    {"MASKED", "SQUASHED", "HANG_WATCHDOG", "CRASH"})

# The per-model injection log.  Mirrors tools/lsu_v332_matrix.MODEL_LOG_NAME.
MODEL_LOG_NAME = {
    "A01": "addrpath_injections.log",
    "A03": "addrpath_injections.log",
    "FW02": "lsq_fwd_injections.log",
    "FW05": "lsq_fwd_injections.log",
    "SQ01": "lsq_fwd_injections.log",
    "SQ03": "lsq_fwd_injections.log",
    "SP05": "lsq_fwd_injections.log",
    "DA04": "lsq_fwd_injections.log",
    "LP01": "l1d_fwd_injections.log",
    "MD04": "md04_injections.log",
    "LQ04": "lq04_injections.log",
    "RP01": "lsq_fwd_injections.log",
}

# A03/RP01 have a documented partial terminal: the model watchdog cuts the
# converted trace, so summary + prop_trace + oracle + marker stand in.
PARTIAL_MARKER_MODELS = ("A03", "RP01")
WATCHDOG_MARKERS = {
    "A03": ("A03_WATCHDOG_EXPIRED", "A03_WATCHDOG"),
    "RP01": ("CHAOS_RP01_WATCHDOG", "RP01_WATCHDOG_EXPIRED", "RP01_WATCHDOG"),
}

# Static design expectations (not evidence): one line per fault model.  These
# describe the intended injection site/terminal; measured values always come
# from the run dir.
MODEL_INFO = {
    "A01": ("AGU EA -> LSQ pushRequest (PRE)", "a01_bit3_load / F0",
            "SDC / MASKED / SQUASHED"),
    "A03": ("AGU EA -> LSQ pushRequest (PRE)", "a03_bit3_stuck0_load / F5",
            "SDC / HANG_WATCHDOG"),
    "FW02": ("LSQFwd forwarding decision", "f6_fw02", "SDC / MASKED"),
    "FW05": ("LSQFwd older-source substitution", "fw05_older_src", "SDC"),
    "SQ01": ("SQ entry data", "sq01_bit3", "SDC"),
    "SQ03": ("SQ _canWB", "sq03_canwb", "MASKED / visibility"),
    "SP05": ("completeStore", "sp05_complete", "SDC"),
    "DA04": ("Request byte-enable", "da04_be_bit0", "SDC"),
    "LP01": ("L1D load response", "post-check", "SDC"),
    "MD04": ("LSQ checkViolations", "md04", "SDC / MASKED"),
    "LQ04": ("LQ entry lifetime", "lq04", "MASKED"),
    "RP01": ("Partial-address replay", "rp01_skip_replay", "HANG_WATCHDOG"),
}

MANIFEST_COLS = (
    "RunID", "ModelID", "ContextID", "SampleRunID", "Seed", "Role",
    "Status", "EvidenceKind", "Evidence", "Reason", "MissingEvidence",
    "CampaignID", "CampaignStatus",
    "TerminalState", "TerminalReason", "OracleResult", "InjectionCount",
    "ControlZeroProof", "QualifiedStatus", "TraceCompleteness",
    "Binary_SHA256", "Config_SHA256", "ELF_SHA256",
    "Workload", "ELF", "InjectionConfig", "ExpectedTerminal",
    "ROI_Start", "ROI_End", "ROI_N", "Warmup", "Percentile",
    "EligibleEventOrdinal", "DynInstSeq", "PC", "VA", "PA", "LQEntry",
    "SQEntry", "InjectionEnabled", "InjectorMounted", "FaultEnabled",
    "SuppressionReason", "InjectionAttemptCount", "InjectionAppliedCount",
    "FormalManifest",
)


# ---------------------------------------------------------------------------
# small IO / value helpers
# ---------------------------------------------------------------------------
def _load_csv(path: Path) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return []


def _read_json(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _as_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return int(value.strip())
    return None


def _as_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no"):
        return False
    return None


def _same_value(left, right) -> bool:
    """Compare strings/ints (a seed may be ``123`` or ``"123"``)."""
    if left is None or right is None:
        return False
    li, ri = _as_int(left), _as_int(right)
    if li is not None and ri is not None:
        return li == ri
    return str(left).strip() == str(right).strip()


# The frozen design matrix spells "no input hash" with several sentinels
# (``N/A``, ``n/a``, the Chinese ``无（内建输入）``).  None of them is a hash;
# comparing an ELF SHA against the literal text would always disagree.
_NOT_AVAILABLE_TOKENS = frozenset({"n/a", "na", "无（内建输入）", "无"})


def _input_hash_available(value) -> bool:
    """True only when the design matrix carries an actual input hash."""
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in _NOT_AVAILABLE_TOKENS


def _sha_matches(observed, expected) -> bool:
    return bool(observed) and bool(expected) and \
        str(observed).strip().lower() == str(expected).strip().lower()


def _yes_no_unknown(value) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return UNKNOWN


def _ctx_of(sample_run_id: str) -> str:
    return str(sample_run_id)[-3:]


_IDENTITY_KEYS = ("seq", "pc", "va", "pa", "lq", "sq")


def parse_identity(text: str | None) -> dict[str, str]:
    """Parse ``seq=..;pc=..;va=..;pa=..;lq=..;sq=..`` from the design mapping."""
    out = {key: NOT_AVAILABLE for key in _IDENTITY_KEYS}
    for part in (text or "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key, value = key.strip(), value.strip()
        if key in out and value:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# run-dir evidence probes
# ---------------------------------------------------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _watchdog_marker(run_dir: Path, model: str) -> str | None:
    tokens = WATCHDOG_MARKERS.get(model)
    if not tokens:
        return None
    names = [MODEL_LOG_NAME.get(model), "stdout.log", "stderr.log"]
    for name in names:
        if not name:
            continue
        path = run_dir / name
        if not path.is_file():
            continue
        text = _read_text(path)
        for token in tokens:
            if token in text:
                return token
    return None


def _partial_watchdog(run_dir: Path, model: str) -> str | None:
    """Documented A03/RP01 partial: marker + summary + prop_trace + oracle."""
    if model not in PARTIAL_MARKER_MODELS:
        return None
    for name in ("summary.json", "prop_trace.csv.gz", "oracle.log"):
        if not (run_dir / name).is_file():
            return None
    return _watchdog_marker(run_dir, model)


def _trace_has_injection(run_dir: Path) -> bool:
    path = run_dir / "trace_v31.jsonl"
    if not path.is_file():
        return False
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"injection"' not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict) and (
                        record.get("event_type") == "injection"
                        or (record.get("record_type") == "event"
                            and record.get("event_type") == "injection")):
                    return True
    except OSError:
        return False
    return False


def _injection_witness(run_dir: Path, summary: dict | None) -> str | None:
    """A fault injection corroborated by the run itself (not the model log).

    The dedicated model log is the primary witness.  When it is absent but the
    run's own ``trace_v31.jsonl`` records an injection event (or the summary
    records a positive injection count), the injection is still evidenced by
    two independent per-run sources; the missing log is not treated as missing
    evidence in that case.
    """
    if _trace_has_injection(run_dir):
        return "trace_v31.jsonl:injection_event"
    if isinstance(summary, dict):
        count = _as_int(summary.get("injection_count"))
        if count is not None and count > 0:
            return "summary.json:injection_count"
    return None


# Mirrors tools/lsu_v332_matrix.py:driver_for/required_outputs: RP01 always
# runs the direct gem5 driver and A03's fault run is direct.  Direct runs do
# not emit the converted ``trace_v31.jsonl``; requiring it here would grade
# legitimate evidence as incomplete (e.g. the five zero-injection RP01
# controls, whose raw ``prop_trace.csv.gz`` is present).
DIRECT_FAULT_MODELS = frozenset({"A03"})


def _expects_converted_trace(model: str, role: str) -> bool:
    return not (model == "RP01"
                or (model in DIRECT_FAULT_MODELS and role == "fault"))


def _missing_outputs(run_dir: Path, model: str, role: str,
                     summary: dict | None, partial_marker: str | None
                     ) -> list[str]:
    missing: list[str] = []
    if not (run_dir / "summary.json").is_file():
        missing.append("summary.json")
    if not (run_dir / "oracle.log").is_file():
        missing.append("oracle.log")
    if (partial_marker is None and _expects_converted_trace(model, role)
            and not (run_dir / "trace_v31.jsonl").is_file()):
        missing.append("trace_v31.jsonl")
    if role == "fault" and partial_marker is None:
        log_name = MODEL_LOG_NAME.get(model)
        if log_name and not (run_dir / log_name).is_file():
            if _injection_witness(run_dir, summary) is None:
                missing.append(log_name)
    return missing


def _campaign_hard_failure(status) -> str | None:
    text = str(status or "").strip().upper()
    if text in {"FAILED", "TIMEOUT", "OUTPUT_INCOMPLETE", "HASH_MISMATCH"}:
        return text
    return None


# ---------------------------------------------------------------------------
# per-record collection
# ---------------------------------------------------------------------------
def _base_record(matrix_row: dict, mapping_row: dict | None,
                 model: str, ctx: str, role: str, run_dir: Path) -> dict:
    workload_path = str(matrix_row.get("WorkloadPath") or "")
    identity = parse_identity(
        (mapping_row or {}).get("InjectionIdentity", ""))
    info = MODEL_INFO.get(model, ("", "", ""))
    record = {column: NOT_AVAILABLE for column in MANIFEST_COLS}
    record.update({
        "RunID": matrix_row.get("RunID") or f"{model}-{ctx}",
        "ModelID": model,
        "ContextID": ctx,
        "SampleRunID": matrix_row.get("SampleRunID", NOT_AVAILABLE),
        "Seed": matrix_row.get("Seed", NOT_AVAILABLE),
        "Role": role,
        "Status": None,
        "EvidenceKind": NON_FORMAL,
        "Evidence": str(run_dir),
        "Reason": "",
        "MissingEvidence": "",
        "Workload": Path(workload_path).name if workload_path else NOT_AVAILABLE,
        "ELF": workload_path or NOT_AVAILABLE,
        "InjectionConfig": info[1],
        "ExpectedTerminal": info[2],
        "InjectionEnabled": "YES" if role == "fault" else "NO",
        "InjectionAttemptCount": UNKNOWN,
        "InjectionAppliedCount": UNKNOWN,
        "InjectionCount": UNKNOWN,
        "FormalManifest": "GENERATED_BY_COLLECTOR",
        "DynInstSeq": identity["seq"],
        "PC": identity["pc"],
        "VA": identity["va"],
        "PA": identity["pa"],
        "LQEntry": identity["lq"],
        "SQEntry": identity["sq"],
    })
    if mapping_row:
        record.update({
            "ROI_Start": mapping_row.get("ROI_Start_Ordinal", NOT_AVAILABLE),
            "ROI_End": mapping_row.get("ROI_End_Ordinal", NOT_AVAILABLE),
            "ROI_N": mapping_row.get("ROI_N", NOT_AVAILABLE),
            "Warmup": "0",
            "Percentile": mapping_row.get("Percentile", NOT_AVAILABLE),
            "EligibleEventOrdinal": mapping_row.get(
                "Absolute_Eligible_Ordinal", NOT_AVAILABLE),
        })
    return record


def _finish(record: dict, status: str, reason: str,
            missing: list[str] | None = None) -> dict:
    record["Status"] = status
    record["Reason"] = reason
    record["MissingEvidence"] = ";".join(missing or [])
    return record


_ACCEPTED_ATTEMPT_STATES = (
    lsu_run_state.STATUS_COMPLETED, lsu_run_state.STATUS_ORACLE_FAIL)


def _canonical_evidence(run_dir: Path, campaign_id: str
                        ) -> tuple[Path | None, str | None]:
    """Resolve the canonical attempt directory for one task.

    Returns ``(evidence_dir, reason)``.  ``reason`` is ``None`` when the
    evidence is accepted; otherwise the task cannot be graded as FORMAL.
    A legacy flat run dir (no ``attempts/``, no ``canonical.json``) is kept
    readable as-is, but its evidence is graded normally later.
    """
    attempts_present = lsu_run_state.attempts_root(run_dir).is_dir()
    canonical = lsu_run_state.read_canonical(run_dir)
    if canonical is None:
        if attempts_present:
            # Executions exist but none was accepted: never read a blind flat
            # file or an arbitrary attempt.
            return None, "CANONICAL_MISSING"
        return run_dir, None
    attempt_id = str(canonical.get("attempt_id") or "")
    adir = lsu_run_state.attempt_dir(run_dir, attempt_id) if attempt_id else None
    if adir is None or not adir.is_dir():
        return None, "CANONICAL_ATTEMPT_MISSING"
    state = lsu_run_state.scan_task_state(run_dir, campaign_id)
    if state.get("state") not in _ACCEPTED_ATTEMPT_STATES:
        return None, f"CANONICAL_{state.get('state')}"
    return adir, None


def _contained(path: Path, root: Path) -> bool:
    try:
        return Path(path).resolve().is_relative_to(root)
    except OSError:
        return False


def collect_task(runs: Path, campaign_id: str, matrix_row: dict,
                 mapping_row: dict | None, role: str,
                 expected_binary_sha: str, expected_config_sha: str,
                 campaign_identity: dict | None) -> dict:
    """Grade one scheduled (model, context, role) task from its canonical run.

    Evidence is read from ``lsu_run_state.canonical_dir(run_dir)`` (the
    accepted attempt) rather than a flat run-dir read.  ``EvidenceKind`` is
    FORMAL only when the resolved evidence is under ``--runs``, the
    ``campaign.json`` campaign id and the full design identity match, the
    frozen SHAs agree and every required artifact is present.
    """
    model = str(matrix_row.get("FaultModelID") or "").strip()
    sample_run_id = str(matrix_row.get("SampleRunID") or "").strip()
    seed = matrix_row.get("Seed")
    ctx = _ctx_of(sample_run_id)
    run_dir = Path(runs) / f"{model}-{ctx}-{role}"
    record = _base_record(matrix_row, mapping_row, model, ctx, role, run_dir)
    record["Evidence"] = str(run_dir)

    # 1. run directory ------------------------------------------------------
    if not run_dir.is_dir():
        return _finish(record, "OUTPUT_INCOMPLETE", "RUN_DIR_MISSING",
                       ["run_dir"])

    # 1b. canonical attempt resolution --------------------------------------
    evidence_dir, resolve_reason = _canonical_evidence(run_dir, campaign_id)
    if resolve_reason is not None:
        return _finish(record, "OUTPUT_INCOMPLETE", resolve_reason,
                       ["canonical_attempt"])
    evidence_dir = Path(evidence_dir)
    record["Evidence"] = str(evidence_dir)

    # 1c. containment: resolved evidence must stay under --runs -------------
    runs_root = Path(runs).resolve()
    if not _contained(evidence_dir, runs_root):
        return _finish(record, "OUTPUT_INCOMPLETE", "EVIDENCE_OUTSIDE_RUNS",
                       ["evidence_path"])

    # 2. campaign.json (runner-written manifest) ----------------------------
    campaign = None
    for candidate in (evidence_dir / "campaign.json", run_dir / "campaign.json"):
        if not candidate.is_file() or not _contained(candidate, runs_root):
            continue
        campaign = _read_json(candidate)
        if campaign is not None:
            break
    if campaign is None:
        return _finish(record, "OUTPUT_INCOMPLETE", "MANIFEST_MISSING",
                       ["campaign.json"])

    cid = campaign.get("campaign_id")
    record["CampaignID"] = cid if cid is not None else NOT_AVAILABLE
    record["CampaignStatus"] = campaign.get("status", NOT_AVAILABLE)
    for key, column in (("binary_sha", "Binary_SHA256"),
                        ("config_sha", "Config_SHA256"),
                        ("elf_sha", "ELF_SHA256")):
        value = campaign.get(key)
        record[column] = value if value not in (None, "") else NOT_AVAILABLE

    if not _same_value(cid, campaign_id):
        record["Reason"] = "HISTORICAL_CAMPAIGN_MISMATCH"
        return _finish(record, "OUTPUT_INCOMPLETE",
                       "HISTORICAL_CAMPAIGN_MISMATCH", ["campaign_id"])

    identity_checks = (
        ("model", model), ("context", ctx), ("role", role),
        ("sample_run_id", sample_run_id), ("seed", seed),
    )
    id_mismatch = [name for name, expected in identity_checks
                   if not _same_value(campaign.get(name), expected)]
    if id_mismatch:
        return _finish(record, "OUTPUT_INCOMPLETE", "ID_MISMATCH",
                       id_mismatch)

    # 3. SHA gate ------------------------------------------------------------
    binary = campaign.get("binary_sha")
    config = campaign.get("config_sha")
    elf = campaign.get("elf_sha")
    sha_missing = [name for name, value in
                   (("binary_sha", binary), ("config_sha", config),
                    ("elf_sha", elf)) if not value]
    if sha_missing:
        return _finish(record, "OUTPUT_INCOMPLETE", "SHA_MISSING", sha_missing)

    sha_problems: list[str] = []
    if not _sha_matches(binary, expected_binary_sha):
        sha_problems.append("binary_sha")
    if not _sha_matches(config, expected_config_sha):
        sha_problems.append("config_sha")
    if campaign_identity is not None:
        if not _sha_matches(binary, campaign_identity.get("binary_sha")):
            sha_problems.append("identity.binary_sha")
        if not _sha_matches(config, campaign_identity.get("config_sha")):
            sha_problems.append("identity.config_sha")
        elf_map = campaign_identity.get("elf_sha")
        workload = record.get("Workload")
        if isinstance(elf_map, dict) and workload not in elf_map:
            # The design matrix may still carry an abstract, stale workload
            # name (e.g. ``sq_forward`` for the real ``sq_forward_w4v2``).
            # Recover the authorized basename from the campaign identity by
            # matching the run's own ELF hash; never relax the check itself.
            for name, expected in elf_map.items():
                if _sha_matches(elf, expected):
                    workload = name
                    record["Workload"] = name
                    break
        if isinstance(elf_map, dict) and workload in elf_map:
            if not _sha_matches(elf, elf_map[workload]):
                sha_problems.append(f"identity.elf_sha[{workload}]")
        elif _input_hash_available(matrix_row.get("InputHash")):
            if not _sha_matches(elf, matrix_row.get("InputHash")):
                sha_problems.append("design.InputHash")
    # De-duplicate while keeping order.
    sha_problems = list(dict.fromkeys(sha_problems))
    if sha_problems:
        return _finish(record, "HASH_MISMATCH", "SHA_DISAGREEMENT",
                       sha_problems)

    # 4. summary.json --------------------------------------------------------
    summary = _read_json(evidence_dir / "summary.json")
    if summary is None:
        return _finish(record, "OUTPUT_INCOMPLETE", "SUMMARY_MISSING",
                       ["summary.json"])

    summary_mismatch = [
        name for name, expected in (
            ("model", model), ("context", ctx), ("role", role), ("seed", seed))
        if not _same_value(summary.get(name), expected)
    ]
    for key, column in (("binary_sha", "Binary_SHA256"),
                        ("config_sha", "Config_SHA256"),
                        ("elf_sha", "ELF_SHA256")):
        observed = summary.get(key)
        if observed not in (None, "") and not _sha_matches(observed, campaign.get(key)):
            summary_mismatch.append(key)
    if summary_mismatch:
        return _finish(record, "HASH_MISMATCH",
                       "SUMMARY_CAMPAIGN_DISAGREEMENT", summary_mismatch)

    # The run's own summary is authoritative for workload provenance; the
    # design matrix may still point at a stale tree or abstract basename.
    evidence_workload = summary.get("workload")
    if isinstance(evidence_workload, str) and evidence_workload.strip():
        record["Workload"] = Path(evidence_workload).name
        record["ELF"] = evidence_workload

    terminal = str(summary.get("terminal") or NOT_AVAILABLE)
    record["TerminalState"] = terminal
    record["TerminalReason"] = str(
        summary.get("terminal_reason") or NOT_AVAILABLE)
    observed_oracle = summary.get("oracle")
    record["OracleResult"] = (
        "PASS" if observed_oracle is True else
        "FAIL" if observed_oracle is False else
        "NO_CHECKSUM" if "oracle" in summary else NOT_AVAILABLE)

    trace_meta = summary.get("trace_completeness")
    declared_trace = NOT_AVAILABLE
    if isinstance(trace_meta, dict):
        declared_trace = str(
            trace_meta.get("trace_completeness") or NOT_AVAILABLE)
    record["TraceCompleteness"] = declared_trace

    # Attempt and applied counts stay separate fields for every record.
    applied = _as_int(summary.get("injection_applied_count"))
    if applied is None:
        applied = _as_int(summary.get("injection_count"))
    attempt = _as_int(summary.get("injection_attempt_count"))
    record["InjectionAttemptCount"] = (
        attempt if attempt is not None else UNKNOWN)
    record["InjectionAppliedCount"] = (
        applied if applied is not None else UNKNOWN)

    # 5. timeout -------------------------------------------------------------
    if (_as_bool(campaign.get("timed_out")) is True
            or _as_bool(summary.get("timed_out")) is True
            or _as_int(campaign.get("exit_code")) == 124
            or _as_int(summary.get("exit_code")) == 124):
        return _finish(record, "TIMEOUT", "EXTERNAL_TIMEOUT",
                       ["wall_clock_timeout"])

    # 6. required outputs ----------------------------------------------------
    partial_marker = _partial_watchdog(evidence_dir, model)
    missing = _missing_outputs(evidence_dir, model, role, summary, partial_marker)
    if missing:
        if "trace_v31.jsonl" in missing:
            record["TraceCompleteness"] = "MISSING"
        return _finish(record, "OUTPUT_INCOMPLETE", "MISSING_REQUIRED_OUTPUT",
                       missing)

    # Evidence is now complete (identity + frozen SHAs + all artifacts):
    # this is the only point where a record becomes FORMAL.
    record["EvidenceKind"] = FORMAL

    # 7. control runs --------------------------------------------------------
    if role == "control":
        result = classify_control_run(evidence_dir)
        record["ControlZeroProof"] = result["proof_class"]
        record["InjectorMounted"] = _yes_no_unknown(result["injector_mounted"])
        record["FaultEnabled"] = _yes_no_unknown(result["fault_enabled"])
        record["SuppressionReason"] = result["suppression_reason"]
        record["InjectionAttemptCount"] = result["injection_attempt_count"]
        record["InjectionAppliedCount"] = result["injection_applied_count"]
        record["InjectionCount"] = result["injection_applied_count"]
        hard_failure = _campaign_hard_failure(campaign.get("status"))
        if hard_failure is not None:
            return _finish(record, hard_failure,
                           f"CAMPAIGN_STATUS_{hard_failure}")
        control_status = result["status"]
        if control_status in ("FAIL", "CONTROL_PROOF_INCOMPLETE"):
            # A missing count is CONTROL_PROOF_INCOMPLETE -- never a zero PASS.
            return _finish(record, control_status, f"CONTROL_{control_status}")
        if observed_oracle is True:
            return _finish(record, "COMPLETED", "CONTROL_ORACLE_PASS")
        if observed_oracle is False:
            # The simulator ran fine; the *control* oracle failed.  That is an
            # oracle verdict, not a simulator run failure.
            return _finish(record, "ORACLE_FAIL", "CONTROL_ORACLE_FAIL")
        return _finish(record, "FAILED", "CONTROL_ORACLE_MISSING")

    # 8. fault runs ----------------------------------------------------------
    record["InjectionCount"] = (
        applied if applied is not None else UNKNOWN)

    qualified_status = NOT_AVAILABLE
    if model in QUALIFIED_MODELS:
        qualified = qualified_evidence(model, evidence_dir)
        qualified_status = qualified["status"]
        record["QualifiedStatus"] = qualified_status
        if record["TraceCompleteness"] == NOT_AVAILABLE:
            record["TraceCompleteness"] = qualified_status

    hard_failure = _campaign_hard_failure(campaign.get("status"))
    if hard_failure is not None:
        return _finish(record, hard_failure,
                       f"CAMPAIGN_STATUS_{hard_failure}")

    if terminal == "SDC":
        status, reason = "ORACLE_FAIL", "TERMINAL_SDC"
    elif terminal in MEASURED_TERMINALS:
        status, reason = "COMPLETED", f"TERMINAL_{terminal}"
    elif qualified_status == "QUALIFIED":
        # QUALIFIED evidence is reported as QUALIFIED, never upgraded to PASS.
        status, reason = "QUALIFIED", "QUALIFIED_EVIDENCE"
    else:
        status, reason = "FAILED", f"UNRECOGNIZED_TERMINAL_{terminal}"

    if qualified_status == "TRACE_INCOMPLETE":
        if terminal in WATCHDOG_TERMINALS:
            # Documented measured terminal for a qualified model: the model
            # watchdog cut the trace, so the completeness stays incomplete.
            status, reason = "TRACE_INCOMPLETE", "TERMINAL_WATCHDOG_TRACE_CUT"
        else:
            status, reason = "FAILED", "QUALIFIED_TRACE_INCOMPLETE"

    return _finish(record, status, reason)


# ---------------------------------------------------------------------------
# artifact writers
# ---------------------------------------------------------------------------
def _write_csv(path: Path, rows: list[dict], fieldnames) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames),
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _pair_rows(faults: list[dict], controls: list[dict]) -> list[dict]:
    rows = []
    for fault, control in zip(faults, controls):
        rows.append({
            "ModelID": fault["ModelID"],
            "ContextID": fault["ContextID"],
            "SampleRunID": fault["SampleRunID"],
            "Seed": fault["Seed"],
            "FaultStatus": fault["Status"],
            "ControlStatus": control["Status"],
            "FaultEvidenceKind": fault["EvidenceKind"],
            "ControlEvidenceKind": control["EvidenceKind"],
            "FaultEvidence": fault["Evidence"],
            "ControlEvidence": control["Evidence"],
            "FaultTerminal": fault["TerminalState"],
            "FaultOracle": fault["OracleResult"],
            "ControlOracle": control["OracleResult"],
            "FaultInjectionCount": fault["InjectionCount"],
            "ControlInjectionCount": control["InjectionCount"],
            "ControlZeroProof": control["ControlZeroProof"],
            "PairMatched": "YES" if (
                _same_value(fault["Seed"], control["Seed"])
                and fault["SampleRunID"] == control["SampleRunID"]) else "NO",
        })
    return rows


def _control_proof_rows(controls: list[dict]) -> list[dict]:
    rows = []
    for control in controls:
        rows.append({
            "ModelID": control["ModelID"],
            "ContextID": control["ContextID"],
            "SampleRunID": control["SampleRunID"],
            "Seed": control["Seed"],
            "ControlStatus": control["Status"],
            "ControlZeroProof": control["ControlZeroProof"],
            "EvidenceKind": control["EvidenceKind"],
            "InjectorMounted": control["InjectorMounted"],
            "FaultEnabled": control["FaultEnabled"],
            "SuppressionReason": control["SuppressionReason"],
            "InjectionAttemptCount": control["InjectionAttemptCount"],
            "InjectionAppliedCount": control["InjectionAppliedCount"],
            "InjectionCount": control["InjectionCount"],
            "ControlOracle": control["OracleResult"],
            "Evidence": control["Evidence"],
        })
    return rows


def write_core_artifacts(out: Path, records: list[dict],
                         faults: list[dict], controls: list[dict]) -> None:
    _write_csv(out / "LSU_120Run_Campaign_Manifest.csv", records,
               MANIFEST_COLS)
    _write_csv(out / "LSU_60Fault_60Control_Pair_Map.csv",
               _pair_rows(faults, controls),
               ("ModelID", "ContextID", "SampleRunID", "Seed",
                "FaultStatus", "ControlStatus", "FaultEvidenceKind",
                "ControlEvidenceKind", "FaultEvidence", "ControlEvidence",
                "FaultTerminal", "FaultOracle", "ControlOracle",
                "FaultInjectionCount", "ControlInjectionCount",
                "ControlZeroProof", "PairMatched"))
    _write_csv(out / "LSU_Control_Zero_Proof_Final.csv",
               _control_proof_rows(controls),
               ("ModelID", "ContextID", "SampleRunID", "Seed",
                "ControlStatus", "ControlZeroProof", "EvidenceKind",
                "InjectorMounted", "FaultEnabled", "SuppressionReason",
                "InjectionAttemptCount", "InjectionAppliedCount",
                "InjectionCount", "ControlOracle", "Evidence"))
    for record in records:
        run_name = Path(record["Evidence"]).name
        path = out / "per_run" / run_name / "campaign_manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n", encoding="utf-8")


def _add_sheet(workbook, title, header, rows):
    from openpyxl.styles import Alignment, Font

    sheet = workbook.create_sheet(title)
    sheet.append(list(header))
    for row in rows:
        sheet.append(list(row))
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "A2"
    return sheet


def write_full_exports(out: Path, records: list[dict], faults: list[dict],
                       controls: list[dict], *, runs: Path, campaign_id: str,
                       expected_binary_sha: str,
                       expected_config_sha: str) -> None:
    """XLSX config workbook + readiness CSV, built from isolated records only."""
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)
    formal = sum(1 for row in records if row["EvidenceKind"] == FORMAL)
    _add_sheet(workbook, "README", ("Item", "Value"), [
        ("Workbook", "LSU_Formal_Experiment_Config_Final.xlsx"),
        ("Purpose", "Formal campaign configuration (one row per fault/control)"),
        ("CampaignRoot", str(runs)),
        ("CampaignID", campaign_id),
        ("EvidenceSource", "campaign root only (no historical audit read)"),
        ("Final binary SHA256", expected_binary_sha),
        ("Final config SHA256", expected_config_sha),
        ("Scheduled tasks", len(records)),
        ("Formal tasks", formal),
    ])
    _add_sheet(workbook, "Fault_Config", MANIFEST_COLS,
               ([row[c] for c in MANIFEST_COLS] for row in faults))
    _add_sheet(workbook, "Control_Config", MANIFEST_COLS,
               ([row[c] for c in MANIFEST_COLS] for row in controls))
    census = [["ModelID", "ContextID", "SampleRunID", "Seed", "ROI_Start",
               "ROI_End", "ROI_N", "Percentile", "EligibleEventOrdinal",
               "DynInstSeq", "PC", "ExpectedTerminal", "Status"]]
    for row in faults:
        census.append([row["ModelID"], row["ContextID"], row["SampleRunID"],
                       row["Seed"], row["ROI_Start"], row["ROI_End"],
                       row["ROI_N"], row["Percentile"],
                       row["EligibleEventOrdinal"], row["DynInstSeq"],
                       row["PC"], row["ExpectedTerminal"], row["Status"]])
    _add_sheet(workbook, "ROI_Census", census[0], census[1:])
    validation = [["Check", "Result", "Detail"]]
    validation.append(["Scheduled tasks", len(records), "design rows x roles"])
    validation.append(["Formal tasks", formal, "EvidenceKind=FORMAL"])
    validation.append(["Unique SampleRunID",
                       len({row["SampleRunID"] for row in faults}),
                       "expected 60"])
    validation.append(["Fault/control same seed",
                       all(_same_value(f["Seed"], c["Seed"])
                           for f, c in zip(faults, controls)), "per pair"])
    validation.append(["Binary SHA consistent",
                       all(row["Binary_SHA256"] == expected_binary_sha
                           for row in records if row["EvidenceKind"] == FORMAL),
                       expected_binary_sha])
    validation.append(["Config SHA consistent",
                       all(row["Config_SHA256"] == expected_config_sha
                           for row in records if row["EvidenceKind"] == FORMAL),
                       expected_config_sha])
    _add_sheet(workbook, "Config_Validation", validation[0], validation[1:])
    out.mkdir(parents=True, exist_ok=True)
    workbook.save(out / "LSU_Formal_Experiment_Config_Final.xlsx")

    readiness = []
    for fault, control in zip(faults, controls):
        problems = []
        if fault["EvidenceKind"] != FORMAL or \
                fault["Status"] not in FAULT_SUCCESS_STATUSES:
            problems.append(f"fault:{fault['Status']}")
        if control["EvidenceKind"] != FORMAL or \
                control["Status"] not in CONTROL_SUCCESS_STATUSES:
            problems.append(f"control:{control['Status']}")
        readiness.append({
            "ModelID": fault["ModelID"],
            "ContextID": fault["ContextID"],
            "SampleRunID": fault["SampleRunID"],
            "Seed": fault["Seed"],
            "FaultStatus": fault["Status"],
            "ControlStatus": control["Status"],
            "EvidenceKind": (FORMAL if fault["EvidenceKind"] == control["EvidenceKind"] == FORMAL
                             else NON_FORMAL),
            "TerminalState": fault["TerminalState"],
            "OracleResult": fault["OracleResult"],
            "ControlZeroProof": control["ControlZeroProof"],
            "QualifiedStatus": fault["QualifiedStatus"],
            "ReadyGate": "READY" if not problems else ";".join(problems),
        })
    _write_csv(out / "LSU_60Context_Final_Readiness.csv", readiness,
               ("ModelID", "ContextID", "SampleRunID", "Seed", "FaultStatus",
                "ControlStatus", "EvidenceKind", "TerminalState",
                "OracleResult", "ControlZeroProof", "QualifiedStatus",
                "ReadyGate"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect the LSU v3.3.3 formal campaign manifest from the "
                    "campaign root only.")
    parser.add_argument("--runs", required=True,
                        help="campaign root holding <MODEL>-<CTX>-<role>/ dirs")
    parser.add_argument("--campaign-id", required=True,
                        help="expected campaign_id in every campaign.json")
    parser.add_argument("--design-matrix", required=True,
                        help="frozen design matrix CSV (identity only)")
    parser.add_argument("--design-mapping", required=True,
                        help="ROI/identity mapping CSV (identity only)")
    parser.add_argument("--out", default="audit_launch_fix_v333/artifacts",
                        help="artifact output directory")
    parser.add_argument("--manifest-only", action="store_true",
                        help="write the manifest/pair/proof/per-run artifacts "
                             "without the XLSX/readiness export")
    parser.add_argument("--expected-binary-sha", default=DEFAULT_BINARY_SHA,
                        help="expected gem5 binary SHA256")
    parser.add_argument("--expected-config-sha", default=DEFAULT_CONFIG_SHA,
                        help="expected workload config SHA256")
    args = parser.parse_args(argv)

    runs = Path(args.runs).resolve()
    if not runs.is_dir():
        print(f"error: --runs is not a directory: {runs}", file=sys.stderr)
        return 2

    matrix_rows = _load_csv(Path(args.design_matrix))
    if not matrix_rows:
        print(f"error: --design-matrix is empty/unreadable: "
              f"{args.design_matrix}", file=sys.stderr)
        return 2
    mapping_rows = _load_csv(Path(args.design_mapping))
    mapping_idx = {(str(row.get("ModelID", "")).strip(),
                    str(row.get("ContextID", "")).strip()): row
                   for row in mapping_rows}

    campaign_identity = _read_json(runs / "campaign_identity.json")
    if campaign_identity is not None:
        identity_cid = campaign_identity.get("campaign_id")
        if identity_cid not in (None, "") and \
                not _same_value(identity_cid, args.campaign_id):
            campaign_identity = None

    records: list[dict] = []
    for matrix_row in matrix_rows:
        model = str(matrix_row.get("FaultModelID") or "").strip()
        ctx = _ctx_of(matrix_row.get("SampleRunID", ""))
        mapping_row = mapping_idx.get((model, ctx))
        for role in ("fault", "control"):
            records.append(collect_task(
                runs, args.campaign_id, matrix_row, mapping_row, role,
                args.expected_binary_sha, args.expected_config_sha,
                campaign_identity))

    faults = [record for record in records if record["Role"] == "fault"]
    controls = [record for record in records if record["Role"] == "control"]
    out = Path(args.out)
    write_core_artifacts(out, records, faults, controls)
    if not args.manifest_only:
        write_full_exports(
            out, records, faults, controls, runs=runs,
            campaign_id=args.campaign_id,
            expected_binary_sha=args.expected_binary_sha,
            expected_config_sha=args.expected_config_sha)

    formal = sum(1 for record in records if record["EvidenceKind"] == FORMAL)
    status_tally: dict[str, int] = {}
    for record in records:
        status_tally[record["Status"]] = \
            status_tally.get(record["Status"], 0) + 1
    print(f"collected {len(records)} tasks from {runs} "
          f"(campaign_id={args.campaign_id})")
    print(f"formal={formal} non_formal={len(records) - formal}")
    print("statuses " + json.dumps(dict(sorted(status_tally.items()))))
    print("wrote artifacts to", out)

    def task_ok(record: dict) -> bool:
        allowed = (CONTROL_SUCCESS_STATUSES if record.get("Role") == "control"
                   else FAULT_SUCCESS_STATUSES)
        return record["EvidenceKind"] == FORMAL and record["Status"] in allowed

    ok = all(task_ok(record) for record in records)
    if not ok:
        for record in records:
            if not task_ok(record):
                print(f"  {record['EvidenceKind']}: {record['Status']}: "
                      f"{record['ModelID']}-{record['ContextID']}-"
                      f"{record['Role']} ({record['Reason']}; "
                      f"missing={record['MissingEvidence']})",
                      file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
