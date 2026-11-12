#!/usr/bin/env python3
"""Agent E — synthetic fixtures and independent integration acceptance.

Every assertion runs against the tiny fixtures under
``tests/fixtures/lsu_v333_synthetic/``; no gem5 process is started and no
historical run evidence is read.  The public interfaces are the ones frozen in
``audit_launch_fix_v333/README_INTERFACES.md``:

* runner       ``tools/lsu_v332_matrix.py`` (``planned_command`` /
               ``run_context`` / ``main``, with monkeypatched subprocess)
* collector    ``tools/lsu_v333_launch.py --runs <root> --campaign-id <id>
               --design-matrix ... --design-mapping ... --manifest-only``
* control      ``lsu_v333_control_proof.classify_control_run``
* qualified    ``lsu_v333_qualified.qualified_evidence``

Modules owned by other agents may not exist yet.  Tests that depend on a
missing module skip with an explicit ``PENDING (Agent X)`` reason — they are
never silently treated as passing.  When the module exists but contradicts the
frozen interface, the test FAILS and the contradiction is reported.
"""
from __future__ import annotations

import contextlib
import csv
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).resolve().parent / "fixtures" / "lsu_v333_synthetic"
TOOLS = ROOT / "tools"
COLLECTOR = TOOLS / "lsu_v333_launch.py"

sys.path.insert(0, str(TOOLS))
import lsu_v332_matrix as mx  # noqa: E402

BINARY_SHA = ("1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea31"
              "0960b4f338")
CONFIG_SHA = ("8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b8"
              "1992cb225")

CAMPAIGN_ID = "SYNTH-V333-FORMAL"
CLEAN_ID = "SYNTH-V333-CLEAN"
PARTIAL_ID = "SYNTH-V333-PARTIAL"
HISTORICAL_ID = "SYNTH-V332-PRE-FORMAL"

# Statuses that mean "this task is evidence-complete" in the frozen vocabulary.
PASS_LIKE = {"PASS", "COMPLETED", "ORACLE_FAIL", "QUALIFIED"}
# Terminal that is a designed experiment outcome for RP01/A03, never a timeout.
WATCHDOG_TERMINALS = {"HANG_WATCHDOG", "NO_CHECKSUM"}


# ---------------------------------------------------------------------------
# module / collector discovery
# ---------------------------------------------------------------------------
def _load_module(relpath: str, owner: str, modname: str):
    path = ROOT / relpath
    if not path.exists():
        pytest.skip(f"PENDING ({owner}): {relpath} not present yet; public "
                    f"interface per audit_launch_fix_v333/README_INTERFACES.md")
    if modname in sys.modules:
        return sys.modules[modname]
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _control_mod():
    return _load_module("tools/lsu_v333_control_proof.py", "Agent C",
                        "lsu_v333_control_proof")


def _qualified_mod():
    return _load_module("tools/lsu_v333_qualified.py", "Agent D",
                        "lsu_v333_qualified")


def _collector_missing_flags():
    if not COLLECTOR.exists():
        return ["tools/lsu_v333_launch.py absent"]
    text = COLLECTOR.read_text(encoding="utf-8", errors="replace")
    return [flag for flag in ("--campaign-id", "--design-matrix",
                              "--design-mapping")
            if flag not in text]


def _run_collector(tmp_path: Path, root_name: str, campaign_id: str,
                   design_name: str) -> tuple[Path, int]:
    missing = _collector_missing_flags()
    if missing:
        pytest.skip("PENDING (Agent B): tools/lsu_v333_launch.py does not yet "
                    f"expose {missing}; collector interface is per "
                    "README_INTERFACES.md")
    mod = _load_module("tools/lsu_v333_launch.py", "Agent B",
                       "lsu_v333_launch_collector")
    out = tmp_path / f"out_{root_name}_{campaign_id}"
    argv = [
        "--runs", str(FIX / root_name),
        "--campaign-id", campaign_id,
        "--design-matrix",
        str(FIX / "design" / f"{design_name}_SAMPLE_MATRIX.csv"),
        "--design-mapping",
        str(FIX / "design" / f"{design_name}_ROI_MAPPING.csv"),
        "--out", str(out),
        "--manifest-only",
    ]
    try:
        rc = mod.main(argv)
    except SystemExit as exc:  # argparse-driven collectors exit this way
        rc = exc.code
    return out, 0 if rc is None else int(rc)


