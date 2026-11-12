#!/usr/bin/env python3
"""LSU v3.3.3 control zero-injection proof classifier.

One control run is a *proof* only when the executed command shows the injector
was absent, or mounted but provably disabled/suppressed, AND the per-run
evidence shows zero injection was applied.  This module reads nothing outside
the given run directory and never fabricates a count:

* a missing summary / applied count / executed command yields
  ``CONTROL_PROOF_INCOMPLETE`` -- never a default ``0`` and never ``PASS``;
* a mounted control whose trace is missing cannot be corroborated, so a zero is
  not upgraded to ``PASS`` (an *absent* injector needs no injection trace: the
  command itself is the proof and the summary count is authoritative);
* any observed ``injection_applied_count > 0`` is ``FAIL``.

Interface (see audit_launch_fix_v333/README_INTERFACES.md):

    classify_control_run(run_dir: Path) -> dict

Keys: ``injector_mounted, fault_enabled, suppression_reason,
injection_attempt_count, injection_applied_count, proof_class, status,
evidence``.

CLI::

    python3 tools/lsu_v333_control_proof.py --runs audit_v3_3_3/runs \
        --out audit_launch_fix_v333/artifacts/LSU_Control_Zero_Proof_Final.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

# Injector mount flags for the LSU matrix.  Authoritative list mirrors
# docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py:MOUNT_FLAGS.
MOUNT_FLAGS = (
    "--chaos_lsqfwd",
    "--chaos_addrpath",
    "--chaos_l1dfwd",
    "--chaos_lq04",
    "--chaos_md04",
)

# Token hints that denote an *explicit* injection suppression rule.  The
# current 120-run pre-formal package has none (0 suppressed); the path exists
# so a formal run that records one is classified, not silently downgraded.
SUPPRESS_FLAG_HINTS = (
    "suppress",
    "disable_injection",
    "injection_off",
    "no_injection",
    "faults_off",
)

UNKNOWN = "UNKNOWN"

# Strict tri-state ControlInjected classifier.  Used by ``--emit-control-audit``
# so a missing/illegal ``InjectionCount`` can never become a zero-injection
# PASS (the former inline ``in ("0", "")`` check in 04_final_reports.sh did
# exactly that).
CONTROL_INJECTED_NO = "NO"
CONTROL_INJECTED_YES = "YES"
CONTROL_INJECTED_UNKNOWN = "UNKNOWN"
CONTROL_INJECTED_INVALID = "INVALID"

_INTEGER_TEXT = re.compile(r"^[+-]?\d+$")


def classify_injection_count(value: object) -> tuple[str, str]:
    """Classify an ``InjectionCount`` value as ``(state, reason)``.

    Rules (order matters -- missing is checked *before* empty):

    * ``None`` / missing key            -> ``("UNKNOWN", "MISSING")``
    * ``""`` or whitespace              -> ``("UNKNOWN", "EMPTY")``
    * only ``^[+-]?\\d+$`` is accepted
    * negative                          -> ``("INVALID", "NEGATIVE")``
    * zero                              -> ``("NO", "ZERO")``
    * positive                          -> ``("YES", "POSITIVE")``
    * anything else (``"1.0"``, ``"nan"``, ``"abc"``, ``"0x0"``, lists,
      bools, floats)                    -> ``("UNKNOWN", "UNPARSEABLE")``

    A missing value is never defaulted to ``0``.
    """
    if value is None:
        return CONTROL_INJECTED_UNKNOWN, "MISSING"
    if isinstance(value, bool):
        # bool is an int subclass but is not an integer count.
        return CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return CONTROL_INJECTED_UNKNOWN, "EMPTY"
    else:
        return CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"

    if not _INTEGER_TEXT.fullmatch(text):
        return CONTROL_INJECTED_UNKNOWN, "UNPARSEABLE"
    number = int(text)
    if number < 0:
        return CONTROL_INJECTED_INVALID, "NEGATIVE"
    if number == 0:
        return CONTROL_INJECTED_NO, "ZERO"
    return CONTROL_INJECTED_YES, "POSITIVE"


PROOF_INJECTOR_ABSENT = "INJECTOR_ABSENT"
PROOF_MOUNTED_BUT_DISABLED = "MOUNTED_BUT_DISABLED"
PROOF_MOUNTED_BUT_SUPPRESSED = "MOUNTED_BUT_SUPPRESSED"
PROOF_INCOMPLETE = "CONTROL_PROOF_INCOMPLETE"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_INCOMPLETE = "CONTROL_PROOF_INCOMPLETE"

_PROOF_CLASSES = (
    PROOF_INJECTOR_ABSENT,
    PROOF_MOUNTED_BUT_DISABLED,
    PROOF_MOUNTED_BUT_SUPPRESSED,
    PROOF_INCOMPLETE,
)

# Log counters emitted by the injectors / trigger harness.  Only the explicit
# ``attempted=`` counter is treated as an attempt (A01/A03/SQ01 instrument it);
# ``fired=`` in the per-model STATUS lines is a site counter, not an attempt
# counter, so it is deliberately not promoted into the attempt field.
_RE_APPLIED = (
    re.compile(r"faults_injected\s*[:=]\s*(\d+)"),
    re.compile(r"(?<![A-Za-z0-9_])injected=(\d+)"),
)
_RE_ATTEMPT = (
    re.compile(r"(?<![A-Za-z0-9_])attempted=(\d+)"),
)

# Trace pre-filters must tolerate JSON whitespace (real gem5 JSONL is compact,
# but tests/hand-written traces are not): optional spaces after the colon.
_RE_TRACE_SUMMARY = re.compile(r'"record_type"\s*:\s*"summary"')
_RE_TRACE_INJECTION = re.compile(r'"event_type"\s*:\s*"injection"')


# --------------------------------------------------------------------------
# small IO helpers
# --------------------------------------------------------------------------
def _load_json(path: Path, evidence: list[str]) -> dict | None:
    if not path.is_file():
        evidence.append(f"MISSING {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        evidence.append(f"UNREADABLE {path}: {exc}")
        return None
    if not isinstance(data, dict):
        evidence.append(f"UNREADABLE {path}: not a JSON object")
        return None
    return data


def _split_command_text(text: str) -> list[str]:
    """Split an executed-command file/shell line into argv tokens."""
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        # Unbalanced quotes in a hand-edited command.txt: fall back to spaces.
        return text.split()


def _flag_value(tokens: list[str], flag: str) -> str | None:
    """Return the token following ``flag`` (supports ``--flag=value``)."""
    for i, tok in enumerate(tokens):
        if tok == flag:
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                return tokens[i + 1]
            return None
        if tok.startswith(flag + "="):
            return tok.split("=", 1)[1]
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


# --------------------------------------------------------------------------
# executed-command parsing
# --------------------------------------------------------------------------
def _read_executed_command(
    run_dir: Path, evidence: list[str]
) -> tuple[list[str] | None, str | None, str | None]:
    """Return (tokens, source_name, note).

    ``command.txt`` is the executed command.  Only if it is absent do we fall
    back to other records that capture the *executed* argv (manifest command,
    pilot_meta command, summary ``fault_command``).  ``summary["cmd"]`` is the
    run_pilot driver argv and never contains the injector mount -- it must
    never be used here.
    """
    cmd_txt = run_dir / "command.txt"
    if cmd_txt.is_file():
        try:
            tokens = _split_command_text(cmd_txt.read_text(encoding="utf-8"))
        except OSError as exc:
            return None, None, f"command.txt unreadable: {exc}"
        if not tokens:
            return None, None, "command.txt is empty"
        evidence.append(f"{cmd_txt}: executed command ({len(tokens)} tokens)")
        return tokens, "command.txt", None

    for name in ("manifest.json", "pilot_meta.json"):
        path = run_dir / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cmd = data.get("command") if isinstance(data, dict) else None
        if isinstance(cmd, list) and cmd:
            evidence.append(
                f"{path}: executed command fallback ({len(cmd)} tokens)"
            )
            return [str(t) for t in cmd], name, None

    summary_path = run_dir / "summary.json"
    if summary_path.is_file():
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            fc = data.get("fault_command")
            if isinstance(fc, str) and fc.strip():
                tokens = _split_command_text(fc)
                evidence.append(
                    f"{summary_path}: fault_command fallback ({len(tokens)} tokens)"
                )
                return tokens, "summary.json:fault_command", None

    evidence.append("MISSING executed command evidence (command.txt et al.)")
    return None, None, "executed command evidence missing"


def _suppression_tokens(tokens: list[str]) -> list[str]:
    out = []
    for tok in tokens:
        if not tok.startswith("--"):
            continue
        low = tok.lower()
        if any(hint in low for hint in SUPPRESS_FLAG_HINTS):
            out.append(tok)
    return out


# --------------------------------------------------------------------------
# count evidence
# --------------------------------------------------------------------------
def _log_files(run_dir: Path) -> list[Path]:
    if not run_dir.is_dir():
        return []
    return sorted(p for p in run_dir.glob("*.log") if p.is_file())


def _scan_logs(
    run_dir: Path, evidence: list[str]
) -> tuple[list[int], list[int], list[str]]:
    """Return (applied_candidates, attempt_candidates, evidence lines)."""
    applied: list[int] = []
    attempts: list[int] = []
    evidence_lines: list[str] = []
    for path in _log_files(run_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for regex in _RE_APPLIED:
            for match in regex.finditer(text):
                # The 3-group CHAOS_*_STATUS pattern stores injected in group 2.
                value = match.group(2) if regex.groups == 2 else match.group(1)
                if value is not None:
                    applied.append(int(value))
                    evidence_lines.append(
                        f"{path}: '{match.group(0).strip()}'"
                    )
        for regex in _RE_ATTEMPT:
            for match in regex.finditer(text):
                attempts.append(int(match.group(1)))
                evidence_lines.append(f"{path}: '{match.group(0).strip()}'")
    if evidence_lines:
        evidence.extend(evidence_lines)
    else:
        evidence.append("no injector counter line in *.log")
    return applied, attempts, evidence_lines


def _scan_trace(
    run_dir: Path, evidence: list[str]
) -> tuple[bool, int | None, int | None]:
    """Return (trace_present, injection_event_count, summary_injections)."""
    path = run_dir / "trace_v31.jsonl"
    if not path.is_file():
        evidence.append(f"MISSING {path}")
        return False, None, None

    injection_events: int | None = None
    summary_injections: int | None = None
    usable_record = False
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                if not (_RE_TRACE_SUMMARY.search(line)
                        or _RE_TRACE_INJECTION.search(line)):
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rtype = rec.get("record_type")
                if rtype == "event" and rec.get("event_type") == "injection":
                    usable_record = True
                    injection_events = (injection_events or 0) + 1
                elif rtype == "summary":
                    usable_record = True
                    counts = rec.get("counts")
                    if isinstance(counts, dict):
                        value = _as_int(counts.get("injections"))
                        if value is not None:
                            summary_injections = value
    except OSError as exc:
        evidence.append(f"UNREADABLE {path}: {exc}")
        return False, None, None

    if not usable_record:
        # A present-but-empty trace is NOT evidence of zero injections; it
        # cannot corroborate a count (each synthetic missing-count fixture
        # lands here).  Do not turn it into a zero.
        evidence.append(f"{path}: present but no injection/summary record (no zero proof)")
        return False, None, None

    evidence.append(
        f"{path}: injection events={injection_events if injection_events is not None else 0}; "
        f"summary counts.injections={summary_injections}"
    )
    return True, injection_events if injection_events is not None else 0, \
        summary_injections


def _resolve_counts(
    run_dir: Path,
    summary: dict | None,
    pilot_meta: dict | None,
    evidence: list[str],
) -> tuple[int | str, int | str, bool, int | None]:
    """Resolve (applied_count, attempt_count, trace_present, trace_injections).

    Authority for the applied count: summary.json ``injection_count`` is the
    primary value; pilot_meta, trace and model-log counters corroborate it.
    Any positive candidate wins (a real injection cannot be averaged away).
    """
    applied_candidates: list[tuple[str, int]] = []
    attempt_candidates: list[tuple[str, int]] = []

    if summary is not None:
        for key in ("injection_count", "injection_applied_count"):
            value = _as_int(summary.get(key))
            if value is not None:
                applied_candidates.append((f"summary.json:{key}", value))
        events = summary.get("injection_events")
        if isinstance(events, list):
            applied_candidates.append(("summary.json:injection_events", len(events)))
        for key in ("injection_attempt_count", "attempt_count"):
            value = _as_int(summary.get(key))
            if value is not None:
                attempt_candidates.append((f"summary.json:{key}", value))

    if pilot_meta is not None:
        for key in ("injection_count", "injection_applied_count"):
            value = _as_int(pilot_meta.get(key))
            if value is not None:
                applied_candidates.append((f"pilot_meta.json:{key}", value))
        injection = pilot_meta.get("injection")
        if isinstance(injection, dict):
            value = _as_int(injection.get("injected"))
            if value is not None:
                applied_candidates.append(
                    ("pilot_meta.json:injection.injected", value)
                )
            events = injection.get("events")
            if isinstance(events, list):
                applied_candidates.append(
                    ("pilot_meta.json:injection.events", len(events))
                )
        for key in ("injection_attempt_count", "attempt_count"):
            value = _as_int(pilot_meta.get(key))
            if value is not None:
                attempt_candidates.append((f"pilot_meta.json:{key}", value))

    trace_present, trace_injections, summary_injections = _scan_trace(
        run_dir, evidence
    )
    if trace_injections is not None:
        applied_candidates.append(("trace_v31.jsonl:events", trace_injections))
    if summary_injections is not None:
        applied_candidates.append(
            ("trace_v31.jsonl:counts.injections", summary_injections)
        )

    log_applied, log_attempts, _ = _scan_logs(run_dir, evidence)
    applied_candidates.extend(
        (f"model-log[{i}]", v) for i, v in enumerate(log_applied)
    )
    attempt_candidates.extend(
        (f"model-log[{i}]", v) for i, v in enumerate(log_attempts)
    )

    if applied_candidates:
        applied: int | str = max(v for _, v in applied_candidates)
        evidence.append(
            "applied candidates: "
            + ", ".join(f"{src}={v}" for src, v in applied_candidates)
        )
    else:
        applied = UNKNOWN
        evidence.append("injection_applied_count: no per-run count available -> UNKNOWN")

    if attempt_candidates:
        attempt: int | str = max(v for _, v in attempt_candidates)
        evidence.append(
            "attempt candidates: "
            + ", ".join(f"{src}={v}" for src, v in attempt_candidates)
        )
    else:
        attempt = UNKNOWN
        evidence.append(
            "injection_attempt_count: not instrumented in this run -> UNKNOWN"
        )

    return applied, attempt, trace_present, trace_injections


# --------------------------------------------------------------------------
# classifier
# --------------------------------------------------------------------------
def classify_control_run(run_dir: Path) -> dict:
    """Classify one control run's zero-injection proof.

    Returns exactly the interface keys documented in README_INTERFACES.md.
    Never defaults a missing count to 0 and never returns PASS without
    corroborating per-run evidence.
    """
    run_dir = Path(run_dir)
    evidence: list[str] = []

    summary = _load_json(run_dir / "summary.json", evidence)
    pilot_meta = _load_json(run_dir / "pilot_meta.json", evidence)
    mount_evidence = {}
    if isinstance(summary, dict) and isinstance(summary.get("mount_evidence"), dict):
        mount_evidence = summary["mount_evidence"]
    injector_meta = {}
    if isinstance(pilot_meta, dict) and isinstance(pilot_meta.get("injector"), dict):
        injector_meta = pilot_meta["injector"]

    tokens, command_source, command_note = _read_executed_command(run_dir, evidence)

    # ---- mount / probability / suppression ---------------------------------
    incomplete_reasons: list[str] = []
    if tokens is None:
        injector_mounted: bool | None = None
        mounts: list[str] = []
        command_probability: float | None = None
        command_md04: float | None = None
        suppression_flags: list[str] = []
        incomplete_reasons.append(command_note or "executed command missing")
    else:
        mounts = [flag for flag in MOUNT_FLAGS if flag in tokens]
        injector_mounted = bool(mounts)
        evidence.append(
            f"{command_source}: mount flags={mounts or '[]'}"
        )
        command_probability = _as_float(_flag_value(tokens, "--probability"))
        command_md04 = _as_float(_flag_value(tokens, "--md04_probability"))
        suppression_flags = _suppression_tokens(tokens)

    # Corroborating gate values recorded by the runner.
    meta_probability = _as_float(injector_meta.get("probability"))
    meta_md04 = _as_float(injector_meta.get("md04_probability"))
    sum_probability = _as_float(mount_evidence.get("probability"))
    sum_md04 = _as_float(mount_evidence.get("md04_probability"))
    recorded_suppression = list(injector_meta.get("suppression_flags") or [])
    recorded_suppression += list(mount_evidence.get("suppression_flags") or [])
    if injector_meta.get("zero_injection_proof") == PROOF_MOUNTED_BUT_SUPPRESSED:
        recorded_suppression.append("pilot_meta.json:injector.zero_injection_proof")

    probability = command_probability
    if probability is None:
        probability = meta_probability
        if probability is not None:
            evidence.append(f"pilot_meta.json: injector.probability={probability}")
    if probability is None:
        probability = sum_probability
        if probability is not None:
            evidence.append(f"summary.json: mount_evidence.probability={probability}")

    md04_probability = command_md04
    if md04_probability is None:
        md04_probability = meta_md04
    if md04_probability is None:
        md04_probability = sum_md04

    if probability is not None:
        evidence.append(f"probability={probability}")
    if md04_probability is not None:
        evidence.append(f"md04_probability={md04_probability}")

    # Conflicting gate records are an evidence-integrity failure, not a pass.
    if command_probability is not None:
        for label, value in (
            ("pilot_meta.injector.probability", meta_probability),
            ("summary.mount_evidence.probability", sum_probability),
        ):
            if value is not None and abs(value - command_probability) > 1e-12:
                incomplete_reasons.append(
                    f"probability conflict: command={command_probability} "
                    f"vs {label}={value}"
                )
                evidence.append(incomplete_reasons[-1])
    if command_md04 is not None:
        for label, value in (
            ("pilot_meta.injector.md04_probability", meta_md04),
            ("summary.mount_evidence.md04_probability", sum_md04),
        ):
            if value is not None and abs(value - command_md04) > 1e-12:
                incomplete_reasons.append(
                    f"md04_probability conflict: command={command_md04} "
                    f"vs {label}={value}"
                )
                evidence.append(incomplete_reasons[-1])

    if recorded_suppression:
        evidence.append(
            "recorded suppression: " + ",".join(str(s) for s in recorded_suppression)
        )

    # ---- proof class --------------------------------------------------------
    disabled_reason: str | None = None
    if probability is not None and probability == 0.0:
        disabled_reason = "probability=0.0"
    if md04_probability is not None and md04_probability == 0.0:
        disabled_reason = (
            "md04_probability=0.0"
            if disabled_reason is None
            else disabled_reason + "; md04_probability=0.0"
        )

    if tokens is None:
        proof_class = PROOF_INCOMPLETE
        suppression_reason = "executed command evidence missing"
    elif not mounts:
        proof_class = PROOF_INJECTOR_ABSENT
        suppression_reason = "injector flag absent from executed command"
    elif disabled_reason is not None:
        proof_class = PROOF_MOUNTED_BUT_DISABLED
        suppression_reason = disabled_reason
    elif suppression_flags or recorded_suppression:
        proof_class = PROOF_MOUNTED_BUT_SUPPRESSED
        flags = suppression_flags + [str(s) for s in recorded_suppression]
        suppression_reason = "explicit suppression: " + ",".join(flags)
    else:
        proof_class = PROOF_INCOMPLETE
        if probability is None:
            suppression_reason = "mounted injector with no recorded gate probability"
        else:
            suppression_reason = (
                f"mounted injector with probability={probability} is active"
            )
        incomplete_reasons.append(suppression_reason)
        evidence.append(suppression_reason)

    if proof_class in (PROOF_INJECTOR_ABSENT, PROOF_MOUNTED_BUT_DISABLED,
                       PROOF_MOUNTED_BUT_SUPPRESSED):
        fault_enabled: bool | None = False
    elif mounts and probability is not None and probability > 0.0 and \
            (md04_probability is None or md04_probability > 0.0):
        fault_enabled = True
    else:
        fault_enabled = None

    # ---- counts -------------------------------------------------------------
    applied_count, attempt_count, trace_present, trace_injections = _resolve_counts(
        run_dir, summary, pilot_meta, evidence
    )

    if summary is None:
        incomplete_reasons.append("summary.json missing/unreadable")
    if applied_count == UNKNOWN:
        incomplete_reasons.append("injection_applied_count unavailable")
    if injector_mounted and not trace_present:
        incomplete_reasons.append(
            "trace_v31.jsonl missing: mounted-control zero cannot be corroborated"
        )
    if trace_present and isinstance(trace_injections, int) and trace_injections > 0:
        # Explicit trace evidence of a real injection; recorded as FAIL below.
        evidence.append(f"trace shows {trace_injections} injection event(s)")

    # ---- status -------------------------------------------------------------
    if applied_count != UNKNOWN and int(applied_count) > 0:
        status = STATUS_FAIL
    elif incomplete_reasons:
        status = STATUS_INCOMPLETE
        for reason in incomplete_reasons:
            evidence.append(f"INCOMPLETE: {reason}")
    else:
        status = STATUS_PASS

    # Keep proof_class and status coherent: a proof-class failure is an
    # incomplete proof unless a real injection was observed.
    if proof_class == PROOF_INCOMPLETE and status == STATUS_PASS:
        status = STATUS_INCOMPLETE

    assert proof_class in _PROOF_CLASSES, proof_class
    return {
        "injector_mounted": injector_mounted,
        "fault_enabled": fault_enabled,
        "suppression_reason": suppression_reason,
        "injection_attempt_count": attempt_count,
        "injection_applied_count": applied_count,
        "proof_class": proof_class,
        "status": status,
        "evidence": evidence,
    }


# --------------------------------------------------------------------------
# CLI: 60-row CSV (ModelID-ContextID-control)
# --------------------------------------------------------------------------
CSV_COLUMNS = (
    "SampleRunID",
    "ModelID",
    "ContextID",
    "Role",
    "EvidenceKind",
    "InjectorMounted",
    "FaultEnabled",
    "SuppressionReason",
    "InjectionAttemptCount",
    "InjectionAppliedCount",
    "InjectionCount",
    "ControlZeroProof",
    "ControlProofStatus",
    "MountFlags",
    "Probability",
    "Md04Probability",
    "OracleResult",
    "ExitCode",
    "TraceInjectionEvents",
    "Evidence",
)

_RUN_DIR_RE = re.compile(r"^(?P<model>[A-Z0-9]+)-(?P<ctx>R\d{2})-control$")


def _duration_tokens(tokens: list[str] | None) -> tuple[list[str], float | None, float | None]:
    """Re-derive the mount facts for the CSV identity columns."""
    if not tokens:
        return [], None, None
    mounts = [flag for flag in MOUNT_FLAGS if flag in tokens]
    return (
        mounts,
        _as_float(_flag_value(tokens, "--probability")),
        _as_float(_flag_value(tokens, "--md04_probability")),
    )


def _oracle_exit(run_dir: Path) -> tuple[str, Any]:
    summary = None
    path = run_dir / "summary.json"
    if path.is_file():
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            summary = None
    if not isinstance(summary, dict):
        return "n/a", "n/a"
    oracle = summary.get("oracle")
    oracle_result = "PASS" if oracle is True else "FAIL" if oracle is False else "n/a"
    exit_code = summary.get("exit_code", "n/a")
    return oracle_result, exit_code


def _fmt_bool(value: Any) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return UNKNOWN


def build_rows(runs_root: Path, evidence_kind: str = "PRE_FORMAL"):
    runs_root = Path(runs_root)
    rows = []
    for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        match = _RUN_DIR_RE.match(run_dir.name)
        if not match:
            continue
        result = classify_control_run(run_dir)
        tokens, _, _ = _read_executed_command(run_dir, [])
        mounts, probability, md04_probability = _duration_tokens(tokens)
        oracle_result, exit_code = _oracle_exit(run_dir)
        rows.append(
            {
                "SampleRunID": run_dir.name,
                "ModelID": match.group("model"),
                "ContextID": match.group("ctx"),
                "Role": "control",
                "EvidenceKind": evidence_kind,
                "InjectorMounted": _fmt_bool(result["injector_mounted"]),
                "FaultEnabled": _fmt_bool(result["fault_enabled"]),
                "SuppressionReason": result["suppression_reason"],
                "InjectionAttemptCount": result["injection_attempt_count"],
                "InjectionAppliedCount": result["injection_applied_count"],
                "InjectionCount": result["injection_applied_count"],
                "ControlZeroProof": result["proof_class"],
                "ControlProofStatus": result["status"],
                "MountFlags": " ".join(mounts),
                "Probability": "" if probability is None else probability,
                "Md04Probability": "" if md04_probability is None else md04_probability,
                "OracleResult": oracle_result,
                "ExitCode": exit_code,
                "TraceInjectionEvents": _trace_event_count(run_dir),
                "Evidence": " | ".join(result["evidence"]),
            }
        )
    return rows


def _trace_event_count(run_dir: Path) -> Any:
    _, injection_events, summary_injections = _scan_trace(run_dir, [])
    if injection_events is None and summary_injections is None:
        return "n/a"
    return injection_events if injection_events is not None else summary_injections


def write_csv(path: Path, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------
# CLI: strict tri-state control-audit CSV (ModelID-ContextID-control)
# --------------------------------------------------------------------------
CONTROL_AUDIT_COLUMNS = (
    "ModelID",
    "ContextID",
    "InjectionAttemptCount",
    "InjectionAppliedCount",
    "InjectionCount",
    "ControlInjected",
    "ControlInjectedReason",
    "ControlZeroProof",
)


def build_control_audit_rows(proof_rows: list[dict]) -> list[dict]:
    """Classify ``InjectionCount`` for every proof row.

    ``InjectionCount``, ``InjectionAttemptCount`` and ``InjectionAppliedCount``
    stay separate columns: the applied/attempt counts are copied verbatim and
    the tri-state is derived *only* from ``InjectionCount``.  A missing column
    or ``None`` is UNKNOWN/MISSING -- never ``NO``.
    """
    rows: list[dict] = []
    for proof in proof_rows:
        raw = proof.get("InjectionCount")
        state, reason = classify_injection_count(raw)
        rows.append({
            "ModelID": proof.get("ModelID", ""),
            "ContextID": proof.get("ContextID", ""),
            "InjectionAttemptCount": proof.get("InjectionAttemptCount", ""),
            "InjectionAppliedCount": proof.get("InjectionAppliedCount", ""),
            "InjectionCount": "" if raw is None else raw,
            "ControlInjected": state,
            "ControlInjectedReason": reason,
            "ControlZeroProof": proof.get("ControlZeroProof", ""),
        })
    return rows


def emit_control_audit(proof_path: Path, out_path: Path) -> int:
    proof_path = Path(proof_path)
    if not proof_path.is_file():
        print(f"error: --proof is not a file: {proof_path}", file=sys.stderr)
        return 2
    try:
        with proof_path.open(newline="", encoding="utf-8") as handle:
            proof_rows = list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        print(f"error: unreadable --proof CSV: {exc}", file=sys.stderr)
        return 2
    if not proof_rows:
        print(f"error: no control rows in {proof_path}", file=sys.stderr)
        return 2

    rows = build_control_audit_rows(proof_rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONTROL_AUDIT_COLUMNS,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    tally: dict[str, int] = {}
    for row in rows:
        state = row["ControlInjected"]
        tally[state] = tally.get(state, 0) + 1
    zero_proven = tally.get(CONTROL_INJECTED_NO, 0)
    print(f"rows={len(rows)} out={out_path}")
    print(f"ControlInjected {dict(sorted(tally.items()))}")
    print(f"zero_injection_proven={zero_proven} "
          f"not_proven={len(rows) - zero_proven}")

    # UNKNOWN/INVALID (and an observed YES) are never counted as a pass.
    problems = [row for row in rows
                if row["ControlInjected"] != CONTROL_INJECTED_NO]
    for row in problems:
        print(f"  {row['ControlInjected']}"
              f"({row['ControlInjectedReason']}): "
              f"{row['ModelID']}-{row['ContextID']} "
              f"InjectionCount={row['InjectionCount']!r} "
              f"attempt={row['InjectionAttemptCount']!r} "
              f"applied={row['InjectionAppliedCount']!r}",
              file=sys.stderr)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify LSU control zero-injection proofs into a CSV."
    )
    parser.add_argument("--runs", type=Path,
                        help="campaign runs root (e.g. audit_v3_3_3/runs); "
                             "required unless --emit-control-audit")
    parser.add_argument("--out", required=True, type=Path,
                        help="output CSV path")
    parser.add_argument("--proof", type=Path,
                        help="Control Zero Proof CSV (with --emit-control-audit)")
    parser.add_argument("--emit-control-audit", action="store_true",
                        help="emit the strict tri-state ControlInjected audit "
                             "CSV from an existing Control Zero Proof CSV")
    parser.add_argument("--evidence-kind", default="PRE_FORMAL",
                        choices=("PRE_FORMAL", "FORMAL"),
                        help="EvidenceKind stamped on every row (default: PRE_FORMAL)")
    args = parser.parse_args(argv)

    if args.emit_control_audit:
        if args.proof is None:
            print("error: --emit-control-audit requires --proof",
                  file=sys.stderr)
            return 2
        return emit_control_audit(args.proof, args.out)

    if args.runs is None:
        print("error: --runs is required unless --emit-control-audit",
              file=sys.stderr)
        return 2
    if not args.runs.is_dir():
        print(f"error: --runs is not a directory: {args.runs}", file=sys.stderr)
        return 2

    rows = build_rows(args.runs, args.evidence_kind)
    if not rows:
        print(f"error: no MODEL-Rxx-control dirs under {args.runs}", file=sys.stderr)
        return 2
    write_csv(args.out, rows)

    def tally(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            value = str(row[key])
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    print(f"rows={len(rows)} out={args.out}")
    print(f"InjectorMounted  {tally('InjectorMounted')}")
    print(f"ControlZeroProof {tally('ControlZeroProof')}")
    print(f"ControlProofStatus {tally('ControlProofStatus')}")
    print(f"OracleResult     {tally('OracleResult')}")

    problems = [r for r in rows
                if r["ControlProofStatus"] in (STATUS_FAIL, STATUS_INCOMPLETE)]
    for row in problems:
        print(f"  {row['ControlProofStatus']}: {row['SampleRunID']} "
              f"({row['ControlZeroProof']}) {row['SuppressionReason']}",
              file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
