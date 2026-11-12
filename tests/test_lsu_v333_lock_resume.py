"""LSU v3.3.3 campaign lock, attempt isolation, resume and dry-run gates.

Everything here runs on synthetic directories under ``tmp_path``.  gem5 is
never invoked: the one execution seam (``mx.run_subprocess``) is replaced,
and the dry-run test additionally patches ``subprocess.run/Popen`` to raise.
No test writes inside ``runs/lsu/formal_v333_final_20261112``.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import lsu_campaign_lock as cl  # noqa: E402
import lsu_run_state as rs  # noqa: E402
import lsu_v332_matrix as mx  # noqa: E402

CAMPAIGN = "LSU-V333-FINAL-20261112"


@pytest.fixture
def preserve_matrix_globals():
    names = ("OUT_BASE", "SUMMARY_CSV", "FORCE", "EXPECTED_BINARY_SHA",
             "EXPECTED_CONFIG_SHA", "EXPECTED_ELF_SHA")
    saved = {name: getattr(mx, name) for name in names}
    yield
    for name, value in saved.items():
        setattr(mx, name, value)


# ---------------------------------------------------------------------------
# Lock: metadata, contention, stale rules, path binding
# ---------------------------------------------------------------------------
def test_lock_acquired_metadata_fields(tmp_path):
    out = tmp_path / "campaign"
    with cl.campaign_lock(out, "LSU-TEST-1") as record:
        data = json.loads((out / cl.LOCK_NAME).read_text())
        assert data["pid"] == os.getpid()
        assert data["hostname"] == socket.gethostname()
        assert data["campaign_id"] == "LSU-TEST-1"
        assert data["out_base"] == str(out)
        assert data["started_at"]
        assert record["pid"] == os.getpid()
        assert record["campaign_id"] == "LSU-TEST-1"
    # Released: the same process may reacquire its own campaign.
    with cl.campaign_lock(out, "LSU-TEST-1"):
        pass


_CHILD = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from lsu_campaign_lock import campaign_lock, LockHeld

try:
    with campaign_lock(Path(sys.argv[1]), sys.argv[2]):
        print("ACQUIRED", flush=True)
except LockHeld as exc:
    print("LOCK_HELD", exc, flush=True)
    sys.exit(3)
"""


def _child_acquire(out_base, campaign_id):
    return subprocess.run(
        [sys.executable, "-c", _CHILD, str(out_base), campaign_id,
         str(TOOLS)],
        capture_output=True, text=True, timeout=60)


def test_second_waiter_child_process_is_refused(tmp_path):
    out = tmp_path / "campaign"
    with cl.campaign_lock(out, "LSU-C1"):
        same = _child_acquire(out, "LSU-C1")
        other = _child_acquire(out, "LSU-C2")
    assert same.returncode == 3, (same.returncode, same.stdout, same.stderr)
    assert "LOCK_HELD" in same.stdout
    # A different campaign id on the SAME root is refused just as hard.
    assert other.returncode == 3, (other.returncode, other.stdout,
                                   other.stderr)
    assert "LOCK_HELD" in other.stdout
    # After release the SAME campaign is re-acquirable, while a *different*
    # campaign still sees live-owner metadata (this process is alive) and stays
    # fail-closed until that metadata is reclaimed/archived.
    stale = _child_acquire(out, "LSU-C2")
    assert stale.returncode == 3, (stale.returncode, stale.stdout)
    assert "LOCK_HELD" in stale.stdout
    ok = _child_acquire(out, "LSU-C1")
    assert ok.returncode == 0, (ok.returncode, ok.stdout, ok.stderr)
    assert "ACQUIRED" in ok.stdout


def _dead_pid() -> int:
    for pid in range(3_999_999, 3_990_000, -1):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return pid
        except PermissionError:
            continue
    raise AssertionError("no dead pid found")   # pragma: no cover


