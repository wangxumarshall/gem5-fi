"""Parse the frozen LSU v3.1 Excel into a validated, normalized run configuration.

Authority for every value is the Excel itself.  This module never invents a
seed, never substitutes a workload path, and never fills a missing field with a
default.  ``require_complete=True`` raises one ``ConfigError`` listing every
problem after the whole sheet has been inspected, so a caller can see all 45
missing WorkloadPath rows (or any other gap) in one run.

The normalized record is the input to ``manifest.py`` and to the pilot runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import openpyxl

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
MODEL_COUNT = 12
SAMPLES_PER_MODEL = 5
SAMPLE_COUNT = MODEL_COUNT * SAMPLES_PER_MODEL
VALID_MODES = {"F0", "F5", "F6"}

# Columns the v3.2 platform consumes.  The v3.1 workbook also carries legacy
# TerminalState/TraceCompleteness columns (34/35); the v3.2 fields are 41/42.
REQUIRED_COLUMNS = [
    "SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID",
    "FaultLocation", "TargetField", "BitEntryByteIndex", "NormalValue",
    "FaultValue", "InjectionMode", "InjectionTiming", "FaultDuration",
    "TargetInstruction", "EligibleEventCondition", "EventOrdinal",
    "FaultConfigID", "ContextDifferenceRule", "WorkloadPath",
    "BinarySHA256", "InputHash", "Oracle", "WarmUp", "ROI",
    "gem5Commit", "BinaryPath", "ConfigScript", "FullCommand", "Timeout",
    "OutputDir", "RequiredLogs", "PreflightStatus", "ExecutionStatus",
    "TerminalState", "TraceCompleteness", "EvidencePath", "DecisionStatus",
    "ConfigFrozen", "RunStatus", "FaultActivationStatus",
    "TerminalState_v31", "TraceCompleteness_v31",
]

# Excel column -> normalized JSON key.
FIELD_MAP = {
    "SampleRunID": "sample_run_id",
    "RunID": "run_id",
    "SubTaskID": "sub_task_id",
    "Seed": "seed",
    "FaultModelID": "model_id",
    "FaultLocation": "fault_location",
    "TargetField": "target_field",
    "BitEntryByteIndex": "target_bit",
    "NormalValue": "normal_value",
    "FaultValue": "fault_value",
    "InjectionMode": "injection_mode",
    "InjectionTiming": "injection_timing",
    "FaultDuration": "fault_duration",
    "TargetInstruction": "target_instruction",
    "EligibleEventCondition": "target_event",
    "EventOrdinal": "event_ordinal",
    "FaultConfigID": "fault_config_id",
    "ContextDifferenceRule": "context_difference_rule",
    "WorkloadPath": "workload_path",
    "BinarySHA256": "binary_sha256",
    "InputHash": "input_hash",
    "Oracle": "oracle",
    "WarmUp": "warmup",
    "ROI": "roi",
    "gem5Commit": "gem5_commit",
    "BinaryPath": "binary_path",
    "ConfigScript": "config_script",
    "FullCommand": "full_command",
    "Timeout": "timeout",
    "OutputDir": "output_dir",
    "RequiredLogs": "required_logs",
    "PreflightStatus": "preflight_status",
    "ExecutionStatus": "execution_status",
    "TerminalState_v31": "terminal_state_v31",
    "TraceCompleteness_v31": "trace_completeness_v31",
    "RunStatus": "run_status_v31",
    "FaultActivationStatus": "fault_activation_status_v31",
    "DecisionStatus": "decision_status",
    "ConfigFrozen": "config_frozen",
    "EvidencePath": "evidence_path",
}


class ConfigError(RuntimeError):
    """Raised when the frozen workbook cannot produce a complete run config."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        self.errors = errors or []
        if self.errors:
            detail = "\n".join(
                f"  - {e.get('sample_run_id', '<workbook>')}: "
                f"{e.get('field', '')}: {e.get('message', '')}"
                for e in self.errors[:80]
            )
            more = ""
            if len(self.errors) > 80:
                more = f"\n  ... {len(self.errors) - 80} more"
            message = f"{message} ({len(self.errors)} error(s))\n{detail}{more}"
        super().__init__(message)


