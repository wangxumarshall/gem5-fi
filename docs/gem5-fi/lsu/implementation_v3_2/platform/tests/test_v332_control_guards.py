"""v3.3.2 P0 control-hazard guard tests.

Two matched no-fault controls were not truly zero-injection in v3.3.1:

* **DA04** always mounted ``--chaos_lsqfwd --lsq_struct_mode da04_be_bit0``.
  The DA04 byte-enable corruption is *ordinal*-gated (F0 on
  ``lsq_pushRequest_byte_enable``), never probability-gated, so
  ``--probability 0.0`` still let the injector fire.
* **MD04** hard-coded ``--md04_probability 1.0``; CHAOSMD04 gates on its own
  ``md04_probability`` and never consults the global ``--probability``, so a
  control that mounts the injector fires.

The fix mirrors the LQ04/FW02 precedent: a control at probability 0.0 omits
the injector mount entirely (the propagation tracer stays on).  FAULT runs
must remain byte-identical.  ``run_pilot.build_model_extra`` is the extracted
pure helper that owns this decision; these tests pin it directly, plus the
RP01 replay-pilot command builder, plus the new ``--dry-run`` path.

The dry-run test passes a nonexistent ``--gem5`` path: if the simulator were
invoked at all the call would fail, so a clean exit 0 proves the command was
only printed/written and gem5 was skipped.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

import run_pilot  # noqa: E402
import run_replay_pilot  # noqa: E402


def _has(cmd, flag):
    return flag in cmd


def _value(cmd, flag):
    return cmd[cmd.index(flag) + 1]


# ---------------------------------------------------------------------------
# DA04: ordinal-gated byte-enable corruption
# ---------------------------------------------------------------------------

def test_da04_control_omits_injector():
    cmd = run_pilot.build_model_extra("DA04", 0.0, seed=11, ordinal=3)
    for absent in ("--chaos_lsqfwd", "--lsq_struct_mode", "da04_be_bit0",
                   "--max_faults", "--rng_seed", "--lsqfwd_event_ordinal",
                   "--lsqfwd_lsu_tier"):
        assert absent not in cmd, f"{absent!r} must not be mounted for a DA04 control"


def test_da04_fault_run_is_unchanged():
    cmd = run_pilot.build_model_extra("DA04", 1.0, seed=11, ordinal=3)
    assert _has(cmd, "--chaos_lsqfwd")
    assert _value(cmd, "--lsq_struct_mode") == "da04_be_bit0"
    assert _value(cmd, "--lsqfwd_lsu_tier") == "F0"
    assert _value(cmd, "--max_faults") == "1"
    assert _value(cmd, "--rng_seed") == "11"
    assert _value(cmd, "--lsqfwd_event_ordinal") == "3"


# ---------------------------------------------------------------------------
# MD04: CHAOSMD04 gates on md04_probability, not --probability
# ---------------------------------------------------------------------------

def test_md04_control_omits_injector_and_its_probability():
    cmd = run_pilot.build_model_extra("MD04", 0.0, seed=11, ordinal=3)
    for absent in ("--chaos_md04", "--md04_probability", "--md04_first_clock",
                   "--md04_max_faults", "--md04_rng_seed",
                   "--md04_event_ordinal"):
        assert absent not in cmd, f"{absent!r} must not be mounted for an MD04 control"


def test_md04_fault_run_keeps_md04_probability_1():
    cmd = run_pilot.build_model_extra("MD04", 1.0, seed=11, ordinal=3)
    assert _has(cmd, "--chaos_md04")
    assert _value(cmd, "--md04_probability") == "1.0"
    assert _value(cmd, "--md04_max_faults") == "1"
    assert _value(cmd, "--md04_rng_seed") == "11"
    assert _value(cmd, "--md04_event_ordinal") == "3"


# ---------------------------------------------------------------------------
# LQ04 / FW02: pre-existing omit behaviour must be preserved exactly
# ---------------------------------------------------------------------------

def test_lq04_control_still_omits_and_fault_still_mounts():
    control = run_pilot.build_model_extra("LQ04", 0.0, seed=11, ordinal=3)
    assert control == []
    fault = run_pilot.build_model_extra("LQ04", 1.0, seed=11, ordinal=3)
    assert _has(fault, "--chaos_lq04")
    assert _value(fault, "--lq04_max_faults") == "1"


def test_fw02_control_still_omits_and_fault_still_mounts():
    control = run_pilot.build_model_extra("FW02", 0.0, seed=11, ordinal=3)
    assert control == []
    fault = run_pilot.build_model_extra("FW02", 1.0, seed=11, ordinal=3)
    assert _has(fault, "--chaos_lsqfwd")
    assert _value(fault, "--lsq_struct_mode") == "f6_fw02"


# ---------------------------------------------------------------------------
# Other models: controls are deliberately untouched (probability-gated attach)
# ---------------------------------------------------------------------------

def test_probability_gated_models_keep_their_control_mount():
    for model, flag in (("SQ01", "--chaos_lsqfwd"),
                        ("SQ03", "--chaos_lsqfwd"),
                        ("SP05", "--chaos_lsqfwd"),
                        ("FW05", "--chaos_lsqfwd"),
                        ("LP01", "--chaos_l1dfwd"),
                        ("A01", "--chaos_addrpath"),
                        ("A03", "--chaos_addrpath")):
        cmd = run_pilot.build_model_extra(model, 0.0, seed=11, ordinal=3)
        assert flag in cmd, f"{model} control attach is probability-gated; flag must stay"


# ---------------------------------------------------------------------------
# RP01 replay pilot: FP01 control omits --chaos_lsqfwd
# ---------------------------------------------------------------------------

def test_rp01_replay_control_omits_lsqfwd():
    cmd = run_replay_pilot.build_replay_command(
        Path("/nonexistent/gem5.opt"), Path("/tmp/rp01-out"), probability=0.0)
    for absent in ("--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                   "--max_faults", "--rng_seed", "--lsqfwd_event_ordinal"):
        assert absent not in cmd
    assert _value(cmd, "--probability") == "0.0"
    assert "--chaos_propagation" in cmd
    assert "--prop_replay_all" in cmd


def test_rp01_replay_fault_run_keeps_fw02_carrier():
    cmd = run_replay_pilot.build_replay_command(
        Path("/nonexistent/gem5.opt"), Path("/tmp/rp01-out"), probability=1.0)
    assert _value(cmd, "--probability") == "1.0"
    assert "--chaos_lsqfwd" in cmd
    assert _value(cmd, "--lsq_struct_mode") == "f6_fw02"


# ---------------------------------------------------------------------------
# --dry-run: print + write command.txt, never invoke gem5
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model,probability,absent,expected", [
    ("DA04", 0.0, ("--chaos_lsqfwd", "--lsq_struct_mode"), ()),
    ("MD04", 0.0, ("--chaos_md04", "--md04_probability"), ()),
    ("MD04", 1.0, (), ("--chaos_md04", "--md04_probability")),
])
def test_dry_run_prints_command_and_never_runs_gem5(
        tmp_path, capsys, model, probability, absent, expected):
    outdir = tmp_path / f"dry-{model}-{probability}"
    rc = run_pilot.main([
        "--model", model,
        "--probability", str(probability),
        "--pilot-id", f"V332-DRY-{model}",
        "--context-index", "1",
        "--outdir", str(outdir),
        "--gem5", str(tmp_path / "does-not-exist-gem5.opt"),
        "--dry-run",
    ])
    assert rc == 0
    printed = capsys.readouterr().out
    command_txt = (outdir / "command.txt").read_text().splitlines()
    # The printed line is the exact command that was written to command.txt.
    assert command_txt
    assert str(tmp_path / "does-not-exist-gem5.opt") == command_txt[0]
    assert printed.strip() == " ".join(command_txt)
    for flag in absent:
        assert flag not in command_txt
    for flag in expected:
        assert flag in command_txt
    # gem5 was skipped: no run artifacts / manifest / meta exist.
    assert not (outdir / "pilot_meta.json").exists()
    assert not (outdir / "manifest.json").exists()
    assert not (outdir / "stdout.log").exists()


# ---------------------------------------------------------------------------
# LP01 v3.3.2 record parser: the new pa/va/pc/dyn_inst_seq identity fields are
# inserted between the old positional fields. The parser must still count the
# injection (a single positional regex silently returned 0 and would have
# rejected every LP01 fault as injection-free).
# ---------------------------------------------------------------------------

def test_l1dfwd_parser_accepts_v332_identity_fields(tmp_path):
    log = tmp_path / "l1d_fwd_injections.log"
    log.write_text(
        "Tick: 172865, Site: l1d_load_complete, addr=0x80d90, "
        "pa=0x80d90, va=0x7ffffefd90, pc=0x4005d0, size=8, mask=0x8, "
        "dyn_inst_seq=5, lq_entry_id=1, entry_generation=1, request_id=0, "
        "eligible_ordinal=1, byte0_changed=1, addr_unchanged=1, "
        "size_unchanged=1, faults_injected: 1\n"
        "Tick: 173000, Site: l1d_load_complete, addr=0x4919c8, size=8, "
        "mask=0x8, eligible_ordinal=2, byte0_changed=1, "
        "addr_unchanged=1, size_unchanged=1, faults_injected: 2\n")
    events = run_pilot._l1dfwd_events(log)
    assert len(events) == 2
    first = events[0]
    assert first["pc"] == 0x4005D0
    assert first["va"] == 0x7FFFFEFD90
    assert first["pa"] == first["addr"] == 0x80D90
    assert first["dyn_inst_seq"] == 5
    assert first["lq_entry_id"] == 1
    assert first["entry_generation"] == 1
    assert first["eligible_ordinal"] == 1
    # Legacy line shape (no identity fields) still parses.
    assert events[1]["addr"] == 0x4919C8
    assert events[1]["eligible_ordinal"] == 2