def test_dead_pid_stale_lock_is_reclaimed_with_archive(tmp_path):
    out = tmp_path / "campaign"
    out.mkdir()
    dead = _dead_pid()
    (out / cl.LOCK_NAME).write_text(json.dumps({
        "pid": dead, "hostname": socket.gethostname(),
        "started_at": "2026-11-01T00:00:00+00:00",
        "campaign_id": "LSU-OLD", "out_base": str(out)}))
    with cl.campaign_lock(out, "LSU-NEW") as record:
        assert record["campaign_id"] == "LSU-NEW"
        assert json.loads((out / cl.LOCK_NAME).read_text())["pid"] == \
            os.getpid()
    archived = sorted((out / cl.STALE_DIR).glob("*.json"))
    assert archived, "stale lock metadata must be archived"
    payload = json.loads(archived[0].read_text())
    assert payload["pid"] == dead
    assert payload["campaign_id"] == "LSU-OLD"
    assert payload["stale_reason"]
    assert payload["observed_pid_alive"] is False


def test_live_pid_foreign_campaign_metadata_fails_closed(tmp_path):
    """A free flock with a live foreign-campaign pid is NOT stomped."""
    out = tmp_path / "campaign"
    out.mkdir()
    (out / cl.LOCK_NAME).write_text(json.dumps({
        "pid": os.getpid(), "hostname": socket.gethostname(),
        "started_at": "2026-11-01T00:00:00+00:00",
        "campaign_id": "LSU-OTHER", "out_base": str(out)}))
    with pytest.raises(cl.LockHeld):
        with cl.campaign_lock(out, "LSU-MINE"):
            pass


def test_lock_path_follows_out_base_and_has_no_default_binding(tmp_path):
    import inspect
    sig = inspect.signature(cl.campaign_lock)
    assert all(param.default is inspect.Parameter.empty
               for param in sig.parameters.values()), sig
    # The old defect: a module-level default bound runs/lsu/formal_v333.
    source = (TOOLS / "lsu_v332_matrix.py").read_text()
    assert "def matrix_lock(path: Path = LOCK_FILE)" not in source
    root_a = tmp_path / "campaign-a"
    root_b = tmp_path / "campaign-b"
    with cl.campaign_lock(root_a, "LSU-A"):
        pass
    with cl.campaign_lock(root_b, "LSU-B"):
        pass
    assert cl.lock_path(root_a) == root_a / cl.LOCK_NAME
    assert (root_a / cl.LOCK_NAME).is_file()
    assert (root_b / cl.LOCK_NAME).is_file()
    assert not (root_a / cl.LOCK_NAME).is_symlink()


def test_force_does_not_bypass_the_lock(tmp_path, monkeypatch, capsys,
                                        preserve_matrix_globals):
    runs = tmp_path / "campaign"
    runs.mkdir()
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    with cl.campaign_lock(runs, CAMPAIGN):
        rc = mx.main(["--models", "A01", "--contexts", "1", "--roles",
                      "fault", "--out-base", str(runs), "--out-csv",
                      str(tmp_path / "raw.csv"), "--campaign-id", CAMPAIGN,
                      "--resume", "--force"])
    captured = capsys.readouterr()
    assert rc == 3, (rc, captured.out, captured.err)
    assert "LOCK_HELD" in captured.err


# ---------------------------------------------------------------------------
# Runner seam: synthetic execution
# ---------------------------------------------------------------------------
def _fake_preflight_ok(**kwargs):
    return {
        "status": mx.PREFLIGHT_OK, "ok": True,
        "model": kwargs["model"], "role": kwargs["role"],
        "evidence": {"checks": {}, "missing": [], "sha_mismatches": [],
                     "observed_sha": {}, "expected_sha": {}},
        "binary_sha": "b" * 64, "config_sha": "c" * 64, "elf_sha": "e" * 64,
    }


def _success_outputs(outdir: Path) -> None:
    (outdir / "trace_v31.jsonl").write_text("")
    (outdir / "prop_trace.csv.gz").write_bytes(b"")
    (outdir / "oracle.log").write_text("PASS\n")
    (outdir / mx.MODEL_LOG_NAME["A01"]).write_text(
        "FUNNEL: attempted=1 eligible=1 injected=1\n")
    (outdir / "pilot_meta.json").write_text(json.dumps({
        "model": "A01", "seed": 2108120075, "injection_count": 1,
        "oracle_pass": True, "terminal": "MASKED", "exit_code": 0,
        "classification": {"terminal_state": "MASKED",
                           "terminal_state_reason": "ORACLE_PASS",
                           "run_status": "COMPLETED"},
        "injection": {"events": 1}, "trace": {}}))


