#!/usr/bin/env python3
"""Agent E — independent acceptance suite for the LSU v3.3.3 final launch.

This suite is adversarial and fail-closed: it treats the tools as untrusted
implementations of the frozen interfaces in
``docs/superpowers/plans/2026-11-12-lsu-v333-final-launch-closure.md`` and
asserts the launch gates directly.  It never starts gem5, never writes under
``runs/lsu/formal_v333_final_20261112`` and never edits audited source.

Gates covered
-------------
* 12 models / 5 contexts / 120 unique tasks / 60 SampleRunID / 60 Seed / pairs
* frozen binary/config SHA on the real files
* workload ELF SHA for all 12 models against the frozen provenance table
* strict tri-state ``ControlInjected`` classifier (missing/illegal never NO)
* campaign-scoped lock under ``--out-base`` + child-process exclusion
* resume state machine (COMPLETED skip, retry states, HASH_MISMATCH, ORACLE_FAIL)
* collector isolation / missing evidence never PASS
* ``bash -n`` for the four campaign scripts
* the real 120-task dry run (120 commands, READY line, no campaign dir)
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
RUNS_FINAL = ROOT / "runs/lsu/formal_v333_final_20261112"
RUNS_HISTORICAL = ROOT / "runs/lsu/formal_v333"

CAMPAIGN_ID = "LSU-V333-FINAL-20261112"
CAMPAIGN_ID_DEFAULT = "LSU-V333-FORMAL-20261112"

FROZEN_BINARY_SHA = (
    "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd")
FROZEN_CONFIG_SHA = (
    "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225")

FROZEN_MODELS = {
    "A01", "A03", "FW02", "FW05", "SQ01", "SQ03",
    "SP05", "DA04", "LP01", "MD04", "LQ04", "RP01",
}

DESIGN_MATRIX = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
                 / "60_SAMPLE_MATRIX.csv")
DESIGN_MAPPING = (ROOT / "audit_v3_3_3/roi"
                  / "LSU_60Context_ROI_Percentile_Mapping.csv")
PROVENANCE_DOC = (ROOT / "audit_launch_fix_v333/authorization"
                  / "LSU_Final_Binary_Provenance.md")

SHELL_SCRIPTS = tuple(
    ROOT / "audit_v3_3_3/trace_closure/final_config" / name
    for name in ("01_launch_campaign.sh", "02_manifest_only.sh",
                 "03_full_collector.sh", "04_final_reports.sh"))

# ---------------------------------------------------------------------------
# module loading (importlib; never modify the audited tools)
# ---------------------------------------------------------------------------
_MODULE_CACHE: dict[str, object] = {}
_LOAD_ERRORS: dict[str, str] = {}


def _load(name: str, relpath: str):
    if name in _MODULE_CACHE:
        return _MODULE_CACHE[name]
    if name in _LOAD_ERRORS:
        raise AssertionError(
            f"{relpath} could not be imported: {_LOAD_ERRORS[name]}")
    path = ROOT / relpath
    if not path.is_file():
        _LOAD_ERRORS[name] = f"missing file {path}"
        raise AssertionError(_LOAD_ERRORS[name])
    try:
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - surfaced verbatim as a failure
        _LOAD_ERRORS[name] = f"{type(exc).__name__}: {exc}"
        raise AssertionError(
            f"{relpath} could not be imported: {_LOAD_ERRORS[name]}")
    _MODULE_CACHE[name] = module
    return module


def _matrix():
    return _load("lsu_v332_matrix_acceptance", "tools/lsu_v332_matrix.py")


def _run_state():
    return _load("lsu_run_state_acceptance", "tools/lsu_run_state.py")


def _campaign_lock():
    return _load("lsu_campaign_lock_acceptance",
                 "tools/lsu_campaign_lock.py")


def _control_proof():
    return _load("lsu_v333_control_proof_acceptance",
                 "tools/lsu_v333_control_proof.py")


def _collector():
    return _load("lsu_v333_launch_acceptance", "tools/lsu_v333_launch.py")


def _provenance():
    return _load("lsu_v333_provenance_acceptance",
                 "tools/lsu_v333_provenance.py")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _design_rows() -> list[dict]:
    with open(DESIGN_MATRIX, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _frozen_workload_table() -> dict[str, str]:
    """Parse the frozen workload ELF table from the provenance document."""
    text = PROVENANCE_DOC.read_text(encoding="utf-8")
    table: dict[str, str] = {}
    for match in re.finditer(
            r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", text,
            flags=re.MULTILINE):
        table[match.group(1)] = match.group(2)
    return table


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True),
                    encoding="utf-8")


def _fault_control_seed(cmd: list[str]) -> str:
    for index, token in enumerate(cmd):
        if (token == "--seed" or token.endswith("rng_seed")) \
                and index + 1 < len(cmd):
            return cmd[index + 1]
    raise AssertionError(f"no seed flag in planned command: {cmd}")


# ===========================================================================
# Gate 1 — 12 models / 5 contexts / 120 tasks / 60 IDs / 60 seeds / pairs
# ===========================================================================
def test_design_matrix_has_12_models_5_contexts_60_rows():
    rows = _design_rows()
    models = {row["FaultModelID"] for row in rows}
    assert models == FROZEN_MODELS, (
        f"model set drift: {sorted(models ^ FROZEN_MODELS)}")
    counts = {}
    for row in rows:
        model = row["FaultModelID"]
        counts[model] = counts.get(model, 0) + 1
    assert set(counts.values()) == {5}, (
        f"every model must have 5 contexts, got {counts}")


def test_120_unique_tasks_and_60_unique_sample_ids_and_seeds():
    matrix = _matrix()
    assert len(matrix.MODELS) == 12, matrix.MODELS
    rows = _design_rows()
    sample_ids = [row["SampleRunID"] for row in rows]
    seeds = [row["Seed"] for row in rows]
    assert len(rows) == 60, f"expected 60 design rows, got {len(rows)}"
    assert len(set(sample_ids)) == 60, "SampleRunID is not unique"
    assert len(set(seeds)) == 60, "Seed is not unique"

    tasks = set()
    for row in rows:
        model = row["FaultModelID"]
        ctx = row["SampleRunID"][-3:]
        assert ctx in {f"R{i:02d}" for i in range(1, 6)}, ctx
        for role in ("fault", "control"):
            tasks.add((model, ctx, role))
    assert len(tasks) == 120, f"expected 120 unique tasks, got {len(tasks)}"

    # The runner's own frozen identity map must expose the same 60 pairs.
    assert len(matrix.FROZEN_ID) == 60
    assert len({v[0] for v in matrix.FROZEN_ID.values()}) == 60
    assert len({v[1] for v in matrix.FROZEN_ID.values()}) == 60
    for model in FROZEN_MODELS:
        keys = {ctx for (m, ctx) in matrix.FROZEN_ID if m == model}
        assert keys == {f"R{i:02d}" for i in range(1, 6)}, (model, keys)


def test_fault_control_pairs_share_sample_run_id_and_seed(tmp_path):
    matrix = _matrix()
    for row in _design_rows():
        model = row["FaultModelID"]
        ctx = int(row["SampleRunID"][-2:])
        fault_cmd = matrix.planned_command(
            model, ctx, "fault", tmp_path / f"{model}-R{ctx:02d}-fault")
        control_cmd = matrix.planned_command(
            model, ctx, "control", tmp_path / f"{model}-R{ctx:02d}-control")
        assert _fault_control_seed(fault_cmd) == _fault_control_seed(control_cmd), (
            f"{model} R{ctx:02d}: fault/control seed mismatch")
        assert _fault_control_seed(fault_cmd) == row["Seed"], (
            f"{model} R{ctx:02d}: runner seed != frozen design seed")


# ===========================================================================
# Gate 2 — frozen binary and config SHA on the real files
# ===========================================================================
def test_frozen_binary_sha():
    binary = ROOT / "build/ARM/gem5.opt"
    assert binary.is_file(), f"missing {binary}"
    observed = _sha256(binary)
    assert observed == FROZEN_BINARY_SHA, (
        f"build/ARM/gem5.opt SHA256 is {observed}, "
        f"expected frozen {FROZEN_BINARY_SHA}")


def test_frozen_config_sha():
    config = ROOT / "configs/se/lsu_proxy.py"
    assert config.is_file(), f"missing {config}"
    observed = _sha256(config)
    assert observed == FROZEN_CONFIG_SHA, (
        f"configs/se/lsu_proxy.py SHA256 is {observed}, "
        f"expected frozen {FROZEN_CONFIG_SHA}")


# ===========================================================================
# Gate 3 — workload ELF SHA for all 12 models against the frozen table
# ===========================================================================
def test_workload_elf_hashes_match_frozen_table():
    matrix = _matrix()
    frozen = _frozen_workload_table()
    assert len(frozen) >= 9, (
        f"frozen workload table parse produced only {len(frozen)} rows")
    failures = []
    for model in matrix.MODELS:
        path = matrix.resolve_workload(
            model, matrix.CONTEXTS[model].get("workload"))
        assert path is not None and Path(path).is_file(), (
            f"{model}: workload ELF missing: {path}")
        name = Path(path).name
        assert name in frozen, (
            f"{model}: {name} absent from the frozen provenance table")
        observed = _sha256(Path(path))
        if observed != frozen[name]:
            failures.append(f"{model}:{name} {observed} != {frozen[name]}")
    assert not failures, "workload ELF SHA drift: " + "; ".join(failures)


def test_provenance_table_all_12_models_match_frozen():
    provenance = _provenance()
    table = provenance.provenance_table()
    assert len(table) == 12, f"provenance table has {len(table)} rows"
    bad = [row for row in table if not row.get("MatchesFrozen")]
    assert not bad, f"provenance rows not matching frozen table: {bad}"


# ===========================================================================
# Gate 4 — strict tri-state ControlInjected
# ===========================================================================
@pytest.mark.parametrize("value,expected", [
    (0, "NO"),
    ("0", "NO"),
    (" 0 ", "NO"),
    ("+0", "NO"),
    (1, "YES"),
    (5, "YES"),
    ("1", "YES"),
    ("5", "YES"),
])
def test_classify_injection_count_zero_and_positive(value, expected):
    classifier = _control_proof().classify_injection_count
    state, reason = classifier(value)
    assert state == expected, (value, state, reason)


@pytest.mark.parametrize("value,expected", [
    (None, "UNKNOWN"),
    ("", "UNKNOWN"),
    ("   ", "UNKNOWN"),
    ("abc", "UNKNOWN"),
    ("1.0", "UNKNOWN"),
    ("nan", "UNKNOWN"),
    ("0x0", "UNKNOWN"),
    (-1, "INVALID"),
    ("-3", "INVALID"),
])
def test_classify_injection_count_missing_illegal_negative(value, expected):
    classifier = _control_proof().classify_injection_count
    state, reason = classifier(value)
    assert state == expected, (value, state, reason)


def test_control_audit_cli_never_writes_no_for_missing_or_illegal(tmp_path):
    proof = tmp_path / "proof.csv"
    out = tmp_path / "audit.csv"
    with open(proof, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "ModelID", "ContextID", "InjectionAttemptCount",
            "InjectionAppliedCount", "InjectionCount", "ControlZeroProof"])
        writer.writeheader()
        writer.writerow({"ModelID": "A01", "ContextID": "R01",
                         "InjectionAttemptCount": "0",
                         "InjectionAppliedCount": "0",
                         "InjectionCount": "0", "ControlZeroProof": "X"})
        writer.writerow({"ModelID": "A01", "ContextID": "R02",
                         "InjectionAttemptCount": "1",
                         "InjectionAppliedCount": "1",
                         "InjectionCount": "1", "ControlZeroProof": "X"})
        writer.writerow({"ModelID": "A01", "ContextID": "R03",
                         "InjectionAttemptCount": "0",
                         "InjectionAppliedCount": "",
                         "InjectionCount": "", "ControlZeroProof": "X"})
        writer.writerow({"ModelID": "A01", "ContextID": "R04",
                         "InjectionAttemptCount": "-1",
                         "InjectionAppliedCount": "-1",
                         "InjectionCount": "-1", "ControlZeroProof": "X"})
        writer.writerow({"ModelID": "A01", "ContextID": "R05",
                         "InjectionAttemptCount": "?",
                         "InjectionAppliedCount": "?",
                         "InjectionCount": "abc", "ControlZeroProof": "X"})

    rc = _control_proof().main([
        "--emit-control-audit", "--proof", str(proof), "--out", str(out)])
    assert rc != 0, "a control audit with YES/UNKNOWN/INVALID must not exit 0"
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_ctx = {row["ContextID"]: row for row in rows}
    assert by_ctx["R01"]["ControlInjected"] == "NO"
    assert by_ctx["R02"]["ControlInjected"] == "YES"
    assert by_ctx["R03"]["ControlInjected"] == "UNKNOWN"
    assert by_ctx["R04"]["ControlInjected"] == "INVALID"
    assert by_ctx["R05"]["ControlInjected"] == "UNKNOWN"
    # Attempt/Applied stay separate columns and are preserved verbatim.
    assert by_ctx["R02"]["InjectionAttemptCount"] == "1"
    assert by_ctx["R02"]["InjectionAppliedCount"] == "1"


def test_control_audit_cli_missing_column_is_unknown_not_no(tmp_path):
    proof = tmp_path / "proof.csv"
    out = tmp_path / "audit.csv"
    proof.write_text(
        "ModelID,ContextID,InjectionAttemptCount,InjectionAppliedCount,"
        "ControlZeroProof\nA01,R01,,,X\n", encoding="utf-8")
    rc = _control_proof().main([
        "--emit-control-audit", "--proof", str(proof), "--out", str(out)])
    assert rc != 0, "a missing InjectionCount column must not exit 0"
    with open(out, newline="", encoding="utf-8") as fh:
        row = next(iter(csv.DictReader(fh)))
    assert row["ControlInjected"] == "UNKNOWN", row
    assert row["ControlInjected"] != "NO"


# ===========================================================================
# Gate 5 — campaign-scoped lock
# ===========================================================================
def test_lock_path_is_under_out_base_not_historical_root(tmp_path):
    lock = _campaign_lock()
    out_base = tmp_path / "formal_v333_final_20261112"
    path = lock.lock_path(out_base)
    assert path.parent == out_base, (
        f"lock path {path} is not under the campaign root {out_base}")
    assert "formal_v333/" not in str(path), (
        f"lock path leaked into the historical root: {path}")
    signature = inspect.signature(lock.campaign_lock.__wrapped__
                                  if hasattr(lock.campaign_lock, "__wrapped__")
                                  else lock.campaign_lock)
    for name in ("out_base", "campaign_id"):
        assert signature.parameters[name].default is inspect.Parameter.empty, (
            f"campaign_lock.{name} must not have a default argument")


def test_lock_metadata_carries_campaign_identity(tmp_path):
    lock = _campaign_lock()
    out_base = tmp_path / "campaign"
    with lock.campaign_lock(out_base, CAMPAIGN_ID):
        metadata = json.loads(lock.lock_path(out_base).read_text())
    assert metadata["campaign_id"] == CAMPAIGN_ID
    assert metadata["out_base"] == str(out_base)
    for key in ("pid", "hostname", "started_at", "campaign_id", "out_base"):
        assert key in metadata, f"lock metadata missing {key}"


def test_two_concurrent_acquires_cannot_both_succeed(tmp_path):
    lock = _campaign_lock()
    out_base = tmp_path / "campaign"
    lock_file = lock.lock_path(out_base).resolve()
    child = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location("
        "'child_lock', sys.argv[1])\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "from pathlib import Path\n"
        "try:\n"
        "    with mod.campaign_lock(Path(sys.argv[2]), sys.argv[3]):\n"
        "        print('ACQUIRED')\n"
        "except mod.LockHeld as exc:\n"
        "    print('LOCK_HELD ' + str(exc))\n"
        "    sys.exit(3)\n"
    )
    with lock.campaign_lock(out_base, CAMPAIGN_ID):
        result = subprocess.run(
            [sys.executable, "-c", child, str(ROOT / "tools/lsu_campaign_lock.py"),
             str(out_base), CAMPAIGN_ID],
            capture_output=True, text=True, timeout=60)
    assert result.returncode != 0, (
        "a second concurrent campaign acquire succeeded: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}")
    assert "LOCK_HELD" in (result.stdout + result.stderr), (
        f"expected LOCK_HELD; stdout={result.stdout!r} stderr={result.stderr!r}")
    assert lock_file.name.startswith(".lsu_v332_matrix.lock")


def test_dead_pid_lock_is_reclaimed(tmp_path):
    lock = _campaign_lock()
    out_base = tmp_path / "campaign"
    path = lock.lock_path(out_base)
    path.parent.mkdir(parents=True, exist_ok=True)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    _write_json(path, {
        "pid": dead.pid,
        "hostname": os.uname().nodename,
        "started_at": "2026-11-12T00:00:00+00:00",
        "campaign_id": CAMPAIGN_ID,
        "out_base": str(out_base),
    })
    with lock.campaign_lock(out_base, CAMPAIGN_ID) as record:
        assert record["pid"] == os.getpid()
    archived = [p for p in out_base.rglob("*") if p.is_file()
                and any("stale" in part for part in p.parts)]
    assert archived, "a dead-PID lock must be archived before reclaim"


def test_runner_uses_campaign_scoped_lock_and_resume():
    source = (ROOT / "tools/lsu_v332_matrix.py").read_text(encoding="utf-8")
    assert "campaign_lock" in source, (
        "tools/lsu_v332_matrix.py does not use the campaign-scoped lock")
    assert not re.search(r"def matrix_lock\(path: Path = LOCK_FILE",
                         source), (
        "matrix_lock still binds a module-level LOCK_FILE default (the old "
        "runs/lsu/formal_v333 path)")
    assert "scan_task_state" in source, (
        "the runner does not consult the attempt state machine on resume")
    assert "next_attempt_id" in source, (
        "the runner does not allocate attempt ids (no attempt isolation)")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/lsu_v332_matrix.py"), "--help"],
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "--resume" in result.stdout, (
        "the runner CLI does not expose --resume")


# ===========================================================================
# Gate 6 — resume state machine
# ===========================================================================
def _make_attempt(run_dir: Path, attempt_id: str, status: str,
                  outputs=("summary.json",)) -> Path:
    state = _run_state()
    adir = state.attempt_dir(run_dir, attempt_id)
    adir.mkdir(parents=True, exist_ok=True)
    for name in outputs:
        (adir / name).write_text("{}", encoding="utf-8")
    state.write_attempt_record(adir, {"attempt_id": attempt_id,
                                      "status": status,
                                      "campaign_id": CAMPAIGN_ID})
    return adir


def test_completed_attempt_is_skipped_and_canonical(tmp_path):
    state = _run_state()
    run_dir = tmp_path / "A01-R01-fault"
    _make_attempt(run_dir, "attempt_001", state.STATUS_COMPLETED)
    state.write_canonical(run_dir, {"attempt_id": "attempt_001",
                                    "campaign_id": CAMPAIGN_ID})
    info = state.scan_task_state(run_dir, CAMPAIGN_ID)
    assert info["state"] == state.STATUS_COMPLETED, info
    assert state.canonical_dir(run_dir) == state.attempt_dir(
        run_dir, "attempt_001")
    assert state.next_attempt_id(run_dir) == "attempt_002"


@pytest.mark.parametrize("status", ["FAILED", "TIMEOUT", "OUTPUT_INCOMPLETE"])
def test_retryable_attempt_gets_a_new_attempt(tmp_path, status):
    state = _run_state()
    run_dir = tmp_path / "A01-R01-fault"
    _make_attempt(run_dir, "attempt_001", status)
    info = state.scan_task_state(run_dir, CAMPAIGN_ID)
    assert info["state"] == status, info
    assert status in state.RETRYABLE
    assert state.next_attempt_id(run_dir) == "attempt_002"


def test_hash_mismatch_canonical_is_refused(tmp_path):
    state = _run_state()
    run_dir = tmp_path / "A01-R01-fault"
    _make_attempt(run_dir, "attempt_001", state.STATUS_COMPLETED)
    state.write_canonical(run_dir, {"attempt_id": "attempt_001",
                                    "campaign_id": "OLD-CAMPAIGN"})
    info = state.scan_task_state(run_dir, CAMPAIGN_ID)
    assert info["state"] == state.STATUS_HASH_MISMATCH, info
    assert state.STATUS_HASH_MISMATCH not in state.RETRYABLE


def test_oracle_fail_canonical_is_not_replaced(tmp_path):
    state = _run_state()
    run_dir = tmp_path / "RP01-R01-fault"
    _make_attempt(run_dir, "attempt_001", state.STATUS_ORACLE_FAIL)
    _make_attempt(run_dir, "attempt_002", state.STATUS_COMPLETED)
    state.write_canonical(run_dir, {"attempt_id": "attempt_001",
                                    "campaign_id": CAMPAIGN_ID})
    with pytest.raises(RuntimeError):
        state.write_canonical(run_dir, {"attempt_id": "attempt_002",
                                        "campaign_id": CAMPAIGN_ID})
    info = state.scan_task_state(run_dir, CAMPAIGN_ID)
    assert info["state"] == state.STATUS_ORACLE_FAIL, info
    assert info["attempt_id"] == "attempt_001", info


def test_completed_attempt_bytes_are_immutable(tmp_path):
    state = _run_state()
    run_dir = tmp_path / "A01-R01-fault"
    adir = _make_attempt(run_dir, "attempt_001", state.STATUS_COMPLETED)
    record = adir / "attempt.json"
    before = record.read_bytes()
    try:
        state.write_attempt_record(adir, {"attempt_id": "attempt_001",
                                          "status": state.STATUS_RUNNING,
                                          "campaign_id": CAMPAIGN_ID})
    except RuntimeError:
        pass
    assert record.read_bytes() == before, (
        "a COMPLETED attempt record was overwritten")
    assert state.read_attempt_record(adir)["status"] == state.STATUS_COMPLETED


def test_legacy_flat_dir_is_not_accepted_as_formal_attempt(tmp_path):
    state = _run_state()
    run_dir = tmp_path / "A01-R01-fault"
    run_dir.mkdir()
    (run_dir / "summary.json").write_text("{}", encoding="utf-8")
    info = state.scan_task_state(run_dir, CAMPAIGN_ID)
    assert info["state"] == state.STATUS_COMPLETED, info
    assert info["reason"] == "LEGACY_FLAT_RUN_DIR", info
    assert state.canonical_dir(run_dir) == run_dir


def _resume_campaign(tmp_path: Path, status: str,
                     canonical_campaign: str = CAMPAIGN_ID) -> tuple[Path, Path, Path]:
    """A one-task campaign root whose attempt_001 is in ``status``."""
    state = _run_state()
    root = tmp_path / "campaign"
    run_dir = root / "A01-R01-fault"
    _make_attempt(run_dir, "attempt_001", status,
                  outputs=("summary.json", "campaign.json"))
    (state.attempt_dir(run_dir, "attempt_001") / "campaign.json").write_text(
        json.dumps({"campaign_id": CAMPAIGN_ID}), encoding="utf-8")
    state.write_canonical(run_dir, {"attempt_id": "attempt_001",
                                    "campaign_id": canonical_campaign})
    return root, run_dir, state.attempt_dir(run_dir, "attempt_001")


def _run_resume(tmp_path: Path, root: Path) -> tuple[int, list[dict]]:
    matrix = _matrix()
    out_csv = tmp_path / "raw.csv"
    rc = matrix.main([
        "--models", "A01", "--contexts", "1", "--roles", "fault",
        "--out-base", str(root), "--out-csv", str(out_csv),
        "--campaign-id", CAMPAIGN_ID,
        "--expected-binary-sha", FROZEN_BINARY_SHA,
        "--expected-config-sha", FROZEN_CONFIG_SHA,
        "--resume",
    ])
    rows = []
    if out_csv.is_file():
        with open(out_csv, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    return rc, rows


def test_runner_resume_skips_completed_without_execution(tmp_path):
    root, run_dir, adir = _resume_campaign(tmp_path, "COMPLETED")
    before = (adir / "attempt.json").read_bytes()
    rc, rows = _run_resume(tmp_path, root)
    assert rc == 0, f"resume of a COMPLETED task failed; rows={rows}"
    assert len(rows) == 1 and rows[0]["status"] == "COMPLETED", rows
    assert rows[0]["resumed"] in {"True", "true", "YES", "1"}, rows
    assert (adir / "attempt.json").read_bytes() == before, (
        "resume overwrote the completed attempt")
    assert not (run_dir / "attempts" / "attempt_002").exists(), (
        "resume created a second attempt for a COMPLETED task")


def test_runner_resume_does_not_replace_oracle_fail(tmp_path):
    root, run_dir, adir = _resume_campaign(tmp_path, "ORACLE_FAIL")
    before = (adir / "attempt.json").read_bytes()
    rc, rows = _run_resume(tmp_path, root)
    assert rc == 0, rows
    assert len(rows) == 1 and rows[0]["status"] == "ORACLE_FAIL", rows
    assert (adir / "attempt.json").read_bytes() == before
    assert not (run_dir / "attempts" / "attempt_002").exists(), (
        "an ORACLE_FAIL canonical was replaced by a retry")
    canonical = json.loads((run_dir / "canonical.json").read_text())
    assert canonical["attempt_id"] == "attempt_001"


def test_runner_resume_refuses_hash_mismatch(tmp_path, capsys):
    root, run_dir, adir = _resume_campaign(
        tmp_path, "COMPLETED", canonical_campaign="OLD-CAMPAIGN")
    before = (adir / "attempt.json").read_bytes()
    rc, rows = _run_resume(tmp_path, root)
    captured = capsys.readouterr()
    assert rc != 0, (
        "resume accepted a HASH_MISMATCH canonical; rows=" f"{rows}")
    assert "HASH_MISMATCH" in (captured.out + captured.err), (
        captured.out + captured.err)
    assert (adir / "attempt.json").read_bytes() == before


# ===========================================================================
# Manifest isolation fixtures (built under tmp_path; real design rows)
# ===========================================================================
def _selected_rows(n: int = 2) -> tuple[list[dict], Path, Path]:
    rows = _design_rows()
    chosen = []
    seen = set()
    for row in rows:
        if row["FaultModelID"] not in seen and row["SampleRunID"].endswith("R01"):
            chosen.append(row)
            seen.add(row["FaultModelID"])
        if len(chosen) == n:
            break
    assert len(chosen) == n
    return chosen, DESIGN_MATRIX, DESIGN_MAPPING


def _write_design(tmp_path: Path, rows: list[dict]) -> Path:
    with open(DESIGN_MATRIX, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
    out = tmp_path / "design_SAMPLE_MATRIX.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def _build_campaign(tmp_path: Path, rows: list[dict],
                    campaign_id: str = CAMPAIGN_ID,
                    root_name: str = "campaign") -> Path:
    """Create an evidence-complete synthetic campaign root under tmp_path."""
    matrix = _matrix()
    runs = tmp_path / root_name
    runs.mkdir(parents=True, exist_ok=True)
    elf_map = {}
    for row in rows:
        model = row["FaultModelID"]
        workload = matrix.resolve_workload(
            model, matrix.CONTEXTS[model].get("workload"))
        elf_map[Path(workload).name] = _sha256(Path(workload))
    _write_json(runs / "campaign_identity.json", {
        "campaign_id": campaign_id,
        "binary_sha": FROZEN_BINARY_SHA,
        "config_sha": FROZEN_CONFIG_SHA,
        "elf_sha": elf_map,
    })
    for row in rows:
        model = row["FaultModelID"]
        sample_run_id = row["SampleRunID"]
        seed = int(row["Seed"])
        ctx = sample_run_id[-3:]
        workload = matrix.resolve_workload(
            model, matrix.CONTEXTS[model].get("workload"))
        elf_sha = _sha256(Path(workload))
        for role in ("fault", "control"):
            run_dir = runs / f"{model}-{ctx}-{role}"
            run_dir.mkdir(parents=True, exist_ok=True)
            identity = {
                "binary_sha": FROZEN_BINARY_SHA,
                "config_sha": FROZEN_CONFIG_SHA,
                "elf_sha": elf_sha,
                "campaign_id": campaign_id,
                "context": ctx,
                "model": model,
                "role": role,
                "sample_run_id": sample_run_id,
                "seed": seed,
                "status": "COMPLETED",
                "timed_out": False,
                "exit_code": 0,
            }
            _write_json(run_dir / "campaign.json", identity)
            summary = dict(identity)
            summary.update({
                "terminal": "MASKED" if role == "fault" else "UNRESOLVED",
                "terminal_reason": "ACCEPTANCE_FIXTURE",
                "oracle": False if role == "fault" else True,
                "trace_completeness": {
                    "trace_completeness": "COMPLETE",
                    "record_integrity": "VALID",
                },
            })
            if role == "fault":
                summary["injection_count"] = 1
            else:
                summary.update({"injection_count": 0,
                                "injection_applied_count": 0,
                                "injection_attempt_count": 0})
            _write_json(run_dir / "summary.json", summary)
            (run_dir / "oracle.log").write_text(
                "oracle fixture\n", encoding="utf-8")
            with gzip.open(run_dir / "prop_trace.csv.gz", "wt",
                           encoding="utf-8") as fh:
                fh.write("record_type,category\nfixture,fixture\n")
            if role == "fault":
                (run_dir / "trace_v31.jsonl").write_text(
                    json.dumps({"record_type": "event",
                                "event_type": "injection"}) + "\n",
                    encoding="utf-8")
                (run_dir / matrix.MODEL_LOG_NAME[model]).write_text(
                    "faults_injected: 1\n", encoding="utf-8")
                (run_dir / "command.txt").write_text(
                    f"gem5.opt --outdir={run_dir} configs/se/lsu_proxy.py "
                    f"--cmd={workload} --cpu O3 --probability 1.0 "
                    f"--chaos_addrpath --addrpath_rng_seed {seed}\n",
                    encoding="utf-8")
            else:
                (run_dir / "trace_v31.jsonl").write_text(
                    json.dumps({"record_type": "summary",
                                "counts": {"injections": 0}}) + "\n",
                    encoding="utf-8")
                (run_dir / "command.txt").write_text(
                    f"gem5.opt --outdir={run_dir} configs/se/lsu_proxy.py "
                    f"--cmd={workload} --cpu O3 --probability 0.0 "
                    f"--rng_seed {seed}\n",
                    encoding="utf-8")
    return runs


def _collect(tmp_path: Path, runs: Path, rows: list[dict],
             campaign_id: str = CAMPAIGN_ID) -> tuple[Path, int, list[dict]]:
    design = _write_design(tmp_path, rows)
    out = tmp_path / "collector_out"
    rc = _collector().main([
        "--runs", str(runs),
        "--campaign-id", campaign_id,
        "--design-matrix", str(design),
        "--design-mapping", str(DESIGN_MAPPING),
        "--out", str(out),
        "--manifest-only",
    ])
    manifest = out / "LSU_120Run_Campaign_Manifest.csv"
    assert manifest.is_file(), f"collector wrote no manifest: {sorted(out.iterdir()) if out.is_dir() else out}"
    with open(manifest, newline="", encoding="utf-8") as fh:
        records = list(csv.DictReader(fh))
    return out, rc, records


# ===========================================================================
# Gate 7 — manifest isolation and fail-closed evidence
# ===========================================================================
def test_only_matching_campaign_root_evidence_is_formal(tmp_path):
    rows, _, _ = _selected_rows(2)
    runs = _build_campaign(tmp_path, rows)
    _, rc, records = _collect(tmp_path, runs, rows)
    assert rc == 0, "evidence-complete matching campaign must collect cleanly"
    assert len(records) == 4, f"expected 4 records, got {len(records)}"
    assert all(r["EvidenceKind"] == "FORMAL" for r in records), records
    assert all(Path(r["Evidence"]).resolve().is_relative_to(runs.resolve())
               for r in records)


def test_historical_campaign_root_produces_zero_formal(tmp_path):
    rows, _, _ = _selected_rows(2)
    runs = _build_campaign(tmp_path, rows, campaign_id="LSU-V333-FORMAL-20261112",
                           root_name="historical")
    _, _, records = _collect(tmp_path, runs, rows)
    formal = [r for r in records if r["EvidenceKind"] == "FORMAL"]
    assert not formal, (
        f"historical pre-formal evidence was promoted to FORMAL: {formal}")
    assert all(r["Status"] != "COMPLETED" for r in records), records


def test_identity_mismatch_is_not_formal(tmp_path):
    rows, _, _ = _selected_rows(2)
    runs = _build_campaign(tmp_path, rows)
    target = sorted(runs.glob("*-R01-control"))[0]
    payload = json.loads((target / "campaign.json").read_text())
    payload["seed"] = int(payload["seed"]) + 1
    _write_json(target / "campaign.json", payload)
    _, _, records = _collect(tmp_path, runs, rows)
    bad = [r for r in records if r["Evidence"] == str(target)]
    assert bad and bad[0]["EvidenceKind"] != "FORMAL", bad


@pytest.mark.parametrize("victim", ["summary.json", "trace_v31.jsonl",
                                    "oracle.log"])
def test_missing_required_artifact_is_never_pass(tmp_path, victim):
    rows, _, _ = _selected_rows(1)
    runs = _build_campaign(tmp_path, rows)
    target = sorted(runs.glob("*-R01-fault"))[0]
    (target / victim).unlink()
    _, _, records = _collect(tmp_path, runs, rows)
    fault = [r for r in records
             if r["Role"] == "fault" and r["ModelID"] == rows[0]["FaultModelID"]]
    assert fault, records
    assert fault[0]["Status"] != "COMPLETED", fault
    assert fault[0]["Status"] not in {
        "ORACLE_FAIL", "QUALIFIED", "TRACE_INCOMPLETE"}, fault
    assert fault[0]["InjectionCount"] not in {"0", 0}, (
        "a missing artifact must never be reported as a zero count")


def test_missing_injection_count_control_is_not_a_zero_pass(tmp_path):
    rows, _, _ = _selected_rows(1)
    runs = _build_campaign(tmp_path, rows)
    target = sorted(runs.glob("*-R01-control"))[0]
    summary = json.loads((target / "summary.json").read_text())
    for key in ("injection_count", "injection_applied_count",
                "injection_attempt_count"):
        summary.pop(key, None)
    _write_json(target / "summary.json", summary)
    (target / "trace_v31.jsonl").unlink()
    _, _, records = _collect(tmp_path, runs, rows)
    control = [r for r in records
               if r["Role"] == "control"
               and r["ModelID"] == rows[0]["FaultModelID"]]
    assert control, records
    assert control[0]["Status"] != "COMPLETED", control
    assert control[0]["InjectionCount"] not in {"0", 0}, (
        "missing InjectionCount must not become a zero-injection PASS")


# ===========================================================================
# Gate 8 — shell syntax for the four campaign scripts
# ===========================================================================
@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=lambda p: p.name)
def test_campaign_shell_scripts_parse(script):
    assert script.is_file(), f"missing campaign script {script}"
    result = subprocess.run(["bash", "-n", str(script)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, (
        f"bash -n failed for {script}: {result.stderr}")


def test_campaign_scripts_pin_final_root_and_campaign_id():
    for script in SHELL_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert "runs/lsu/formal_v333_final_20261112" in text, (
            f"{script.name} does not reference the final campaign root")
        assert CAMPAIGN_ID in text, (
            f"{script.name} does not pin the campaign id {CAMPAIGN_ID}")


# ===========================================================================
# Gate E-extra — authorization/provenance material coherence
# ===========================================================================
STALE_BINARY_SHA = (
    "1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338")
AUTH_DIR = ROOT / "audit_launch_fix_v333/authorization"
AUTHORIZATION_DOCS = (
    AUTH_DIR / "LSU_Final_Binary_Provenance.md",
    AUTH_DIR / "LSU_v3.3.3_Final_Campaign_Authorization_README.md",
    AUTH_DIR / "launch_commands.sh",
)
AUTHORIZATION_LAUNCH_FILES = AUTHORIZATION_DOCS[1:]


def test_authorization_packet_matches_final_launch_configuration():
    """The researcher-facing authorization packet must name the frozen
    binary/root/campaign.  A stale packet silently points at a historical
    root and at a binary SHA that no longer exists."""
    problems = []
    for path in AUTHORIZATION_DOCS:
        assert path.is_file(), f"missing authorization artifact {path}"
        text = path.read_text(encoding="utf-8")
        if STALE_BINARY_SHA in text:
            problems.append(f"{path.name}: still records binary {STALE_BINARY_SHA[:12]}…")
        if FROZEN_BINARY_SHA not in text:
            problems.append(f"{path.name}: does not record frozen binary "
                            f"{FROZEN_BINARY_SHA[:12]}…")
        if path in AUTHORIZATION_LAUNCH_FILES:
            if "runs/lsu/formal_v333_final_20261112" not in text:
                problems.append(
                    f"{path.name}: does not reference the final root")
            if CAMPAIGN_ID not in text:
                problems.append(
                    f"{path.name}: does not reference {CAMPAIGN_ID}")
    archived = ROOT / "audit_v3_3_3/binary/gem5.opt.v333-1126e0fd"
    if archived.is_file():
        observed = _sha256(archived)
        if not observed.startswith("1126e0fd"):
            problems.append(
                f"{archived.name}: filename names 1126e0fd… but content is "
                f"{observed[:12]}…")
    assert not problems, "authorization packet is stale:\n  " + "\n  ".join(problems)


# ===========================================================================
# Gate 9 — the real 120-task dry run
# ===========================================================================
_DRY_RUN: dict | None = None


def _dry_run() -> dict:
    global _DRY_RUN
    if _DRY_RUN is not None:
        return _DRY_RUN
    existed_before = RUNS_FINAL.exists()
    result = subprocess.run([
        sys.executable, str(ROOT / "tools/lsu_v332_matrix.py"),
        "--models", "all", "--roles", "fault,control",
        "--contexts", "1,2,3,4,5",
        "--out-base", str(RUNS_FINAL),
        "--campaign-id", CAMPAIGN_ID,
        "--expected-binary-sha", FROZEN_BINARY_SHA,
        "--expected-config-sha", FROZEN_CONFIG_SHA,
        "--dry-run",
    ], capture_output=True, text=True, timeout=300, cwd=str(ROOT))
    _DRY_RUN = {
        "result": result,
        "existed_before": existed_before,
        "exists_after": RUNS_FINAL.exists(),
    }
    return _DRY_RUN


def test_dry_run_emits_120_unique_commands():
    run = _dry_run()
    result = run["result"]
    assert result.returncode == 0, (
        f"dry-run exited {result.returncode}: {result.stderr}")
    lines = [line for line in result.stdout.splitlines()
             if line.startswith("DRY-RUN ")]
    assert len(lines) == 120, f"expected 120 DRY-RUN lines, got {len(lines)}"
    outdirs = re.findall(r"--outdir(?:=|\s+)(\S+)", result.stdout)
    assert len(outdirs) == 120, f"expected 120 outdirs, got {len(outdirs)}"
    assert len(set(outdirs)) == 120, "duplicate outdir in the 120-task plan"
    assert all(path.startswith(str(RUNS_FINAL)) for path in outdirs), (
        "a planned outdir is outside the campaign root")
    assert not any(Path(path).exists() for path in outdirs), (
        "dry-run planned an outdir that already exists (collision)")

    expected_tasks = {
        f"{row['FaultModelID']}-{row['SampleRunID'][-3:]}-{role}"
        for row in _design_rows() for role in ("fault", "control")}
    observed_tasks = {Path(path).name for path in outdirs}
    assert observed_tasks == expected_tasks, (
        f"dry-run task drift: {sorted(observed_tasks ^ expected_tasks)}")


def test_dry_run_prints_ready_line_only_when_safe():
    run = _dry_run()
    result = run["result"]
    assert "READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES" in result.stdout, (
        "the dry-run did not print READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES; "
        f"stdout tail={result.stdout.splitlines()[-3:]} "
        f"stderr tail={result.stderr.splitlines()[-3:]}")


def test_dry_run_summary_gate_fields():
    result = _dry_run()["result"]
    lines = [line for line in result.stdout.splitlines()
             if line.startswith("DRY_RUN_SUMMARY ")]
    assert len(lines) == 1, f"expected one DRY_RUN_SUMMARY line, got {lines}"
    gate = json.loads(lines[0][len("DRY_RUN_SUMMARY "):])
    assert gate["task_count"] == 120 and gate["unique_task_count"] == 120, gate
    assert gate["unique_sample_run_ids"] == 60, gate
    assert gate["unique_seeds"] == 60, gate
    assert gate["pairing_ok"] is True, gate
    assert gate["unique_outdirs_ok"] is True, gate
    assert gate["existing_outdir_collisions"] == 0, gate
    assert gate["binary_sha"] == FROZEN_BINARY_SHA, gate
    assert gate["config_sha"] == FROZEN_CONFIG_SHA, gate
    assert gate["elf_ok"] is True, gate
    assert gate["campaign_id"] == CAMPAIGN_ID, gate
    assert gate["ok"] is True, gate


def test_dry_run_does_not_create_the_campaign_dir():
    run = _dry_run()
    assert not run["existed_before"], (
        f"{RUNS_FINAL} existed before the dry-run; the no-creation gate "
        "cannot be measured")
    assert not run["exists_after"], (
        f"the dry run created {RUNS_FINAL}")
