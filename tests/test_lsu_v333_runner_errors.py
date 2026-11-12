"""LSU v3.3.3 runner error/timeout/exit handling (Agent A).

Every assertion is over synthetic run dirs under ``tmp_path`` (or a tiny
Python child process for the timeout path).  gem5 is never invoked and the
shared ``tests/fixtures/lsu_v333_synthetic/`` tree is never read or written.

Status vocabulary under test (audit_launch_fix_v333/README_INTERFACES.md):
    PENDING, RUNNING, COMPLETED, FAILED, TIMEOUT, OUTPUT_INCOMPLETE,
    HASH_MISMATCH, ORACLE_FAIL
ORACLE_FAIL is a measured terminal (SDC) -- recorded, but it does not by
itself make the campaign exit nonzero.
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import nullcontext
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(PLATFORM))

import lsu_v332_matrix as mx  # noqa: E402
import run_pilot as rp  # noqa: E402

MODEL_LOG = mx.MODEL_LOG_NAME


# ---------------------------------------------------------------------------
# Synthetic run dirs
# ---------------------------------------------------------------------------
def make_run(tmp_path, model="A01", role="fault", *, summary=True,
             trace=True, oracle=True, model_log=True, trace_v31=True,
             terminal="MASKED", oracle_pass=True, watchdog_marker=False):
    """Build a run dir with the documented artifact set for model/role."""
    out = tmp_path / f"{model}-R01-{role}"
    out.mkdir(parents=True, exist_ok=True)
    if summary:
        (out / "summary.json").write_text(json.dumps(
            {"model": model, "terminal": terminal, "oracle": oracle_pass}))
    if trace:
        (out / "prop_trace.csv.gz").write_bytes(b"")
    if oracle:
        (out / "oracle.log").write_text("ORACLE PASS\n")
    if model_log:
        token = ""
        if watchdog_marker:
            token = ("A03_WATCHDOG_EXPIRED\n" if model == "A03"
                     else "CHAOS_RP01_WATCHDOG_EXPIRED\n")
        (out / MODEL_LOG[model]).write_text(token or "log\n")
    if trace_v31 and mx.driver_for(model, role) == "run_pilot":
        (out / "trace_v31.jsonl").write_text("")
    if watchdog_marker and not (out / "stdout.log").exists():
        token = ("A03_WATCHDOG_EXPIRED\n" if model == "A03"
                 else "CHAOS_RP01_WATCHDOG_EXPIRED\n")
        (out / "stdout.log").write_text(token)
    return out


def _status(model, out, *, role="fault", terminal="MASKED", oracle_pass=True,
            exit_code=0, timed_out=False, parse_error=None,
            runner_status=None, crash_by_fault=False):
    validation = mx.validate_outputs(model, out, role=role,
                                     parse_error=parse_error)
    status = mx.measured_status(
        model=model, role=role, terminal=terminal, oracle_pass=oracle_pass,
        exit_code=exit_code, timed_out=timed_out,
        validation_status=validation["status"], parse_error=parse_error,
        runner_status=runner_status, crash_by_fault=crash_by_fault)
    return validation, status


# ---------------------------------------------------------------------------
# 1. Full success
# ---------------------------------------------------------------------------
def test_full_success_is_completed_and_exit_zero(tmp_path):
    out = make_run(tmp_path)
    validation, status = _status("A01", out)
    assert validation["status"] == mx.PREFLIGHT_OK
    assert validation["missing"] == []
    assert status == mx.STATUS_COMPLETED
    assert mx.campaign_exit_code([{"status": status}]) == 0


def test_run_pilot_full_success_output_validation(tmp_path):
    out = tmp_path / "rp"
    out.mkdir()
    for name in ("command.txt", "prop_trace.csv.gz", "oracle.log",
                 MODEL_LOG["A01"]):
        (out / name).write_text("x")
    validation = rp.output_validation(out, "A01", 1.0)
    assert validation["status"] == "OK", validation
    assert rp.acceptance_exit_code(True, validation) == 0


# ---------------------------------------------------------------------------
# 2. Missing outputs
# ---------------------------------------------------------------------------
def test_missing_summary_is_output_incomplete(tmp_path):
    out = make_run(tmp_path, summary=False)
    validation, status = _status("A01", out)
    assert "summary.json" in validation["missing"]
    assert validation["status"] == mx.STATUS_OUTPUT_INCOMPLETE
    assert status == mx.STATUS_OUTPUT_INCOMPLETE
    assert mx.campaign_exit_code([{"status": status}]) == 1


def test_missing_trace_is_output_incomplete(tmp_path):
    out = make_run(tmp_path, trace=False)
    validation, status = _status("A01", out)
    assert "prop_trace.csv.gz" in validation["missing"]
    assert validation["status"] == mx.STATUS_OUTPUT_INCOMPLETE
    assert status == mx.STATUS_OUTPUT_INCOMPLETE


def test_missing_oracle_is_output_incomplete(tmp_path):
    out = make_run(tmp_path, oracle=False)
    validation, status = _status("A01", out)
    assert "oracle.log" in validation["missing"]
    assert status == mx.STATUS_OUTPUT_INCOMPLETE


def test_missing_model_log_is_output_incomplete_for_fault(tmp_path):
    out = make_run(tmp_path, model_log=False)
    validation, status = _status("A01", out)
    assert MODEL_LOG["A01"] in validation["missing"]
    assert status == mx.STATUS_OUTPUT_INCOMPLETE


def test_control_does_not_require_the_injector_log(tmp_path):
    out = make_run(tmp_path, role="control", model_log=False)
    validation, status = _status("A01", out, role="control",
                                 terminal="UNRESOLVED")
    assert validation["status"] == mx.PREFLIGHT_OK
    assert status == mx.STATUS_COMPLETED


# ---------------------------------------------------------------------------
# 3. Preflight: seed / SampleRunID / SHA / unique outdir
# ---------------------------------------------------------------------------
def _preflight_files(tmp_path):
    binary = tmp_path / "gem5.opt"
    config = tmp_path / "lsu_proxy.py"
    elf = tmp_path / "workload"
    for p in (binary, config, elf):
        p.write_text("x")
    return binary, config, elf


def test_preflight_missing_seed_fails_without_running(tmp_path):
    binary, config, elf = _preflight_files(tmp_path)
    pre = mx.preflight_task(
        model="A01", role="fault", binary=binary, config=config,
        workload=elf, seed=None, sample_run_id="SR-000001",
        outdir=tmp_path / "run", expected_binary_sha=None,
        expected_config_sha=None, sha_fn=lambda p: "sha")
    assert pre["status"] == mx.STATUS_FAILED
    assert pre["ok"] is False
    assert "seed" in pre["evidence"]["missing"]


def test_preflight_missing_sample_run_id_fails(tmp_path):
    binary, config, elf = _preflight_files(tmp_path)
    pre = mx.preflight_task(
        model="A01", role="fault", binary=binary, config=config,
        workload=elf, seed=1234, sample_run_id="",
        outdir=tmp_path / "run", expected_binary_sha=None,
        expected_config_sha=None, sha_fn=lambda p: "sha")
    assert pre["status"] == mx.STATUS_FAILED
    assert "sample_run_id" in pre["evidence"]["missing"]


def test_preflight_existing_outdir_is_not_unique(tmp_path):
    binary, config, elf = _preflight_files(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    (out / "summary.json").write_text("{}")
    pre = mx.preflight_task(
        model="A01", role="fault", binary=binary, config=config,
        workload=elf, seed=1234, sample_run_id="SR-000001", outdir=out,
        expected_binary_sha=None, expected_config_sha=None,
        sha_fn=lambda p: "sha")
    assert pre["status"] == mx.STATUS_FAILED
    assert "outdir_unique" in pre["evidence"]["missing"]


def test_preflight_binary_sha_mismatch_is_hash_mismatch(tmp_path):
    binary, config, elf = _preflight_files(tmp_path)
    pre = mx.preflight_task(
        model="A01", role="fault", binary=binary, config=config,
        workload=elf, seed=1234, sample_run_id="SR-000001",
        outdir=tmp_path / "run", expected_binary_sha="0" * 64,
        expected_config_sha=None, sha_fn=lambda p: "f" * 64)
    assert pre["status"] == mx.STATUS_HASH_MISMATCH
    assert "binary" in pre["evidence"]["sha_mismatches"]


def test_preflight_elf_sha_mismatch_is_hash_mismatch(tmp_path):
    binary, config, elf = _preflight_files(tmp_path)
    pre = mx.preflight_task(
        model="A01", role="fault", binary=binary, config=config,
        workload=elf, seed=1234, sample_run_id="SR-000001",
        outdir=tmp_path / "run", expected_binary_sha=None,
        expected_config_sha=None, expected_elf_sha="0" * 64,
        sha_fn=lambda p: "f" * 64)
    assert pre["status"] == mx.STATUS_HASH_MISMATCH
    assert "workload" in pre["evidence"]["sha_mismatches"]


def test_preflight_missing_binary_is_failed(tmp_path):
    _binary, config, elf = _preflight_files(tmp_path)
    pre = mx.preflight_task(
        model="A01", role="fault", binary=tmp_path / "absent", config=config,
        workload=elf, seed=1, sample_run_id="SR-000001",
        outdir=tmp_path / "run", expected_binary_sha=None,
        expected_config_sha=None, sha_fn=lambda p: "sha")
    assert pre["status"] == mx.STATUS_FAILED
    assert "binary" in pre["evidence"]["missing"]


# ---------------------------------------------------------------------------
# 4. Subprocess execution: OSError and timeout
# ---------------------------------------------------------------------------
def test_subprocess_oserror_is_failed(tmp_path):
    info = mx.run_subprocess([str(tmp_path / "no-such-binary")],
                             outdir=tmp_path / "out", timeout=5)
    assert info["status"] == mx.STATUS_FAILED
    assert info["timed_out"] is False
    assert info["exit_code"] is None
    assert "OSError" in (tmp_path / "out" / "stderr.log").read_text()


def test_subprocess_timeout_is_timeout_and_kills_the_group(tmp_path):
    pid_file = tmp_path / "child.pid"
    code = (
        "import subprocess, sys, time\n"
        "child = subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(60)'])\n"
        "open(sys.argv[1], 'w').write(str(child.pid))\n"
        "sys.stdout.flush()\n"
        "time.sleep(60)\n")
    info = mx.run_subprocess([sys.executable, "-c", code, str(pid_file)],
                             outdir=tmp_path / "out", timeout=1.5)
    assert info["status"] == mx.STATUS_TIMEOUT
    assert info["timed_out"] is True
    assert info["exit_code"] == 124
    assert info["pid"]
    assert "TIMEOUT: external wall-clock limit reached" in info["stderr"]
    assert (tmp_path / "out" / "stderr.log").exists()
    # The whole session was killed: the grandchild must not still be running
    # (it may linger briefly as an unreaped zombie in a container).
    assert pid_file.exists()
    child_pid = int(pid_file.read_text())
    try:
        state = Path(f"/proc/{child_pid}/stat").read_text().split()[2]
    except FileNotFoundError:
        state = None
    assert state is None or state == "Z", state


def test_timeout_is_never_completed_or_oracle_fail(tmp_path):
    out = make_run(tmp_path)
    validation = mx.validate_outputs("A01", out, role="fault")
    status = mx.measured_status(
        model="A01", role="fault", terminal="MASKED", oracle_pass=True,
        exit_code=0, timed_out=True,
        validation_status=validation["status"])
    assert status == mx.STATUS_TIMEOUT
    assert status not in (mx.STATUS_COMPLETED, mx.STATUS_ORACLE_FAIL)


# ---------------------------------------------------------------------------
# 5. Terminal-source distinction (model watchdog vs external/Python timeout)
# ---------------------------------------------------------------------------
def test_terminal_sources_are_never_conflated():
    assert mx.terminal_source(timed_out=True) == mx.TERMINAL_SOURCE_PYTHON_TIMEOUT
    assert mx.terminal_source(watchdog=True) == \
        mx.TERMINAL_SOURCE_MODEL_WATCHDOG
    assert mx.terminal_source(exit_code=124) == \
        mx.TERMINAL_SOURCE_EXTERNAL_TIMEOUT
    assert mx.terminal_source() == mx.TERMINAL_SOURCE_NORMAL
    # run_pilot's helper uses the same vocabulary.
    assert rp.terminal_source(timed_out=True, watchdog=False,
                              exit_code=0) == "PYTHON_TIMEOUT"
    assert rp.terminal_source(timed_out=False, watchdog=True,
                              exit_code=1) == "MODEL_INTERNAL_WATCHDOG"
    assert rp.terminal_source(timed_out=False, watchdog=False,
                              exit_code=124) == "EXTERNAL_TIMEOUT"
    assert rp.terminal_source(timed_out=False, watchdog=False,
                              exit_code=0) == "NORMAL"


def test_model_watchdog_is_a_valid_terminal_not_a_timeout(tmp_path):
    out = make_run(tmp_path, model="A03", role="fault", model_log=False,
                   watchdog_marker=True)
    validation, status = _status(
        "A03", out, terminal="HANG_WATCHDOG", oracle_pass=False, exit_code=1)
    assert validation["partial"] is True
    assert validation["status"] == mx.PREFLIGHT_OK
    assert status == mx.STATUS_COMPLETED
    assert mx.campaign_exit_code([{"status": status}]) == 0


def test_rp01_partial_watchdog_outputs_are_accepted(tmp_path):
    out = make_run(tmp_path, model="RP01", role="fault", model_log=False,
                   watchdog_marker=True)
    validation = mx.validate_outputs("RP01", out, role="fault")
    assert validation["partial"] is True
    assert validation["status"] == mx.PREFLIGHT_OK
    assert mx.watchdog_marker_present(out, "RP01") is True


# ---------------------------------------------------------------------------
# 6. ORACLE_FAIL is recorded but is not a runner failure
# ---------------------------------------------------------------------------
def test_oracle_fail_is_recorded_but_not_a_runner_failure(tmp_path):
    out = make_run(tmp_path, terminal="SDC", oracle_pass=False)
    validation, status = _status(
        "A01", out, terminal="SDC", oracle_pass=False, exit_code=0)
    assert validation["status"] == mx.PREFLIGHT_OK
    assert status == mx.STATUS_ORACLE_FAIL
    assert mx.campaign_exit_code([{"status": status}]) == 0
    record = mx.campaign_record(
        campaign_id=mx.CAMPAIGN_ID_DEFAULT, model="A01", context="R01",
        role="fault", sample_run_id="SR-000001", seed=1234,
        status=status, binary_sha="b", config_sha="c", elf_sha="e",
        started_at="2026-11-12T00:00:00+00:00",
        ended_at="2026-11-12T00:00:01+00:00", exit_code=0,
        timed_out=False, terminal_source=mx.TERMINAL_SOURCE_NORMAL)
    mx.write_campaign_json(out, record)
    on_disk = json.loads((out / "campaign.json").read_text())
    assert on_disk["status"] == "ORACLE_FAIL"
    assert on_disk["campaign_id"] == mx.CAMPAIGN_ID_DEFAULT


def test_control_oracle_fail_is_a_runner_failure(tmp_path):
    out = make_run(tmp_path, role="control", terminal="SDC", oracle_pass=False)
    _validation, status = _status(
        "A01", out, role="control", terminal="SDC", oracle_pass=False,
        exit_code=0)
    assert status == mx.STATUS_FAILED


def test_fault_crash_by_fault_is_a_valid_terminal(tmp_path):
    out = make_run(tmp_path, terminal="CRASH", oracle_pass=False)
    _validation, status = _status(
        "A01", out, terminal="CRASH", oracle_pass=False, exit_code=1,
        crash_by_fault=True)
    # run_pilot records crash_evidence for a genuine fault-induced crash.
    assert status == mx.STATUS_COMPLETED


def test_plain_crash_is_failed(tmp_path):
    out = make_run(tmp_path, terminal="CRASH", oracle_pass=False)
    _validation, status = _status(
        "A01", out, terminal="CRASH", oracle_pass=False, exit_code=1)
    assert status == mx.STATUS_FAILED


# ---------------------------------------------------------------------------
# 7. Partial success -> nonzero campaign exit
# ---------------------------------------------------------------------------
def test_partial_success_is_nonzero_and_summary_counts(tmp_path):
    rows = [{"status": mx.STATUS_COMPLETED},
            {"status": mx.STATUS_OUTPUT_INCOMPLETE}]
    assert mx.campaign_exit_code(rows) == 1
    counts = mx.status_summary(rows)
    assert counts[mx.STATUS_COMPLETED] == 1
    assert counts[mx.STATUS_OUTPUT_INCOMPLETE] == 1


def test_hash_mismatch_and_failed_are_nonzero():
    for status in (mx.STATUS_FAILED, mx.STATUS_TIMEOUT,
                   mx.STATUS_OUTPUT_INCOMPLETE, mx.STATUS_HASH_MISMATCH):
        assert mx.campaign_exit_code([{"status": status}]) == 1, status
        assert mx.campaign_exit_code(
            [{"status": mx.STATUS_COMPLETED}, {"status": status}]) == 1


# ---------------------------------------------------------------------------
# 8. campaign.json interface
# ---------------------------------------------------------------------------
CAMPAIGN_FIELDS = {
    "campaign_id", "model", "context", "role", "sample_run_id", "seed",
    "status", "binary_sha", "config_sha", "elf_sha", "started_at",
    "ended_at", "exit_code", "timed_out", "terminal_source",
}


def test_campaign_record_has_the_collector_interface_fields(tmp_path):
    record = mx.campaign_record(
        campaign_id="LSU-V333-FORMAL-20261112", model="A01", context="R01",
        role="fault", sample_run_id="SR-000001", seed=1234,
        status=mx.STATUS_COMPLETED, binary_sha="b" * 64,
        config_sha="c" * 64, elf_sha="e" * 64,
        started_at="2026-11-12T00:00:00+00:00",
        ended_at="2026-11-12T00:00:10+00:00", exit_code=0, timed_out=False,
        terminal_source=mx.TERMINAL_SOURCE_NORMAL)
    assert CAMPAIGN_FIELDS <= set(record)
    assert record["timed_out"] is False
    path = mx.write_campaign_json(tmp_path, record)
    assert path.name == "campaign.json"
    assert json.loads(path.read_text())["sample_run_id"] == "SR-000001"


# ---------------------------------------------------------------------------
# 9. Matrix main: exit code and per-status summary; campaign id threading
# ---------------------------------------------------------------------------
@pytest.fixture
def preserve_matrix_globals():
    """main() mutates module globals; restore them so suites stay isolated."""
    names = ("OUT_BASE", "SUMMARY_CSV", "FORCE", "EXPECTED_BINARY_SHA",
             "EXPECTED_CONFIG_SHA", "EXPECTED_ELF_SHA")
    saved = {name: getattr(mx, name) for name in names}
    yield
    for name, value in saved.items():
        setattr(mx, name, value)


def test_matrix_main_failure_row_makes_the_campaign_exit_nonzero(
        monkeypatch, tmp_path, capsys, preserve_matrix_globals):
    seen_ids = []

    def fake_run(model, ctx, role, campaign_id=None):
        seen_ids.append(campaign_id)
        status = (mx.STATUS_FAILED if model == "FW02"
                  else mx.STATUS_COMPLETED)
        return {"model": model, "context": f"R{ctx:02d}", "role": role,
                "status": status}

    monkeypatch.setattr(mx, "run_context", fake_run)
    monkeypatch.setattr(mx, "matrix_lock", lambda *a, **k: nullcontext())
    rc = mx.main(["--models", "A01,FW02", "--roles", "fault",
                  "--contexts", "1", "--out-base", str(tmp_path),
                  "--out-csv", str(tmp_path / "rows.csv"),
                  "--campaign-id", "LSU-TEST-1"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "status summary:" in out
    assert "FAILED=1" in out
    assert seen_ids == ["LSU-TEST-1", "LSU-TEST-1"]


def test_matrix_main_all_completed_exits_zero(monkeypatch, tmp_path,
                                              preserve_matrix_globals):
    def fake_run(model, ctx, role, campaign_id=None):
        return {"model": model, "context": f"R{ctx:02d}", "role": role,
                "status": mx.STATUS_COMPLETED}

    monkeypatch.setattr(mx, "run_context", fake_run)
    monkeypatch.setattr(mx, "matrix_lock", lambda *a, **k: nullcontext())
    rc = mx.main(["--models", "A01", "--roles", "fault", "--contexts", "1",
                  "--out-base", str(tmp_path),
                  "--out-csv", str(tmp_path / "rows.csv")])
    assert rc == 0


# ---------------------------------------------------------------------------
# 10. run_pilot: parse failure / runner error => nonzero, no fake acceptance
# ---------------------------------------------------------------------------
def test_run_pilot_parse_or_runner_error_is_nonzero():
    ok = {"status": "OK", "required": [], "missing": []}
    assert rp.acceptance_exit_code(True, ok, parse_error="KeyError('x')") == 1
    assert rp.acceptance_exit_code(True, ok, runner_error="OSError") == 1
    assert rp.acceptance_exit_code(False, ok) == 1


def test_run_pilot_missing_trace_is_not_accepted(tmp_path):
    out = tmp_path / "rp"
    out.mkdir()
    (out / "command.txt").write_text("cmd")
    (out / "oracle.log").write_text("PASS")
    (out / MODEL_LOG["A01"]).write_text("log")
    validation = rp.output_validation(out, "A01", 1.0)
    assert validation["status"] == "OUTPUT_INCOMPLETE"
    assert "prop_trace.csv.gz" in validation["missing"]
    assert rp.acceptance_exit_code(True, validation) == 1


def test_run_pilot_control_does_not_require_an_injector_log(tmp_path):
    out = tmp_path / "rp"
    out.mkdir()
    for name in ("command.txt", "prop_trace.csv.gz", "oracle.log"):
        (out / name).write_text("x")
    validation = rp.output_validation(out, "FW02", 0.0)
    assert validation["status"] == "OK", validation


def test_run_pilot_parse_helper_is_wired_into_main():
    import inspect
    src = inspect.getsource(rp.main)
    assert "_parse_model_events(" in src
    assert "output_validation(" in src
    assert "acceptance_exit_code(" in src
    # The fault acceptance gate itself never consults oracle_pass: a fault
    # whose oracle FAILs (SDC) remains an accepted measured run.
    gate = src.split("fault_valid = (", 1)[1].split(")", 1)[0]
    assert "oracle_pass" not in gate


# ---------------------------------------------------------------------------
# 11. run_context wiring: provisional RUNNING -> terminal status + campaign.json
# ---------------------------------------------------------------------------
def _fake_preflight_ok(**kwargs):
    return {
        "status": mx.PREFLIGHT_OK, "ok": True,
        "model": kwargs["model"], "role": kwargs["role"],
        "evidence": {"checks": {}, "missing": [], "sha_mismatches": [],
                     "observed_sha": {}, "expected_sha": {}},
        "binary_sha": "b" * 64, "config_sha": "c" * 64, "elf_sha": "e" * 64,
    }


def _make_fake_run(write_outputs=True, timed_out=False, pid=4321,
                   inner_timeout=False):
    def fake_run(cmd, *, outdir, timeout, cwd=None,
                 stdout_name="stdout.log", stderr_name="stderr.log"):
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        if write_outputs:
            (outdir / "trace_v31.jsonl").write_text("")
            (outdir / "prop_trace.csv.gz").write_bytes(b"")
            (outdir / "oracle.log").write_text("PASS\n")
            (outdir / MODEL_LOG["A01"]).write_text(
                "FUNNEL: attempted=1 eligible=1 injected=1\n")
            (outdir / "pilot_meta.json").write_text(json.dumps({
                "model": "A01", "seed": 1234, "injection_count": 1,
                "oracle_pass": True, "terminal": "MASKED",
                "exit_code": 124 if (timed_out or inner_timeout) else 0,
                "classification": {
                    "terminal_state": "MASKED",
                    "terminal_state_reason": "ORACLE_PASS",
                    "run_status": ("TIMEOUT" if (timed_out or inner_timeout)
                                   else "COMPLETED")},
                "injection": {"events": 1}, "trace": {}}))
        (outdir / stdout_name).write_text("")
        (outdir / stderr_name).write_text(
            "TIMEOUT: external wall-clock limit reached\n"
            if (timed_out or inner_timeout) else "")
        return {"cmd": cmd, "pid": pid,
                "exit_code": 124 if timed_out else (1 if inner_timeout else 0),
                "timed_out": timed_out, "elapsed": 0.1,
                "started_at": "2026-11-12T00:00:00+00:00",
                "ended_at": "2026-11-12T00:00:01+00:00",
                "status": mx.STATUS_TIMEOUT if timed_out else None,
                "stdout": "", "stderr": ""}
    return fake_run


def test_run_context_writes_completed_campaign(monkeypatch, tmp_path):
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "run_subprocess", _make_fake_run())
    row = mx.run_context("A01", 1, "fault")
    out = tmp_path / "A01-R01-fault"
    assert row["status"] == mx.STATUS_COMPLETED
    assert row["terminal_source"] == mx.TERMINAL_SOURCE_NORMAL
    record = json.loads((out / "campaign.json").read_text())
    assert record["status"] == mx.STATUS_COMPLETED
    assert record["campaign_id"] == mx.CAMPAIGN_ID_DEFAULT
    assert record["sample_run_id"]
    assert record["seed"] is not None
    assert record["binary_sha"] == "b" * 64
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == mx.STATUS_COMPLETED
    assert summary["pid"] == 4321


def test_run_context_timeout_is_recorded_as_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "run_subprocess",
                        _make_fake_run(timed_out=True))
    row = mx.run_context("A01", 1, "fault")
    out = tmp_path / "A01-R01-fault"
    record = json.loads((out / "campaign.json").read_text())
    assert row["status"] == mx.STATUS_TIMEOUT
    assert record["status"] == mx.STATUS_TIMEOUT
    assert record["timed_out"] is True
    assert record["exit_code"] == 124
    assert record["terminal_source"] == mx.TERMINAL_SOURCE_PYTHON_TIMEOUT
    assert mx.campaign_exit_code([row]) == 1


def test_run_context_inner_runner_timeout_is_external(monkeypatch, tmp_path):
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "run_subprocess",
                        _make_fake_run(inner_timeout=True))
    row = mx.run_context("A01", 1, "fault")
    out = tmp_path / "A01-R01-fault"
    record = json.loads((out / "campaign.json").read_text())
    assert row["status"] == mx.STATUS_TIMEOUT
    assert record["exit_code"] == 124
    # run_pilot's internal wall-clock timeout is external to this driver.
    assert record["terminal_source"] == mx.TERMINAL_SOURCE_EXTERNAL_TIMEOUT
    assert record["timed_out"] is False


def test_run_context_missing_trace_is_output_incomplete(monkeypatch, tmp_path):
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "run_subprocess",
                        _make_fake_run(write_outputs=False))
    row = mx.run_context("A01", 1, "fault")
    assert row["status"] == mx.STATUS_OUTPUT_INCOMPLETE
    assert mx.campaign_exit_code([row]) == 1


def test_run_context_preflight_failure_never_runs(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path)
    monkeypatch.setattr(mx, "preflight_task", lambda **kw: {
        "status": mx.STATUS_HASH_MISMATCH, "ok": False,
        "model": kw["model"], "role": kw["role"],
        "evidence": {"checks": {}, "missing": [], "sha_mismatches": ["binary"],
                     "observed_sha": {}, "expected_sha": {}},
        "binary_sha": "f" * 64, "config_sha": None, "elf_sha": None})
    monkeypatch.setattr(mx, "run_subprocess",
                        lambda *a, **k: called.append(1))
    row = mx.run_context("A01", 1, "fault")
    assert row["status"] == mx.STATUS_HASH_MISMATCH
    assert called == []
    out = tmp_path / "A01-R01-fault"
    assert json.loads((out / "campaign.json").read_text())["status"] == \
        mx.STATUS_HASH_MISMATCH
    assert not (out / "summary.json").exists()