def _install_runner(monkeypatch, calls, behaviour):
    def fake(cmd, *, outdir, timeout, cwd=None, stdout_name="stdout.log",
             stderr_name="stderr.log", **_kwargs):
        calls.append([str(c) for c in cmd])
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        behaviour(outdir)
        (outdir / stdout_name).write_text("")
        (outdir / stderr_name).write_text("")
        return {"cmd": [str(c) for c in cmd], "pid": 4321, "exit_code": 0,
                "timed_out": False, "elapsed": 0.01, "started_at": "",
                "ended_at": "", "status": None, "stdout": "", "stderr": ""}
    monkeypatch.setattr(mx, "run_subprocess", fake)


def _runner_env(tmp_path, monkeypatch):
    runs = tmp_path / "campaign"
    monkeypatch.setattr(mx, "OUT_BASE", runs)
    monkeypatch.setattr(mx, "FORCE", False)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    return runs


def _no_outputs(_outdir: Path) -> None:
    return None


def test_retry_creates_attempt_002_and_keeps_attempt_001_bytes(
        tmp_path, monkeypatch):
    runs = _runner_env(tmp_path, monkeypatch)
    calls = []
    _install_runner(monkeypatch, calls, _no_outputs)
    first = mx.run_context("A01", 1, "fault")
    assert first["status"] == mx.STATUS_OUTPUT_INCOMPLETE, first["status"]
    run_dir = runs / "A01-R01-fault"
    a1 = run_dir / "attempts" / "attempt_001"
    assert a1.is_dir()
    snapshot = {p.name: p.read_bytes() for p in a1.iterdir() if p.is_file()}
    assert snapshot

    _install_runner(monkeypatch, calls, _success_outputs)
    second = mx.run_context("A01", 1, "fault")
    assert second["status"] == mx.STATUS_COMPLETED, second["status"]
    a2 = run_dir / "attempts" / "attempt_002"
    assert a2.is_dir()
    for name, data in snapshot.items():
        assert (a1 / name).read_bytes() == data, name
    assert len(calls) == 2

    canonical = json.loads((run_dir / "canonical.json").read_text())
    assert canonical["attempt_id"] == "attempt_002"
    # The run-dir convenience view now points at the canonical attempt.
    assert (run_dir / "summary.json").is_symlink()
    assert os.readlink(run_dir / "summary.json") == \
        "attempts/attempt_002/summary.json"
    assert json.loads((run_dir / "summary.json").read_text())["status"] == \
        mx.STATUS_COMPLETED


def test_default_raw_csv_follows_out_base(tmp_path, monkeypatch,
                                          preserve_matrix_globals):
    runs = tmp_path / "campaign"
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    _install_runner(monkeypatch, [], _success_outputs)
    rc = mx.main(["--models", "A01", "--contexts", "1", "--roles", "fault",
                  "--out-base", str(runs), "--campaign-id", "LSU-CSV"])
    assert rc == 0
    csv_path = runs / "LSU_Fault_Control_Pair_RAW.csv"
    assert csv_path.is_file()
    assert csv_path.read_text().startswith("model,context,role,")


def test_duplicate_submission_creates_no_second_attempt(tmp_path, monkeypatch):
    runs = _runner_env(tmp_path, monkeypatch)
    calls = []
    _install_runner(monkeypatch, calls, _success_outputs)
    first = mx.run_context("A01", 1, "fault")
    assert first["status"] == mx.STATUS_COMPLETED
    second = mx.run_context("A01", 1, "fault")
    assert second["status"] == mx.STATUS_FAILED
    assert "outdir_unique" in second["error"]
    assert len(calls) == 1
    attempts = sorted(p.name for p in
                      (runs / "A01-R01-fault" / "attempts").iterdir())
    assert attempts == ["attempt_001"]


