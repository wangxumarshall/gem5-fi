"""FW02 control-mount regression tests (LSU v3.2.12 FW02 control fix).

The F6_fw02 injector is ordinal-gated and deliberately probability-independent:
CHAOSLSQFwd attaches the F6Fw02 mode even with ``probability == 0`` and its
suppression decision (``maybeSuppressForwarding``) never consults probability.
A matched no-fault control (``--probability 0.0``) for FW02 must therefore
omit the injector mount entirely -- exactly the LQ04 control-branch treatment
-- because a mounted injector would still fire.  That is the SUPP-FW02-C01
misfire this fix closes (see ``audit_v3_2_12/FW02_CONTROL_FIX_v3.2.12.md``).

The tests drive the real ``run_pilot.main`` end to end against a stub gem5
that records its argv and exits 0, so the assertions cover the command the
platform actually hands to the simulator (persisted in ``command.txt`` and
received by the simulator process), not a reconstruction of it.  The stub
produces no simulator artifacts, so the runs are honestly rejected
(``accepted: false``); only the mount flags and the zero-injection bookkeeping
are under test here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

import run_pilot  # noqa: E402

# The frozen FW02 context R01 identity (RUNBOOK_v3.2.12.md §1 / §4), the same
# context/seed the SUPP-FW02-C01 control was run with.
FW02_SEED = 2941542370
FW02_ORDINAL = 1


def _stub_gem5(tmp_path: Path) -> tuple[Path, Path]:
    """A fake gem5.opt: records its argv and exits 0 without simulating."""
    argv_path = tmp_path / "stub_gem5_argv.txt"
    stub = tmp_path / "gem5.opt"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"Path({str(argv_path)!r}).write_text("
        "'\\n'.join(sys.argv[1:]) + '\\n')\n",
        encoding="utf-8")
    stub.chmod(0o755)
    return stub, argv_path


def _run_pilot(model: str, outdir: Path, stub: Path, *, probability=None,
               seed=1, event_ordinal=1, context_index=1,
               workload=None) -> int:
    argv = ["--model", model,
            "--context-index", str(context_index),
            "--pilot-id", f"PILOT-{model}-MOUNTTEST",
            "--seed", str(seed),
            "--event-ordinal", str(event_ordinal),
            "--outdir", str(outdir),
            "--gem5", str(stub)]
    if workload is not None:
        argv += ["--workload", str(workload)]
    if probability is not None:
        argv += ["--probability", str(probability)]
    return run_pilot.main(argv)


def _command(outdir: Path) -> list[str]:
    return (outdir / "command.txt").read_text().splitlines()


def _value(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def test_fw02_control_omits_the_injector_mount(tmp_path):
    stub, argv_path = _stub_gem5(tmp_path)
    outdir = tmp_path / "fw02-control"
    _run_pilot("FW02", outdir, stub, probability=0.0,
               seed=FW02_SEED, event_ordinal=FW02_ORDINAL)

    cmd = _command(outdir)
    # The probability-independent F6_fw02 injector is NOT mounted: none of
    # the injector flags reach gem5, so no suppression can fire by
    # construction (the SUPP-FW02-C01 misfire mode is unreachable).
    for absent in ("--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                   "--lsqfwd_event_ordinal", "--max_faults", "--rng_seed"):
        assert absent not in cmd, f"{absent!r} must not be mounted for a control"
    # The matched-control context is preserved: intent, workload, trace
    # machinery and run context are unchanged.
    assert _value(cmd, "--probability") == "0.0"
    assert "--chaos_propagation" in cmd
    assert _value(cmd, "--prop_trace_file") == "prop_trace.csv.gz"
    assert cmd[2].endswith("lsu_proxy.py")
    assert cmd[3].endswith("sq_forward")
    assert _value(cmd, "--cpu") == "O3"
    assert _value(cmd, "--variant") == "B0"
    # What gem5 actually received == what command.txt recorded (cmd[0] is the
    # binary path, which the stub drops from its own argv).
    assert argv_path.read_text().splitlines() == cmd[1:]
    # Runner-level bookkeeping for a control with no injector mounted: no
    # lsq_fwd_injections.log exists, so the FW02 post-processing arm records
    # zero injections and no misfire.
    meta = json.loads((outdir / "pilot_meta.json").read_text())
    assert meta["run_role"] == "CONTROL"
    assert meta["injection_count"] == 0
    assert meta["injection"] == {}
    assert meta["control_misfire"] is False


def test_fw02_fault_run_keeps_the_injector_mount(tmp_path):
    stub, _ = _stub_gem5(tmp_path)
    outdir = tmp_path / "fw02-fault"
    _run_pilot("FW02", outdir, stub, seed=FW02_SEED,
               event_ordinal=FW02_ORDINAL)

    cmd = _command(outdir)
    # A FAULT run still mounts the F6_fw02 injector with the frozen context
    # identity -- the fix must only affect the control path.
    assert "--chaos_lsqfwd" in cmd
    assert _value(cmd, "--lsq_struct_mode") == "f6_fw02"
    assert _value(cmd, "--max_faults") == "1"
    assert _value(cmd, "--rng_seed") == str(FW02_SEED)
    assert _value(cmd, "--lsqfwd_event_ordinal") == str(FW02_ORDINAL)
    meta = json.loads((outdir / "pilot_meta.json").read_text())
    assert meta["run_role"] == "FAULT"


def test_lq04_control_precedent_unchanged(tmp_path):
    stub, _ = _stub_gem5(tmp_path)
    outdir = tmp_path / "lq04-control"
    # LQ04's is a pilot-only directed workload, so its runs pass --workload
    # (the Excel InputHash describes the frozen W8 workload and cannot match
    # the override) -- the same invocation shape as the recorded LQ04 pilots.
    _run_pilot("LQ04", outdir, stub, probability=0.0,
               workload=PLATFORM.parent / "workloads" / "lq_lifetime_ordinal")

    cmd = _command(outdir)
    assert "--chaos_lq04" not in cmd
    assert "--chaos_propagation" in cmd


def test_sq01_control_still_mounts_probability_gated_injector(tmp_path):
    stub, _ = _stub_gem5(tmp_path)
    outdir = tmp_path / "sq01-control"
    _run_pilot("SQ01", outdir, stub, probability=0.0)

    cmd = _command(outdir)
    # SQ01's attach is probability-gated in the injector (probability > 0 is
    # required to attach), so its control keeps mounting the injector and
    # relies on the attach gate: the fix must not change other models.
    assert "--chaos_lsqfwd" in cmd
    assert _value(cmd, "--lsq_struct_mode") == "sq01_bit3"