def _repo_root() -> Path:
    # .../docs/gem5-fi/lsu/implementation_v3_2/platform/config_parser.py
    return Path(__file__).resolve().parents[5]


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_workload(raw_path: Any, repo_root: Path) -> tuple[str, Path | None, str | None]:
    """Return (normalized_path, existing_path_or_None, warning_or_None).

    The workbook stores absolute paths under /home/sdc/gem5-fi-ding.  When the
    same repository is checked out in a worktree, prefer the worktree copy of
    that same relative path.  This is path *mapping*, not a default: the
    original value is retained in ``workload_path_source``.
    """
    if _is_blank(raw_path) or str(raw_path).strip() == "ABSENT":
        return "ABSENT", None, None
    raw = str(raw_path)
    p = Path(raw)
    if p.exists():
        return str(p), p, None
    marker = "/gem5-fi-ding/"
    if marker in raw:
        rel = raw.split(marker, 1)[1]
        candidate = repo_root / rel
        if candidate.exists():
            return str(candidate), candidate, (
                f"workload path mapped from {raw} to worktree {candidate}"
            )
    return raw, None, None


def normalize_sample(row: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or _repo_root()
    out: dict[str, Any] = {}
    for col, key in FIELD_MAP.items():
        out[key] = row.get(col)
    # ModelID is FaultModelID on the sample sheet; make the v3.2 name explicit.
    out["model_id"] = row.get("FaultModelID")
    out["workload_path_source"] = row.get("WorkloadPath")
    resolved, existing, warning = _resolve_workload(row.get("WorkloadPath"), repo_root)
    out["workload_path"] = resolved
    out["workload_exists"] = existing is not None
    if warning:
        out["workload_path_warning"] = warning
    if isinstance(out.get("seed"), str) and out["seed"].strip().isdigit():
        out["seed"] = int(out["seed"].strip())
    return out


def _err(errors: list[dict[str, Any]], sample_id: Any, field: str, message: str) -> None:
    errors.append({"sample_run_id": sample_id, "field": field, "message": message})


def validate_samples(
    samples: list[dict[str, Any]],
    *,
    expected_models: Iterable[str] | None = None,
    full: bool = True,
) -> list[dict[str, Any]]:
    """Validate normalized samples; return every error (never stop at the first)."""
    errors: list[dict[str, Any]] = []
    if len(samples) != SAMPLE_COUNT:
        _err(errors, "<workbook>", "SAMPLE_COUNT",
             f"expected {SAMPLE_COUNT}, got {len(samples)}")

    ids = [s.get("sample_run_id") for s in samples]
    for sid, n in Counter(ids).items():
        if n > 1:
            _err(errors, sid, "SampleRunID", f"duplicate SampleRunID ({n} rows)")
    seeds = [s.get("seed") for s in samples]
    for seed, n in Counter(seeds).items():
        if n > 1:
            _err(errors, "<workbook>", "Seed", f"duplicate Seed {seed!r} ({n} rows)")

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in samples:
        by_model[str(s.get("model_id"))].append(s)
    if expected_models is not None:
        expected = set(expected_models)
        got = set(by_model)
        if got != expected:
            _err(errors, "<workbook>", "FaultModelID",
                 f"model set mismatch: missing={sorted(expected - got)} extra={sorted(got - expected)}")
    if len(by_model) != MODEL_COUNT:
        _err(errors, "<workbook>", "FaultModelID",
             f"expected {MODEL_COUNT} models, got {len(by_model)}")
    for model, rows in sorted(by_model.items()):
        if len(rows) != SAMPLES_PER_MODEL:
            _err(errors, "<workbook>", "FaultModelID",
                 f"{model}: expected {SAMPLES_PER_MODEL} samples, got {len(rows)}")

    for s in samples:
        sid = s.get("sample_run_id")
        rid = s.get("run_id")
        sub = s.get("sub_task_id")
        model = s.get("model_id")
        if _is_blank(sid) or _is_blank(rid) or _is_blank(sub):
            _err(errors, sid, "identity", "SampleRunID/RunID/SubTaskID must all be present")
        else:
            if not str(sid).startswith(str(sub) + "-R"):
                _err(errors, sid, "SampleRunID", f"parent mismatch with SubTaskID {sub!r}")
            if not str(sub).startswith(str(rid) + "-S"):
                _err(errors, sid, "SubTaskID", f"parent mismatch with RunID {rid!r}")
            if not str(rid).startswith(str(model) + "-"):
                _err(errors, sid, "RunID", f"RunID {rid!r} does not start with model {model!r}")

        seed = s.get("seed")
        if not isinstance(seed, int) or seed <= 0:
            _err(errors, sid, "Seed", f"seed must be a positive integer, got {seed!r}")
        mode = s.get("injection_mode")
        if mode not in VALID_MODES:
            _err(errors, sid, "InjectionMode", f"expected one of {sorted(VALID_MODES)}, got {mode!r}")

        wl = s.get("workload_path")
        if wl == "ABSENT" or _is_blank(wl):
            _err(errors, sid, "WorkloadPath", "ABSENT/missing workload path")
        elif not s.get("workload_exists"):
            _err(errors, sid, "WorkloadPath", f"path does not exist: {wl}")

        sha = s.get("binary_sha256")
        if _is_blank(sha) or str(sha).strip().upper() == "N/A":
            _err(errors, sid, "BinarySHA256", "N/A/missing binary SHA256")
        elif s.get("workload_exists"):
            got = _sha256(Path(wl))
            if str(sha).lower() != got:
                _err(errors, sid, "BinarySHA256", f"expected {sha}, actual {got}")

        oracle = s.get("oracle")
        if _is_blank(oracle) or str(oracle).strip().upper() == "N/A":
            _err(errors, sid, "Oracle", "N/A/missing oracle value")

        if full:
            for field in ("warmup", "roi"):
                value = s.get(field)
                if _is_blank(value) or str(value).startswith("NEEDS_CONFIG"):
                    _err(errors, sid, field.capitalize(), f"unresolved value: {value!r}")
            for field in ("fault_location", "target_field", "target_bit",
                          "normal_value", "fault_value", "injection_timing",
                          "target_instruction", "target_event"):
                if _is_blank(s.get(field)):
                    _err(errors, sid, field, "missing required configuration field")

    errors.sort(key=lambda e: (str(e.get("sample_run_id")), str(e.get("field"))))
    return errors


def load_config(path: Path, *, require_complete: bool = True) -> dict[str, Any]:
    """Load the frozen workbook.

    ``require_complete=False`` still validates and returns ``validation.errors``;
    it is used by Gate-1 tests and by the repair tool to enumerate gaps.  The
    default raises ``ConfigError`` when any error exists.
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"workbook not found: {path}")
    wb = openpyxl.load_workbook(path, data_only=True)
    if SAMPLE_SHEET not in wb.sheetnames:
        raise ConfigError(f"missing sheet {SAMPLE_SHEET!r}; sheets={wb.sheetnames}")
    ws = wb[SAMPLE_SHEET]
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    header_index = {str(h): i for i, h in enumerate(headers) if h is not None}
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in header_index]
    if missing_cols:
        raise ConfigError(f"missing required columns: {missing_cols}")

    raw_rows: list[dict[str, Any]] = []
    for r in range(2, ws.max_row + 1):
        if _is_blank(ws.cell(r, 1).value):
            continue
        raw_rows.append({h: ws.cell(r, header_index[h] + 1).value for h in REQUIRED_COLUMNS})

    samples = [normalize_sample(row) for row in raw_rows]
    expected_models: list[str] | None = None
    if MODEL_SHEET in wb.sheetnames:
        mws = wb[MODEL_SHEET]
        mh = [mws.cell(1, c).value for c in range(1, mws.max_column + 1)]
        if "ModelID" in mh:
            col = mh.index("ModelID") + 1
            expected_models = [str(mws.cell(r, col).value) for r in range(2, mws.max_row + 1)
                               if not _is_blank(mws.cell(r, col).value)]
    errors = validate_samples(samples, expected_models=expected_models)
    if require_complete and errors:
        raise ConfigError(f"workbook is not a complete frozen configuration: {path}", errors)

    models = sorted({str(s["model_id"]) for s in samples})
    return {
        "schema_version": "lsu-config-v3.2",
        "source": str(path),
        "source_sha256": _sha256(path),
        "models": models,
        "samples": samples,
        "counts": {
            "samples": len(samples),
            "models": len(models),
            "seeds": len({s["seed"] for s in samples}),
            "workloads_present": sum(1 for s in samples if s.get("workload_exists")),
        },
        "validation": {"errors": errors, "error_count": len(errors)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workbook", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="write the config plus validation.errors instead of failing")
    args = ap.parse_args(argv)
    try:
        cfg = load_config(args.workbook, require_complete=not args.allow_incomplete)
    except ConfigError as exc:
        print(f"CONFIG_INVALID: {exc}", file=sys.stderr)
        if exc.errors:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(
                {"schema_version": "lsu-config-v3.2", "source": str(args.workbook),
                 "validation": {"errors": exc.errors, "error_count": len(exc.errors)}},
                ensure_ascii=False, indent=2), encoding="utf-8")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CONFIG_OK samples={cfg['counts']['samples']} models={cfg['counts']['models']} "
          f"seeds={cfg['counts']['seeds']} workloads_present={cfg['counts']['workloads_present']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