def _flatten(data):
    out = []
    if isinstance(data, dict):
        out.append(data)
        for value in data.values():
            if isinstance(value, (dict, list)):
                out.extend(_flatten(value))
    elif isinstance(data, list):
        for item in data:
            out.extend(_flatten(item))
    return out


def _records(out: Path):
    recs = []
    for path in sorted(Path(out).rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".csv":
            with open(path, newline="", encoding="utf-8") as fh:
                recs.extend(dict(row) for row in csv.DictReader(fh))
        elif path.suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            recs.extend(_flatten(data))
    return recs


_EVIDENCE_KEYS = ("Evidence", "EvidencePaths", "EvidencePath", "RunDir",
                  "run_dir", "Path", "Directory", "OutputDir", "output_dir")


def _evidence(rec) -> str:
    return " ".join(str(rec.get(k, "")) for k in _EVIDENCE_KEYS)


def _find(recs, dirname: str):
    hits = [r for r in recs if dirname in _evidence(r)]
    if hits:
        return hits
    return [r for r in recs if any(dirname in str(v) for v in r.values())]


def _first(recs, dirname: str):
    hits = _find(recs, dirname)
    assert hits, f"collector emitted no record for {dirname}"
    return hits[0]


def _status(rec) -> str:
    for key in ("Status", "status", "RunStatus", "run_status",
                "RecordStatus", "record_status", "TerminalStatus",
                "CollectorStatus"):
        value = rec.get(key)
        if value not in (None, ""):
            return str(value).strip().upper()
    return ""


def _evidence_kind(rec) -> str:
    for key in ("EvidenceKind", "evidence_kind", "EvidenceClass",
                "evidence_class"):
        value = rec.get(key)
        if value not in (None, ""):
            return str(value).strip().upper()
    return ""


def _all_text(rec) -> str:
    return " ".join(str(v) for v in rec.values()).upper()


def _assert_not_pass(rec, label: str):
    status = _status(rec)
    assert status not in PASS_LIKE, (
        f"{label}: a defective run must never be reported as {status}: {rec}")


# ---------------------------------------------------------------------------
# collector runs, one per campaign root (module scope, cheap)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def campaign_out(tmp_path_factory):
    return _run_collector(tmp_path_factory.mktemp("campaign"), "campaign",
                          CAMPAIGN_ID, "SYNTH")


@pytest.fixture(scope="module")
def clean_out(tmp_path_factory):
    return _run_collector(tmp_path_factory.mktemp("clean"), "campaign_clean",
                          CLEAN_ID, "CLEAN")


@pytest.fixture(scope="module")
def partial_out(tmp_path_factory):
    return _run_collector(tmp_path_factory.mktemp("partial"),
                          "campaign_partial", PARTIAL_ID, "PARTIAL")


@pytest.fixture(scope="module")
def historical_out(tmp_path_factory):
    return _run_collector(tmp_path_factory.mktemp("historical"),
                          "historical_evidence", CAMPAIGN_ID, "HISTORICAL")


# ===========================================================================
# 0. fixture integrity (no gem5, no other agents' modules)
# ===========================================================================
def _builder():
    path = FIX / "build_fixtures.py"
    assert path.exists(), f"fixture builder missing: {path}"
    spec = importlib.util.spec_from_file_location("lsu_v333_synth_builder",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixture_scenario_dirs_exist():
    builder = _builder()
    for scenario, (root_name, dirname, _kind) in builder.SCENARIOS.items():
        path = FIX / root_name / dirname
        assert path.is_dir(), f"missing scenario dir {scenario}: {path}"
    for (model, ctx, role) in builder.CAMPAIGN_RUNS:
        assert (FIX / "campaign" / f"{model}-{ctx}-{role}").is_dir()


def test_fixture_files_are_tiny():
    large = []
    for path in FIX.rglob("*"):
        if path.is_file() and path.suffix != ".py":
            if path.stat().st_size > 64 * 1024:
                large.append((path, path.stat().st_size))
    assert not large, f"fixtures must stay tiny: {large}"


def test_fixture_missing_files_are_really_missing():
    assert not (FIX / "campaign/A01-R02-fault/summary.json").exists()
    assert (FIX / "campaign/A01-R02-fault/campaign.json").exists()
    assert not (FIX / "campaign/A01-R03-fault/trace_v31.jsonl").exists()
    assert not (FIX / "campaign/A01-R03-control/trace_v31.jsonl").exists()
    assert (FIX / "campaign/A01-R03-fault/summary.json").exists()


def test_fixture_campaign_json_matches_campaign_ids():
    required = {"campaign_id", "model", "context", "role", "sample_run_id",
                "seed", "status", "binary_sha", "config_sha", "elf_sha",
                "started_at", "ended_at", "exit_code", "timed_out"}
    for run in sorted((FIX / "campaign").glob("*/")):
        meta = json.loads((run / "campaign.json").read_text())
        assert required <= set(meta), (run, sorted(required - set(meta)))
        assert meta["campaign_id"] == CAMPAIGN_ID, run
    for run in sorted((FIX / "historical_evidence").glob("*/")):
        meta = json.loads((run / "campaign.json").read_text())
        assert meta["campaign_id"] == HISTORICAL_ID, run


def test_fixture_gzip_trace_is_valid():
    with gzip.open(FIX / "campaign/A01-R01-fault/prop_trace.csv.gz", "rb") as fh:
        text = fh.read().decode()
    assert text.splitlines()[0] == "seq,event"
    assert "injection" in text


def test_fixture_design_matrix_matches_campaign_pairs():
    with open(FIX / "design/SYNTH_SAMPLE_MATRIX.csv", newline="",
              encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    design = {(r["FaultModelID"], r["SampleRunID"].rsplit("-", 1)[-1]): r
              for r in rows}
    pairs = {(p.name.split("-")[0], p.name.split("-")[1])
             for p in (FIX / "campaign").glob("*-fault")}
    assert set(design) == pairs
    for run in (FIX / "campaign").glob("*-fault"):
        model, ctx, _role = run.name.split("-")
        meta = json.loads((run / "campaign.json").read_text())
        assert int(design[(model, ctx)]["Seed"]) == meta["seed"], run


def test_builder_regenerates_identical_fixtures(tmp_path):
    builder = _builder()
    target = tmp_path / "regen"
    builder.build(target)

    def listing(base: Path):
        return sorted(str(p.relative_to(base)) for p in base.rglob("*")
                      if p.is_file() and p.suffix != ".py"
                      and "__pycache__" not in p.parts)

    assert listing(FIX) == listing(target)
    for rel in listing(FIX):
        src, dst = FIX / rel, target / rel
        if src.suffix == ".gz":
            assert src.read_bytes() == dst.read_bytes(), rel
        else:
            a = src.read_text(encoding="utf-8").replace(str(FIX), "<ROOT>")
            b = dst.read_text(encoding="utf-8").replace(str(target), "<ROOT>")
            assert a == b, f"fixture drift in {rel}"


# ===========================================================================
# 1. runner (tools/lsu_v332_matrix.py) — runs now
# ===========================================================================
def _seed_of(cmd) -> int | None:
    tokens = [str(c) for c in cmd]
    for flag in ("--seed", "--rng_seed", "--addrpath_rng_seed"):
        if flag in tokens:
            return int(tokens[tokens.index(flag) + 1])
    return None


def test_runner_120_tasks_unique_paired_and_non_colliding(tmp_path,
                                                          monkeypatch):
    monkeypatch.setattr(mx, "OUT_BASE", tmp_path / "runs")
    tasks = []
    for model in mx.MODELS:
        for ctx in range(1, 6):
            for role in ("fault", "control"):
                outdir = mx.OUT_BASE / f"{model}-R{ctx:02d}-{role}"
                cmd = mx.planned_command(model, ctx, role, outdir)
                tasks.append((model, ctx, role, outdir, cmd))

    assert len(tasks) == 120
    assert len({str(t[3]) for t in tasks}) == 120, "output path collision"

    for model in mx.MODELS:
        for ctx in range(1, 6):
            pair = [t for t in tasks
                    if t[0] == model and t[1] == ctx]
            assert {t[2] for t in pair} == {"fault", "control"}
            frozen_seed = int(mx.FROZEN_ID[(model, f"R{ctx:02d}")][1])
            assert _seed_of(pair[0][4]) == frozen_seed, (
                f"{model} R{ctx:02d}: fault command lost the frozen seed")
            # The RP01 control command does not take a seed flag; the pair is
            # still bound by the same FROZEN_ID[(model, ctx)] entry.  Any
            # control that does carry a seed must carry the paired one.
            assert _seed_of(pair[1][4]) in (frozen_seed, None), (
                f"{model} R{ctx:02d}: fault/control seed mismatch")

    for _model, _ctx, _role, outdir, cmd in tasks:
        assert str(outdir) in " ".join(map(str, cmd)), (
            f"task would not write its own unique outdir: {outdir}")
        joined = " ".join(map(str, cmd))
        assert "audit_v3_3_3" not in joined
        assert "PRE_FORMAL" not in joined


def _preflight_ok(*, outdir=None, **_kwargs):
    """Preflight stub: only the run-dir collision rule is exercised here.

    The real preflight (missing artifact / frozen-SHA checks) is Agent A's
    own unit under ``tests/test_lsu_v333_runner_errors.py``; these tests
    exercise the execution/classification path with a synthetic child.
    """
    evidence = {"checks": {}, "missing": [], "sha_mismatches": [],
                "observed_sha": {}, "expected_sha": {}}
    outdir = Path(outdir) if outdir is not None else None
    if outdir is not None and outdir.exists() and any(outdir.iterdir()):
        evidence["missing"] = ["outdir_unique"]
        return {"status": mx.STATUS_FAILED, "ok": False,
                "binary_sha": "a" * 64, "config_sha": "b" * 64,
                "elf_sha": "c" * 64, "evidence": evidence}
    return {"status": mx.PREFLIGHT_OK, "ok": True,
            "binary_sha": "a" * 64, "config_sha": "b" * 64,
            "elf_sha": "c" * 64, "evidence": evidence}


def _runner_env(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    monkeypatch.setattr(mx, "OUT_BASE", runs)
    monkeypatch.setattr(mx, "FORCE", False)
    monkeypatch.setattr(mx, "_sha256", lambda _path: "f" * 64)
    monkeypatch.setattr(mx, "preflight_task", _preflight_ok)
    return runs


def _install_fake_runner(monkeypatch, calls, handler):
    """Replace the single public execution seam (``mx.run_subprocess``)."""
    def fake(cmd, *, outdir, timeout, cwd=None,
             stdout_name="stdout.log", stderr_name="stderr.log", **_kwargs):
        cmd = [str(c) for c in cmd]
        calls.append(cmd)
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        result = handler(cmd, outdir) or {}
        (outdir / stdout_name).write_text(result.get("stdout", ""))
        (outdir / stderr_name).write_text(result.get("stderr", ""))
        return {
            "cmd": cmd, "pid": 4321,
            "exit_code": result.get("exit_code", 0),
            "timed_out": result.get("timed_out", False),
            "elapsed": 0.01, "started_at": "", "ended_at": "",
            "status": result.get("status"),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
        }
    monkeypatch.setattr(mx, "run_subprocess", fake)


def _stub_outputs(outdir, model, role):
    """The artifacts a successful task leaves (validation only stats them)."""
    (outdir / "prop_trace.csv.gz").write_bytes(b"")
    (outdir / "oracle.log").write_text("")
    if mx.driver_for(model, role) == "run_pilot":
        (outdir / "trace_v31.jsonl").write_text("")
    if role == "fault":
        (outdir / mx.MODEL_LOG_NAME[model]).write_text("")


def _meta_for(cmd):
    control = ("--probability" in cmd
               and cmd[cmd.index("--probability") + 1] == "0.0")
    return {
        "seed": 2108120075,
        "injection_count": 0 if control else 1,
        "oracle_pass": control,
        "terminal": "UNRESOLVED" if control else "SDC",
        "classification": {
            "terminal_state": "UNRESOLVED" if control else "SDC",
            "terminal_state_reason":
                "NO_INJECTION_EVENT" if control else "ORACLE_FAIL",
        },
        "injection": {"events": 0 if control else 1},
    }


def _role_of(cmd):
    if "--probability" in cmd and cmd[cmd.index("--probability") + 1] == "0.0":
        return "control"
    return "fault"


def test_runner_control_status_mapping_is_defined():
    """A completed control maps to COMPLETED (never an exception).

    This is the minimal public-helper check; it localizes the control-path
    crash independently of the subprocess seam.
    """
    status = mx.measured_status(
        model="A01", role="control", terminal="UNRESOLVED", oracle_pass=True,
        exit_code=0, timed_out=False, validation_status=mx.PREFLIGHT_OK)
    assert status == mx.STATUS_COMPLETED, status


def test_runner_complete_pair_and_no_duplicate_launch(tmp_path, monkeypatch):
    runs = _runner_env(tmp_path, monkeypatch)
    calls = []

    def handler(cmd, outdir):
        _stub_outputs(outdir, "A01", _role_of(cmd))
        (outdir / "pilot_meta.json").write_text(json.dumps(_meta_for(cmd)))
        return {"exit_code": 0}

    _install_fake_runner(monkeypatch, calls, handler)

    fault = mx.run_context("A01", 1, "fault")

    assert len(calls) == 1, f"each task must launch exactly one child: {calls}"
    f_sum = json.loads((Path(fault["outdir"]) / "summary.json").read_text())
    assert f_sum["terminal"] == "SDC" and f_sum["injection_count"] == 1
    assert fault["status"] == mx.STATUS_ORACLE_FAIL

    campaign = json.loads((Path(fault["outdir"]) / "campaign.json").read_text())
    assert campaign["campaign_id"] == mx.CAMPAIGN_ID_DEFAULT
    assert campaign["status"] == mx.STATUS_ORACLE_FAIL

    # Re-running the same task is refused at preflight: no second launch.
    again = mx.run_context("A01", 1, "fault")
    assert len(calls) == 1, f"duplicate task launch: {calls}"
    assert again["status"] == mx.STATUS_FAILED
    assert "outdir_unique" in (again.get("error") or "")

    control = mx.run_context("A01", 1, "control")
    assert len(calls) == 2, f"each task must launch exactly one child: {calls}"
    assert fault["outdir"] != control["outdir"]
    assert Path(fault["outdir"]).parent == runs
    assert Path(control["outdir"]).parent == runs
    c_sum = json.loads((Path(control["outdir"]) / "summary.json").read_text())
    assert c_sum["terminal"] == "UNRESOLVED"
    assert c_sum["injection_count"] == 0
    assert control["status"] == mx.STATUS_COMPLETED


def test_runner_external_timeout_is_timed_out_not_pass(tmp_path, monkeypatch):
    _runner_env(tmp_path, monkeypatch)
    calls = []

    def handler(cmd, outdir):
        model = "A03" if "--addrpath_event_ordinal" in cmd else "RP01"
        _stub_outputs(outdir, model, "fault")
        return {"exit_code": 124, "timed_out": True,
                "status": mx.STATUS_TIMEOUT,
                "stderr": "TIMEOUT: external wall-clock limit reached; "
                          "process group killed\n"}

    _install_fake_runner(monkeypatch, calls, handler)

    a03 = mx.run_context("A03", 1, "fault")
    rp01 = mx.run_context("RP01", 1, "fault")

    assert a03["timed_out"] is True and a03["exit_code"] == 124
    assert a03["terminal"] == "HANG"
    assert a03["terminal_reason"] == "NO_CHECKSUM_EXTERNAL_TIMEOUT"
    assert a03["status"] == mx.STATUS_TIMEOUT
    assert a03["terminal_source"] == mx.TERMINAL_SOURCE_PYTHON_TIMEOUT
    assert rp01["timed_out"] is True and rp01["exit_code"] == 124
    assert rp01["terminal"] == "UNRESOLVED"
    assert rp01["terminal_reason"] == "NO_CHECKSUM_NO_WATCHDOG"
    assert rp01["status"] == mx.STATUS_TIMEOUT
    for summary in (a03, rp01):
        assert summary["terminal"] not in {"SDC", "MASKED"}


def test_runner_internal_watchdogs_are_not_external_timeouts(tmp_path,
                                                             monkeypatch):
    _runner_env(tmp_path, monkeypatch)
    calls = []

    def handler(cmd, outdir):
        if "--rp01_event_ordinal" in cmd:
            _stub_outputs(outdir, "RP01", "fault")
            (outdir / "lsq_fwd_injections.log").write_text(
                "CHAOS_RP01_WATCHDOG=EXPIRED tick=5 "
                "deadline_cycles=20000000\n")
            return {"exit_code": 0,
                    "stdout": "RP01_ELIGIBLE ordinal=26\n"
                              "RP01_SKIP_REPLAY 26\n"}
        _stub_outputs(outdir, "A03", "fault")
        (outdir / "addrpath_injections.log").write_text(
            "FUNNEL: candidates=7 injected=0\n"
            "A03_WATCHDOG_EXPIRED tick=7 cycles=1000000\n")
        return {"exit_code": 0}

    _install_fake_runner(monkeypatch, calls, handler)

    rp01 = mx.run_context("RP01", 1, "fault")
    a03 = mx.run_context("A03", 1, "fault")

    assert rp01["terminal"] == "HANG_WATCHDOG"
    assert rp01["terminal_reason"] == "INTERNAL_WATCHDOG_DEADLINE"
    assert rp01["watchdog"] is True and rp01["timed_out"] is False
    assert rp01["status"] == mx.STATUS_COMPLETED
    assert rp01["terminal_source"] == mx.TERMINAL_SOURCE_MODEL_WATCHDOG
    assert a03["terminal"] == "HANG_WATCHDOG"
    assert a03["terminal_reason"] == "WATCHDOG_EXPIRED_NO_CHECKSUM"
    assert a03["watchdog_expired"] is True and a03["timed_out"] is False
    assert a03["status"] == mx.STATUS_COMPLETED
    assert a03["terminal_source"] == mx.TERMINAL_SOURCE_MODEL_WATCHDOG


def test_runner_child_exception_recorded_and_partial_campaign_continues(
        tmp_path, monkeypatch):
    runs = _runner_env(tmp_path, monkeypatch)
    monkeypatch.setattr(mx, "matrix_lock",
                        lambda *a, **k: contextlib.nullcontext())
    calls = []

    def handler(cmd, outdir):
        if outdir.name == "A01-R02-fault":
            raise OSError("synthetic child executable missing")
        _stub_outputs(outdir, "A01", "fault")
        (outdir / "pilot_meta.json").write_text(json.dumps(_meta_for(cmd)))
        return {"exit_code": 0}

    _install_fake_runner(monkeypatch, calls, handler)
    raw = tmp_path / "raw.csv"
    rc = mx.main(["--models", "A01", "--contexts", "1,2",
                  "--roles", "fault", "--out-base", str(runs),
                  "--out-csv", str(raw)])

    assert rc == 1, "a partial campaign with a failed task must exit nonzero"
    with open(raw, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    good = [r for r in rows if r["context"] == "R01"][0]
    bad = [r for r in rows if r["context"] == "R02"][0]
    assert good["status"] == mx.STATUS_ORACLE_FAIL
    assert bad["status"] == mx.STATUS_FAILED
    assert (runs / "A01-R01-fault" / "summary.json").exists()
    # The failed task still records its own evidence; it is never dropped.
    assert (runs / "A01-R02-fault" / "summary.json").exists()
    assert (runs / "A01-R02-fault" / "campaign.json").exists()
    bad_campaign = json.loads(
        (runs / "A01-R02-fault" / "campaign.json").read_text())
    assert bad_campaign["status"] == mx.STATUS_FAILED
    assert "OSError" in (bad_campaign.get("parse_error") or "")
    bad_summary = json.loads(
        (runs / "A01-R02-fault" / "summary.json").read_text())
    assert bad_summary["status"] == mx.STATUS_FAILED
    assert bad.get("terminal") not in {"SDC", "MASKED"}


# ===========================================================================
# 2. control proof (Agent C) — PENDING until the module lands
# ===========================================================================
def test_control_complete_zero_applied_passes():
    mod = _control_mod()
    result = mod.classify_control_run(FIX / "campaign/A01-R01-control")
    assert result["status"] == "PASS", result
    assert result["proof_class"] == "MOUNTED_BUT_DISABLED", result
    assert result["injection_applied_count"] == 0
    assert result["suppression_reason"]


def test_control_applied_greater_than_zero_fails():
    mod = _control_mod()
    result = mod.classify_control_run(FIX / "campaign/A01-R04-control")
    assert result["status"] == "FAIL", result
    assert result["injection_applied_count"] == 1


def test_control_missing_count_is_incomplete_never_zero():
    mod = _control_mod()
    result = mod.classify_control_run(FIX / "campaign/A01-R05-control")
    assert result["status"] == "CONTROL_PROOF_INCOMPLETE", result
    applied = result.get("injection_applied_count")
    assert applied not in (0, "0"), (
        "a missing count must never be reported as zero: %r" % (result,))
    assert applied in (None, "UNKNOWN"), result


def test_control_missing_summary_is_incomplete(tmp_path):
    mod = _control_mod()
    run = _clone_run(tmp_path, "campaign/A01-R02-control", "A01-R02-control")
    (run / "summary.json").unlink()
    result = mod.classify_control_run(run)
    assert result["status"] == "CONTROL_PROOF_INCOMPLETE", result
    applied = result.get("injection_applied_count")
    if applied in (0, "0"):
        # A zero is acceptable only when a per-run source corroborates it;
        # a silent default to 0 is not.
        evidence = " ".join(result.get("evidence") or [])
        assert "counts.injections=0" in evidence, (
            "missing summary was silently repaired to 0: %r" % (result,))
    else:
        assert applied in (None, "UNKNOWN"), result


def test_control_missing_trace_is_incomplete():
    mod = _control_mod()
    result = mod.classify_control_run(FIX / "campaign/A01-R03-control")
    assert result["status"] == "CONTROL_PROOF_INCOMPLETE", result
    assert result["status"] != "PASS"


def test_control_injector_absent_is_a_pass(tmp_path):
    mod = _control_mod()
    run = tmp_path / "A01-R01-control"
    run.mkdir()
    (run / "summary.json").write_text(json.dumps({
        "model": "A01", "role": "control", "injection_count": 0,
        "injection_attempt_count": 0, "injection_applied_count": 0,
        "control_proof": "INJECTOR_ABSENT"}))
    (run / "command.txt").write_text(
        "gem5.opt --outdir=x lsu_proxy.py --cmd=agu --cpu O3 "
        "--probability 0.0\n")
    result = mod.classify_control_run(run)
    assert result["status"] == "PASS", result
    assert result["proof_class"] == "INJECTOR_ABSENT", result


# ===========================================================================
# 3. qualified evidence (Agent D) — PENDING until the module lands
# ===========================================================================
def test_qualified_a01_complete_has_no_extra_rules():
    mod = _qualified_mod()
    result = mod.qualified_evidence("A01", FIX / "campaign/A01-R01-fault")
    assert result["status"] == "PASS", result
    assert result["required_fields"] == []
    assert result["missing"] == []


def _clone_run(tmp_path, rel, name):
    src = FIX / rel
    run = tmp_path / name
    run.mkdir()
    for path in src.iterdir():
        (run / path.name).write_bytes(path.read_bytes())
    return run


def test_qualified_missing_trace_is_not_pass(tmp_path):
    mod = _qualified_mod()
    # A03 is a qualified model: its evidence source here is prop_trace.
    run = _clone_run(tmp_path, "campaign/A03-R01-fault", "A03-R01-fault")
    (run / "prop_trace.csv.gz").unlink()
    result = mod.qualified_evidence("A03", run)
    assert result["status"] == "TRACE_INCOMPLETE", result
    assert result["status"] != "PASS"


def test_qualified_watchdog_terminal_is_never_a_timeout():
    mod = _qualified_mod()
    rp01 = mod.qualified_evidence("RP01", FIX / "campaign/RP01-R01-fault")
    # RP01's trace is cut by its own watchdog: a partial trace, never PASS.
    assert rp01["status"] in {"QUALIFIED", "TRACE_INCOMPLETE"}, rp01
    assert rp01["terminal_rule"] == "MODEL_INTERNAL_WATCHDOG", rp01
    a03 = mod.qualified_evidence("A03", FIX / "campaign/A03-R04-fault")
    assert a03["terminal_rule"], a03
    assert "EXTERNAL_TIMEOUT" not in json.dumps(a03).upper(), a03


def test_qualified_truncated_trace_is_never_upgraded(tmp_path):
    mod = _qualified_mod()
    run = _clone_run(tmp_path, "campaign/A03-R01-fault", "A03-R01-fault")
    (run / "prop_trace.csv.gz").unlink()
    summary = json.loads((run / "summary.json").read_text())
    summary["trace_completeness"]["trace_completeness"] = "TRUNCATED"
    (run / "summary.json").write_text(json.dumps(summary))
    result = mod.qualified_evidence("A03", run)
    assert result["status"] == "TRACE_INCOMPLETE", result


def test_qualified_never_reports_pass_with_missing_fields():
    mod = _qualified_mod()
    for model, run in (("A03", "campaign/A03-R01-fault"),
                       ("SP05", "campaign/SP05-R01-fault"),
                       ("RP01", "campaign/RP01-R01-fault")):
        result = mod.qualified_evidence(model, FIX / run)
        assert result["status"] in {"PASS", "QUALIFIED",
                                    "TRACE_INCOMPLETE"}, (model, result)
        if result["status"] == "PASS":
            assert not result["missing"], (
                f"{model}: PASS with missing fields must never happen: "
                f"{result}")


# ===========================================================================
# 4. collector (Agent B) — PENDING until the new CLI lands
# ===========================================================================
def test_collector_complete_fault_and_control_are_formal(campaign_out):
    out, _rc = campaign_out
    recs = _records(out)
    for dirname in ("A01-R01-fault", "A01-R01-control"):
        rec = _first(recs, dirname)
        assert _evidence_kind(rec) == "FORMAL", (dirname, rec)
        assert _status(rec) in PASS_LIKE, (dirname, rec)


def test_collector_clean_campaign_exits_zero(clean_out):
    out, rc = clean_out
    assert rc == 0, f"all-good campaign must exit 0, got {rc}"
    recs = _records(out)
    for dirname in ("A01-R01-fault", "A01-R01-control",
                    "SP05-R01-fault", "SP05-R01-control"):
        rec = _first(recs, dirname)
        assert _evidence_kind(rec) == "FORMAL", (dirname, rec)
        assert _status(rec) in PASS_LIKE, (dirname, rec)


@pytest.mark.parametrize("dirname,needle", [
    ("A01-R02-fault", None),          # missing summary.json
    ("A01-R03-fault", "INCOMPLETE"),  # missing fault trace
    ("A01-R03-control", "INCOMPLETE"),# missing control trace
])
def test_collector_missing_evidence_is_never_pass(campaign_out, dirname,
                                                  needle):
    out, _rc = campaign_out
    rec = _first(_records(out), dirname)
    _assert_not_pass(rec, dirname)
    if needle:
        assert needle in _all_text(rec), rec


def test_collector_control_proof_defects_are_not_pass(campaign_out):
    out, _rc = campaign_out
    recs = _records(out)
    for dirname in ("A01-R04-control", "A01-R05-control"):
        rec = _first(recs, dirname)
        _assert_not_pass(rec, dirname)
        assert "CONTROL_PROOF" in _all_text(rec) or \
            _status(rec) in {"FAIL", "CONTROL_PROOF_INCOMPLETE"}, rec


def test_collector_sha_mismatches_are_flagged(campaign_out):
    out, _rc = campaign_out
    recs = _records(out)
    for dirname in ("A03-R01-fault", "A03-R02-fault"):
        rec = _first(recs, dirname)
        _assert_not_pass(rec, dirname)
        assert "HASH_MISMATCH" in _all_text(rec), (
            f"{dirname}: SHA mismatch must be flagged, got {rec}")


def test_collector_external_timeout_is_flagged(campaign_out):
    out, rc = campaign_out
    assert rc != 0, "execution/integrity failures must make the campaign exit nonzero"
    rec = _first(_records(out), "A03-R03-fault")
    _assert_not_pass(rec, "A03-R03-fault")
    assert "TIMEOUT" in _all_text(rec), rec


def test_collector_internal_watchdog_is_not_external_timeout(campaign_out):
    out, _rc = campaign_out
    recs = _records(out)
    for dirname in ("RP01-R01-fault", "A03-R04-fault"):
        rec = _first(recs, dirname)
        text = _all_text(rec)
        assert "HANG_WATCHDOG" in text or "WATCHDOG" in text, (dirname, rec)
        status = _status(rec)
        assert status != "TIMEOUT", (dirname, rec)


def test_collector_child_exception_is_failed(campaign_out):
    out, _rc = campaign_out
    rec = _first(_records(out), "FW02-R01-fault")
    _assert_not_pass(rec, "FW02-R01-fault")
    assert any(token in _all_text(rec) or _status(rec) == token
               for token in ("FAILED", "EXCEPTION", "CRASH", "INCOMPLETE")), rec


def test_collector_partial_campaign_reports_good_tasks_and_nonzero(partial_out):
    out, rc = partial_out
    assert rc != 0, "partial campaign has execution failures -> nonzero exit"
    recs = _records(out)
    good = _first(recs, "A01-R01-fault")
    assert _status(good) in PASS_LIKE, good
    for dirname in ("A01-R02-fault", "A01-R02-control"):
        _assert_not_pass(_first(recs, dirname), dirname)


def test_collector_historical_evidence_is_never_formal(campaign_out,
                                                       historical_out):
    out, _rc = campaign_out
    for rec in _records(out):
        blob = _evidence(rec)
        assert "historical_evidence" not in blob, (
            "formal collector read historical evidence: %r" % (rec,))
    hout, _hrc = historical_out
    for rec in _records(hout):
        assert _evidence_kind(rec) != "FORMAL", (
            "historical (non-matching campaign_id) run admitted as FORMAL: %r"
            % (rec,))
        assert not (_status(rec) in PASS_LIKE
                    and _evidence_kind(rec) == "FORMAL"), rec