# ---------------------------------------------------------------------------
# Resume state machine
# ---------------------------------------------------------------------------
def _make_task(runs: Path, *, model="A01", ctx=1, role="fault",
               campaign=CAMPAIGN, status=rs.STATUS_COMPLETED,
               canonical=True, summaries=True, attempt_id="attempt_001"):
    run_dir = runs / rs.task_tag(model, ctx, role)
    adir = rs.attempt_dir(run_dir, attempt_id)
    adir.mkdir(parents=True, exist_ok=True)
    if summaries:
        (adir / "summary.json").write_text(json.dumps({
            "model": model, "status": status, "terminal": "MASKED",
            "sample_run_id": f"SR-{model}-{ctx}", "seed": 1234}))
    (adir / "campaign.json").write_text(json.dumps({
        "campaign_id": campaign, "status": status,
        "sample_run_id": f"SR-{model}-{ctx}", "seed": 1234}))
    rs.write_attempt_record(adir, {
        "attempt_id": attempt_id, "campaign_id": campaign, "model": model,
        "context": f"R{ctx:02d}", "role": role, "status": status,
        "sample_run_id": f"SR-{model}-{ctx}", "seed": 1234})
    if canonical:
        rs.write_canonical(run_dir, {
            "campaign_id": campaign, "attempt_id": attempt_id, "model": model,
            "context": f"R{ctx:02d}", "role": role, "status": status,
            "sample_run_id": f"SR-{model}-{ctx}", "seed": 1234})
    return run_dir, adir


def _resume_main(runs, tmp_path, campaign=CAMPAIGN):
    return mx.main(["--models", "A01", "--contexts", "1", "--roles",
                    "fault", "--out-base", str(runs), "--out-csv",
                    str(tmp_path / "raw.csv"), "--campaign-id", campaign,
                    "--resume"])


def test_resume_completed_is_skipped_without_execution(
        tmp_path, monkeypatch, capsys, preserve_matrix_globals):
    runs = tmp_path / "campaign"
    run_dir, _adir = _make_task(runs)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    # Any execution attempt would be a hard failure.
    monkeypatch.setattr(mx, "run_context",
                        lambda *a, **k: pytest.fail("resume executed a task"))
    rc = _resume_main(runs, tmp_path)
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "resumed; no execution" in out
    assert not (run_dir / "attempts" / "attempt_002").exists()
    index = json.loads((runs / "campaign_index.json").read_text())
    assert index["campaign_id"] == CAMPAIGN
    entry = index["tasks"][0]
    assert entry["state"] == rs.STATUS_COMPLETED
    assert entry["attempt_id"] == "attempt_001"
    assert entry["canonical_attempt_id"] == "attempt_001"
    assert index["counts"]["COMPLETED"] == 1


def test_resume_hash_mismatch_refuses_to_retry(
        tmp_path, monkeypatch, capsys, preserve_matrix_globals):
    runs = tmp_path / "campaign"
    run_dir = runs / "A01-R01-fault"
    adir = rs.attempt_dir(run_dir, "attempt_001")
    adir.mkdir(parents=True)
    (adir / "campaign.json").write_text(json.dumps(
        {"campaign_id": CAMPAIGN, "status": rs.STATUS_HASH_MISMATCH}))
    rs.write_attempt_record(adir, {
        "attempt_id": "attempt_001", "campaign_id": CAMPAIGN,
        "model": "A01", "context": "R01", "role": "fault",
        "status": rs.STATUS_HASH_MISMATCH, "reason": "BINARY_SHA_MISMATCH"})
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    monkeypatch.setattr(mx, "run_context",
                        lambda *a, **k: pytest.fail("hash mismatch retried"))
    rc = _resume_main(runs, tmp_path)
    captured = capsys.readouterr()
    assert rc == 2, (rc, captured.out, captured.err)
    assert "RESUME REFUSED" in captured.err
    assert not (run_dir / "attempts" / "attempt_002").exists()
    assert rs.read_canonical(run_dir) is None


def test_resume_oracle_fail_is_never_retried_or_replaced(
        tmp_path, monkeypatch, capsys, preserve_matrix_globals):
    runs = tmp_path / "campaign"
    run_dir, adir = _make_task(runs, status=rs.STATUS_ORACLE_FAIL)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    monkeypatch.setattr(mx, "run_context",
                        lambda *a, **k: pytest.fail("ORACLE_FAIL re-executed"))
    rc = _resume_main(runs, tmp_path)
    assert rc == 0
    canonical = rs.read_canonical(run_dir)
    assert canonical["attempt_id"] == "attempt_001"
    assert canonical["status"] == rs.STATUS_ORACLE_FAIL
    assert not (run_dir / "attempts" / "attempt_002").exists()
    assert adir.is_dir()


def test_resume_repairs_missing_canonical_without_execution(
        tmp_path, monkeypatch, preserve_matrix_globals):
    runs = tmp_path / "campaign"
    run_dir, _adir = _make_task(runs, canonical=False)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    monkeypatch.setattr(mx, "run_context",
                        lambda *a, **k: pytest.fail("crash-window repair ran"))
    rc = _resume_main(runs, tmp_path)
    assert rc == 0
    canonical = rs.read_canonical(run_dir)
    assert canonical["attempt_id"] == "attempt_001"
    assert canonical["registration"] == "RESUME_REPAIR"


def test_resume_failed_task_creates_a_new_attempt(
        tmp_path, monkeypatch, capsys, preserve_matrix_globals):
    runs = tmp_path / "campaign"
    run_dir, a1 = _make_task(runs, status=rs.STATUS_FAILED, canonical=False,
                             summaries=False)
    monkeypatch.setattr(mx, "_sha256", lambda _p: "f" * 64)
    monkeypatch.setattr(mx, "preflight_task", _fake_preflight_ok)
    calls = []
    _install_runner(monkeypatch, calls, _success_outputs)
    rc = _resume_main(runs, tmp_path)
    assert rc == 0, capsys.readouterr()
    assert len(calls) == 1
    a2 = rs.attempt_dir(run_dir, "attempt_002")
    assert a2.is_dir() and a1.is_dir()
    assert rs.read_canonical(run_dir)["attempt_id"] == "attempt_002"


def test_two_completed_attempts_keep_the_first_canonical(tmp_path):
    runs = tmp_path / "campaign"
    run_dir, a1 = _make_task(runs)
    a2 = rs.attempt_dir(run_dir, "attempt_002")
    a2.mkdir()
    (a2 / "summary.json").write_text(json.dumps({"status": "COMPLETED"}))
    (a2 / "campaign.json").write_text(json.dumps(
        {"campaign_id": CAMPAIGN, "status": "COMPLETED"}))
    rs.write_attempt_record(a2, {
        "attempt_id": "attempt_002", "campaign_id": CAMPAIGN,
        "model": "A01", "context": "R01", "role": "fault",
        "status": rs.STATUS_COMPLETED})
    state = rs.scan_task_state(run_dir, CAMPAIGN,
                               required_outputs=mx.RESUME_REQUIRED)
    assert state["state"] == rs.STATUS_COMPLETED
    assert state["attempt_id"] == "attempt_001"
    assert rs.canonical_dir(run_dir) == a1
    assert a1.is_dir() and a2.is_dir()      # both attempts are preserved
    with pytest.raises(RuntimeError):
        rs.write_canonical(run_dir, {"campaign_id": CAMPAIGN,
                                     "attempt_id": "attempt_002"})


# ---------------------------------------------------------------------------
# Atomic campaign index
# ---------------------------------------------------------------------------
def test_index_never_marks_completed_before_the_summary_exists(tmp_path):
    runs = tmp_path / "campaign"
    run_dir = runs / "A01-R01-fault"
    adir = rs.attempt_dir(run_dir, "attempt_001")
    adir.mkdir(parents=True)
    (adir / "campaign.json").write_text(json.dumps(
        {"campaign_id": CAMPAIGN, "status": "COMPLETED"}))
    # terminal record written, but the summary was never flushed
    rs.write_attempt_record(adir, {
        "attempt_id": "attempt_001", "campaign_id": CAMPAIGN,
        "model": "A01", "context": "R01", "role": "fault",
        "status": rs.STATUS_COMPLETED})
    index = mx.build_campaign_index(runs, CAMPAIGN, [("A01", 1, "fault")])
    entry = index["tasks"][0]
    assert entry["state"] == rs.STATUS_OUTPUT_INCOMPLETE
    assert "MISSING_OUTPUT:summary.json" in (entry["reason"] or "")
    assert index["counts"]["COMPLETED"] == 0
    path = mx.write_campaign_index(runs, index)
    assert json.loads(path.read_text())["tasks"][0]["state"] == \
        rs.STATUS_OUTPUT_INCOMPLETE
    assert not list(path.parent.glob("campaign_index.json.tmp*"))


# ---------------------------------------------------------------------------
# Dry-run: 120-task gates; never creates the campaign root, never runs gem5
# ---------------------------------------------------------------------------
DRY_ARGS = ["--models", "all", "--roles", "fault,control",
            "--contexts", "1,2,3,4,5", "--campaign-id", CAMPAIGN,
            "--expected-binary-sha", mx.EXPECTED_BINARY_SHA256,
            "--expected-config-sha", mx.EXPECTED_CONFIG_SHA256,
            "--dry-run"]


def _summary_from(stdout: str) -> dict:
    line = [ln for ln in stdout.splitlines()
            if ln.startswith("DRY_RUN_SUMMARY ")][0]
    return json.loads(line.split(" ", 1)[1])


def test_dry_run_120_task_matrix_is_ready(tmp_path, monkeypatch, capsys,
                                          preserve_matrix_globals):
    def _boom(*_a, **_k):
        raise AssertionError("dry-run must not spawn a subprocess")

    out = tmp_path / "formal-campaign"
    monkeypatch.setattr(mx.subprocess, "run", _boom)
    monkeypatch.setattr(mx.subprocess, "Popen", _boom)
    rc = mx.main(DRY_ARGS + ["--out-base", str(out)])
    captured = capsys.readouterr()
    assert rc == 0, (rc, captured.err)
    assert captured.out.count("DRY-RUN ") == 120
    assert "READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES" in captured.out
    gate = _summary_from(captured.out)
    assert gate["task_count"] == 120
    assert gate["unique_task_count"] == 120 and gate["unique_tasks"]
    assert gate["unique_sample_run_ids"] == 60 and gate["sample_run_ids_ok"]
    assert gate["unique_seeds"] == 60 and gate["seeds_ok"]
    assert gate["pairing_ok"] is True
    assert gate["unique_outdirs"] == 120 and gate["unique_outdirs_ok"]
    assert gate["existing_outdir_collisions"] == 0
    assert gate["binary_sha"] == mx.EXPECTED_BINARY_SHA256
    assert gate["binary_sha_ok"] is True
    assert gate["config_sha"] == mx.EXPECTED_CONFIG_SHA256
    assert gate["config_sha_ok"] is True
    assert gate["elf_ok"] is True
    assert len(gate["elf_checks"]) == 12
    assert all(check["ok"] for check in gate["elf_checks"])
    assert gate["ok"] is True and gate["errors"] == []
    # No directory side effects whatsoever.
    assert not out.exists()


def test_dry_run_missing_workload_elf_fails(tmp_path, monkeypatch, capsys,
                                            preserve_matrix_globals):
    real = mx.resolve_workload
    missing = tmp_path / "missing_elf"
    monkeypatch.setattr(
        mx, "resolve_workload",
        lambda model, workload=None: (missing if model == "MD04"
                                      else real(model, workload)))
    out = tmp_path / "formal-campaign"
    rc = mx.main(DRY_ARGS + ["--out-base", str(out)])
    captured = capsys.readouterr()
    assert rc == 2, (rc, captured.out)
    assert "READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES" not in captured.out
    gate = _summary_from(captured.out)
    assert gate["ok"] is False
    assert gate["elf_ok"] is False
    assert any(err.startswith("ELF_SHA:MD04") for err in gate["errors"])
    assert not out.exists()


def test_dry_run_wrong_frozen_elf_sha_fails(tmp_path, monkeypatch, capsys,
                                            preserve_matrix_globals):
    table = mx.load_frozen_elf_table()
    assert table, "the frozen provenance table must parse"
    tampered = dict(table)
    tampered["agu_addrmodes"] = "0" * 64
    monkeypatch.setattr(mx, "load_frozen_elf_table", lambda path=None: tampered)
    out = tmp_path / "formal-campaign"
    rc = mx.main(DRY_ARGS + ["--out-base", str(out)])
    captured = capsys.readouterr()
    assert rc == 2
    gate = _summary_from(captured.out)
    assert gate["ok"] is False and gate["elf_ok"] is False
    assert any(err.startswith("ELF_SHA:A01") for err in gate["errors"])
    assert not out.exists()


def test_dry_run_fails_when_the_root_has_colliding_outdirs(
        tmp_path, monkeypatch, capsys, preserve_matrix_globals):
    out = tmp_path / "formal-campaign"
    (out / "A01-R01-fault").mkdir(parents=True)
    rc = mx.main(DRY_ARGS + ["--out-base", str(out)])
    captured = capsys.readouterr()
    assert rc == 2
    gate = _summary_from(captured.out)
    assert gate["ok"] is False
    assert gate["existing_outdir_collisions"] == 1
    assert any(err.startswith("EXISTING_OUTDIR:") for err in gate["errors"])
